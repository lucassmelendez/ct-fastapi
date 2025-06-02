from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from webpay_service import WebpayService

# Crear la aplicación FastAPI
app = FastAPI(
    title="CowTracker API",
    description="API para el sistema de seguimiento de ganado con integración Webpay Plus",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar servicio de Webpay
webpay_service = WebpayService(environment="integration")

# Modelos Pydantic
class Cow(BaseModel):
    id: Optional[int] = None
    name: str
    breed: str
    age: int
    weight: float
    health_status: str = "healthy"

class CowUpdate(BaseModel):
    name: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    health_status: Optional[str] = None

# Nuevos modelos para Webpay
class PaymentRequest(BaseModel):
    amount: int
    buy_order: Optional[str] = None
    session_id: Optional[str] = None
    return_url: Optional[str] = None
    description: Optional[str] = None

class CowPurchaseRequest(BaseModel):
    cow_id: int
    buyer_name: str
    buyer_email: str
    return_url: Optional[str] = None

# Base de datos simulada (en producción usarías una base de datos real)
cows_db = [
    {"id": 1, "name": "Bessie", "breed": "Holstein", "age": 3, "weight": 650.5, "health_status": "healthy", "price": 1500000},
    {"id": 2, "name": "Daisy", "breed": "Jersey", "age": 2, "weight": 450.0, "health_status": "healthy", "price": 1200000},
    {"id": 3, "name": "Moo", "breed": "Angus", "age": 4, "weight": 800.0, "health_status": "sick", "price": 800000}
]

# Base de datos de transacciones (en memoria)
transactions_db = []

# Rutas de la API
@app.get("/")
async def root():
    return {"message": "Bienvenido a CowTracker API con Webpay Plus", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "CowTracker API", "webpay": "enabled"}

@app.get("/cows", response_model=List[Cow])
async def get_cows():
    """Obtener todas las vacas"""
    return cows_db

@app.get("/cows/{cow_id}", response_model=Cow)
async def get_cow(cow_id: int):
    """Obtener una vaca específica por ID"""
    cow = next((cow for cow in cows_db if cow["id"] == cow_id), None)
    if not cow:
        raise HTTPException(status_code=404, detail="Vaca no encontrada")
    return cow

@app.post("/cows", response_model=Cow)
async def create_cow(cow: Cow):
    """Crear una nueva vaca"""
    # Generar nuevo ID
    new_id = max([c["id"] for c in cows_db], default=0) + 1
    cow_dict = cow.dict()
    cow_dict["id"] = new_id
    cow_dict["price"] = 1000000  # Precio por defecto
    cows_db.append(cow_dict)
    return cow_dict

@app.put("/cows/{cow_id}", response_model=Cow)
async def update_cow(cow_id: int, cow_update: CowUpdate):
    """Actualizar una vaca existente"""
    cow_index = next((i for i, cow in enumerate(cows_db) if cow["id"] == cow_id), None)
    if cow_index is None:
        raise HTTPException(status_code=404, detail="Vaca no encontrada")
    
    # Actualizar solo los campos proporcionados
    for field, value in cow_update.dict(exclude_unset=True).items():
        cows_db[cow_index][field] = value
    
    return cows_db[cow_index]

@app.delete("/cows/{cow_id}")
async def delete_cow(cow_id: int):
    """Eliminar una vaca"""
    cow_index = next((i for i, cow in enumerate(cows_db) if cow["id"] == cow_id), None)
    if cow_index is None:
        raise HTTPException(status_code=404, detail="Vaca no encontrada")
    
    deleted_cow = cows_db.pop(cow_index)
    return {"message": f"Vaca {deleted_cow['name']} eliminada exitosamente"}

@app.get("/cows/breed/{breed}")
async def get_cows_by_breed(breed: str):
    """Obtener vacas por raza"""
    filtered_cows = [cow for cow in cows_db if cow["breed"].lower() == breed.lower()]
    return filtered_cows

@app.get("/cows/health/{status}")
async def get_cows_by_health_status(status: str):
    """Obtener vacas por estado de salud"""
    filtered_cows = [cow for cow in cows_db if cow["health_status"].lower() == status.lower()]
    return filtered_cows

# Nuevos endpoints para Webpay Plus
@app.post("/webpay/create-transaction")
async def create_webpay_transaction(payment_request: PaymentRequest):
    """Crear una nueva transacción de pago con Webpay Plus"""
    try:
        result = webpay_service.create_transaction(
            amount=payment_request.amount,
            buy_order=payment_request.buy_order,
            session_id=payment_request.session_id,
            return_url=payment_request.return_url
        )
        
        if result["success"]:
            # Guardar la transacción en la base de datos
            transaction_data = {
                "token": result["token"],
                "buy_order": result["buy_order"],
                "session_id": result["session_id"],
                "amount": result["amount"],
                "status": "created",
                "description": payment_request.description,
                "created_at": result["created_at"]
            }
            transactions_db.append(transaction_data)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear transacción: {str(e)}")

@app.post("/cows/{cow_id}/purchase")
async def purchase_cow(cow_id: int, purchase_request: CowPurchaseRequest):
    """Iniciar el proceso de compra de una vaca"""
    # Verificar que la vaca existe
    cow = next((cow for cow in cows_db if cow["id"] == cow_id), None)
    if not cow:
        raise HTTPException(status_code=404, detail="Vaca no encontrada")
    
    # Crear transacción de pago
    payment_request = PaymentRequest(
        amount=cow["price"],
        buy_order=f"cow_{cow_id}_{purchase_request.buyer_name.replace(' ', '_')}",
        session_id=f"session_{cow_id}_{purchase_request.buyer_email.split('@')[0]}",
        return_url=purchase_request.return_url or "http://localhost:8000/webpay/return",
        description=f"Compra de vaca {cow['name']} - {cow['breed']}"
    )
    
    result = webpay_service.create_transaction(
        amount=payment_request.amount,
        buy_order=payment_request.buy_order,
        session_id=payment_request.session_id,
        return_url=payment_request.return_url
    )
    
    if result["success"]:
        # Guardar información adicional de la compra
        transaction_data = {
            "token": result["token"],
            "buy_order": result["buy_order"],
            "session_id": result["session_id"],
            "amount": result["amount"],
            "status": "created",
            "cow_id": cow_id,
            "cow_name": cow["name"],
            "buyer_name": purchase_request.buyer_name,
            "buyer_email": purchase_request.buyer_email,
            "description": payment_request.description,
            "created_at": result["created_at"]
        }
        transactions_db.append(transaction_data)
        
        return {
            "success": True,
            "message": f"Transacción creada para la compra de {cow['name']}",
            "cow": cow,
            "payment_url": result["url"],
            "token": result["token"],
            "amount": result["amount"]
        }
    
    return result

@app.post("/webpay/confirm")
async def confirm_webpay_transaction(request: Request):
    """Confirmar una transacción de Webpay Plus"""
    try:
        # Obtener el token del formulario POST
        form_data = await request.form()
        token_ws = form_data.get("token_ws")
        
        if not token_ws:
            raise HTTPException(status_code=400, detail="Token no proporcionado")
        
        # Confirmar la transacción
        result = webpay_service.confirm_transaction(token_ws)
        
        if result["success"]:
            # Actualizar el estado de la transacción en la base de datos
            for transaction in transactions_db:
                if transaction.get("token") == token_ws:
                    transaction["status"] = "confirmed" if result["response_code"] == 0 else "failed"
                    transaction["webpay_response"] = result
                    break
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al confirmar transacción: {str(e)}")

@app.get("/webpay/return")
async def webpay_return(request: Request):
    """Página de retorno después del pago"""
    try:
        # Obtener parámetros de la URL
        token_ws = request.query_params.get("token_ws")
        
        if not token_ws:
            return HTMLResponse("""
            <html>
                <body>
                    <h1>Error en el pago</h1>
                    <p>No se recibió el token de la transacción.</p>
                    <a href="/">Volver al inicio</a>
                </body>
            </html>
            """)
        
        # Confirmar automáticamente la transacción
        result = webpay_service.confirm_transaction(token_ws)
        
        # Buscar la transacción en la base de datos
        transaction = next((t for t in transactions_db if t.get("token") == token_ws), None)
        
        if result["success"] and result["response_code"] == 0:
            # Pago exitoso
            if transaction:
                transaction["status"] = "confirmed"
                transaction["webpay_response"] = result
            
            return HTMLResponse(f"""
            <html>
                <head>
                    <title>Pago Exitoso - CowTracker</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; }}
                        .success {{ color: green; }}
                        .info {{ background: #f0f0f0; padding: 20px; margin: 20px 0; }}
                    </style>
                </head>
                <body>
                    <h1 class="success">¡Pago Exitoso!</h1>
                    <div class="info">
                        <h3>Detalles de la transacción:</h3>
                        <p><strong>Orden de compra:</strong> {result.get('buy_order', 'N/A')}</p>
                        <p><strong>Monto:</strong> ${result.get('amount', 0):,} CLP</p>
                        <p><strong>Código de autorización:</strong> {result.get('authorization_code', 'N/A')}</p>
                        <p><strong>Fecha:</strong> {result.get('transaction_date', 'N/A')}</p>
                        {f"<p><strong>Vaca comprada:</strong> {transaction.get('cow_name', 'N/A')}</p>" if transaction and transaction.get('cow_name') else ""}
                        {f"<p><strong>Comprador:</strong> {transaction.get('buyer_name', 'N/A')}</p>" if transaction and transaction.get('buyer_name') else ""}
                    </div>
                    <a href="/">Volver al inicio</a>
                </body>
            </html>
            """)
        else:
            # Pago fallido
            if transaction:
                transaction["status"] = "failed"
                transaction["webpay_response"] = result
            
            return HTMLResponse(f"""
            <html>
                <head>
                    <title>Pago Fallido - CowTracker</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; }}
                        .error {{ color: red; }}
                        .info {{ background: #f0f0f0; padding: 20px; margin: 20px 0; }}
                    </style>
                </head>
                <body>
                    <h1 class="error">Pago Fallido</h1>
                    <div class="info">
                        <p>Lo sentimos, no se pudo procesar tu pago.</p>
                        <p><strong>Código de respuesta:</strong> {result.get('response_code', 'N/A')}</p>
                        <p><strong>Orden de compra:</strong> {result.get('buy_order', 'N/A')}</p>
                    </div>
                    <a href="/">Volver al inicio</a>
                </body>
            </html>
            """)
    
    except Exception as e:
        return HTMLResponse(f"""
        <html>
            <body>
                <h1>Error</h1>
                <p>Ocurrió un error al procesar la respuesta: {str(e)}</p>
                <a href="/">Volver al inicio</a>
            </body>
        </html>
        """)

@app.get("/webpay/status/{token}")
async def get_transaction_status(token: str):
    """Obtener el estado de una transacción"""
    try:
        result = webpay_service.get_transaction_status(token)
        
        # Buscar información adicional en la base de datos local
        local_transaction = next((t for t in transactions_db if t.get("token") == token), None)
        
        if local_transaction:
            result["local_info"] = local_transaction
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estado: {str(e)}")

@app.post("/webpay/refund/{token}")
async def refund_transaction(token: str, amount: int):
    """Anular o reversar una transacción"""
    try:
        result = webpay_service.refund_transaction(token, amount)
        
        if result["success"]:
            # Actualizar el estado en la base de datos local
            for transaction in transactions_db:
                if transaction.get("token") == token:
                    transaction["status"] = "refunded"
                    transaction["refund_info"] = result
                    break
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al anular transacción: {str(e)}")

@app.get("/transactions")
async def get_all_transactions():
    """Obtener todas las transacciones registradas"""
    return {
        "transactions": transactions_db,
        "total": len(transactions_db)
    }

@app.get("/transactions/{buy_order}")
async def get_transaction_by_order(buy_order: str):
    """Obtener una transacción por orden de compra"""
    transaction = next((t for t in transactions_db if t.get("buy_order") == buy_order), None)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    return transaction

# Para desarrollo local
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 