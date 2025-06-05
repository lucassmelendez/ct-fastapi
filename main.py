from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os

# Configurar variables de entorno para Supabase
try:
    import setup_env
    print("✅ Variables de entorno cargadas desde setup_env.py")
except ImportError:
    print("⚠️ No se pudo cargar setup_env.py, usando variables de entorno del sistema")
    
# Verificar si las credenciales de Supabase están configuradas
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_ANON_KEY')
if supabase_url and supabase_key:
    print(f"✅ Credenciales de Supabase configuradas: {supabase_url}")
else:
    print("❌ ADVERTENCIA: Credenciales de Supabase no configuradas")

from webpay_service import WebpayService
from bcentral_service import BCentralService
from config import AppConfig, WebpayConfig

# Crear la aplicación FastAPI
app = FastAPI(
    title="CowTracker API",
    description="API para el sistema de seguimiento de ganado con integración Webpay Plus",
    version="1.0.0"
)

# Configurar CORS usando la configuración
app.add_middleware(
    CORSMiddleware,
    allow_origins=AppConfig.get_cors_origins() + [
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "https://localhost:8081",
        "*"  # Permitir todos los orígenes temporalmente para desarrollo
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware adicional para manejar CORS manualmente
@app.middleware("http")
async def cors_handler(request: Request, call_next):
    response = await call_next(request)
    
    # Agregar headers CORS manualmente
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
    
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Origin, Accept"
    
    return response

# Endpoint OPTIONS para manejar preflight requests
@app.options("/webpay/create-transaction")
async def options_create_transaction():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Origin, Accept",
            "Access-Control-Allow-Credentials": "true"
        }
)

# Inicializar servicio de Webpay (usará la configuración de variables de entorno)
try:
    webpay_service = WebpayService()
    print(f"✅ Webpay configurado correctamente en ambiente: {WebpayConfig.get_environment()}")
except ValueError as e:
    print(f"❌ Error de configuración de Webpay: {e}")
    print("💡 Copia el archivo env.template a .env y configura las variables de entorno")
    webpay_service = None

# Inicializar servicio del Banco Central
try:
    bcentral_service = BCentralService()
    print("✅ Servicio del Banco Central inicializado correctamente")
except Exception as e:
    print(f"❌ Error de configuración del Banco Central: {e}")
    print("💡 Verifica las credenciales del Banco Central en el archivo .env")
    bcentral_service = None

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
    webpay_status = "enabled" if webpay_service else "disabled (check configuration)"
    return {
        "message": "Bienvenido a CowTracker API con Webpay Plus", 
        "status": "running",
        "webpay_status": webpay_status,
        "environment": WebpayConfig.get_environment() if webpay_service else "not configured"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "CowTracker API", 
        "webpay": "enabled" if webpay_service else "disabled",
        "environment": WebpayConfig.get_environment() if webpay_service else "not configured"
    }

@app.get("/config")
async def get_config():
    """Endpoint para verificar la configuración (sin mostrar credenciales)"""
    try:
        return {
            "webpay_environment": WebpayConfig.get_environment(),
            "webpay_host": WebpayConfig.get_host(),
            "return_url": WebpayConfig.get_return_url(),
            "cors_origins": AppConfig.get_cors_origins(),
            "app_debug": AppConfig.DEBUG
        }
    except Exception as e:
        return {
            "error": str(e),
            "message": "Error de configuración. Verifica que el archivo .env esté configurado correctamente."
        }

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
    if not webpay_service:
        raise HTTPException(
            status_code=500, 
            detail="Webpay no está configurado. Verifica las variables de entorno."
        )
    
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
                "environment": result["environment"],
                "created_at": result["created_at"]
            }
            transactions_db.append(transaction_data)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear transacción: {str(e)}")

@app.post("/cows/{cow_id}/purchase")
async def purchase_cow(cow_id: int, purchase_request: CowPurchaseRequest):
    """Iniciar el proceso de compra de una vaca"""
    if not webpay_service:
        raise HTTPException(
            status_code=500, 
            detail="Webpay no está configurado. Verifica las variables de entorno."
        )
    
    # Verificar que la vaca existe
    cow = next((cow for cow in cows_db if cow["id"] == cow_id), None)
    if not cow:
        raise HTTPException(status_code=404, detail="Vaca no encontrada")
    
    # Crear transacción de pago
    payment_request = PaymentRequest(
        amount=cow["price"],
        buy_order=f"cow_{cow_id}_{purchase_request.buyer_name.replace(' ', '_')}",
        session_id=f"session_{cow_id}_{purchase_request.buyer_email.split('@')[0]}",
        return_url=purchase_request.return_url or WebpayConfig.get_return_url(),
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
            "environment": result["environment"],
            "created_at": result["created_at"]
        }
        transactions_db.append(transaction_data)
        
        return {
            "success": True,
            "message": f"Transacción creada para la compra de {cow['name']}",
            "cow": cow,
            "payment_url": result["url"],
            "token": result["token"],
            "amount": result["amount"],
            "environment": result["environment"]
        }
    
    return result

@app.post("/webpay/confirm")
async def confirm_webpay_transaction(request: Request):
    """Confirmar una transacción de Webpay Plus"""
    if not webpay_service:
        raise HTTPException(
            status_code=500, 
            detail="Webpay no está configurado. Verifica las variables de entorno."
        )
    
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
async def webpay_return(token_ws: str = None, TBK_TOKEN: str = None, TBK_ORDEN_COMPRA: str = None, TBK_ID_SESION: str = None):
    """
    Endpoint que maneja el retorno desde Webpay después del pago
    """
    try:
        print(f"🔄 Procesando retorno de Webpay:")
        print(f"   - token_ws: {token_ws}")
        print(f"   - TBK_TOKEN: {TBK_TOKEN}")
        print(f"   - TBK_ORDEN_COMPRA: {TBK_ORDEN_COMPRA}")
        print(f"   - TBK_ID_SESION: {TBK_ID_SESION}")
        
        # Si hay TBK_TOKEN, significa que el usuario canceló o hubo error
        if TBK_TOKEN:
            print("❌ Transacción cancelada o con error")
            return HTMLResponse(content="""
                <!DOCTYPE html>
        <html>
                <head>
                    <title>Pago Cancelado - CowTracker</title>
                    <meta charset="utf-8">
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f8f9fa; }
                        .container { max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        .error { color: #e74c3c; font-size: 24px; margin-bottom: 20px; }
                        .message { color: #666; margin-bottom: 30px; }
                        .button { background: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; }
                    </style>
                </head>
            <body>
                    <div class="container">
                        <div class="error">❌ Pago Cancelado</div>
                        <div class="message">
                            El pago fue cancelado o no se pudo procesar. 
                            No se realizaron cargos a tu tarjeta.
                        </div>
                        <a href="#" onclick="window.close()" class="button">Cerrar Ventana</a>
                    </div>
            </body>
        </html>
        """)
    
        # Si no hay token_ws, es un error
        if not token_ws:
            print("❌ No se recibió token de transacción")
            return HTMLResponse(content="""
                <!DOCTYPE html>
            <html>
                <head>
                    <title>Error - CowTracker</title>
                    <meta charset="utf-8">
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f8f9fa; }
                        .container { max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        .error { color: #e74c3c; font-size: 24px; margin-bottom: 20px; }
                        .message { color: #666; margin-bottom: 30px; }
                        .button { background: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="error">❌ Error en el Pago</div>
                        <div class="message">
                            No se pudo procesar la información del pago. 
                            Por favor, intenta nuevamente.
                        </div>
                        <a href="#" onclick="window.close()" class="button">Cerrar Ventana</a>
                    </div>
                </body>
            </html>
            """)
        
        # Confirmar la transacción con Webpay
        webpay_service = WebpayService()
        transaction_result = webpay_service.confirm_transaction(token_ws)
        
        print(f"📥 Resultado de confirmación: {transaction_result}")
        
        if not transaction_result.get('success'):
            print("❌ Error al confirmar transacción")
            return HTMLResponse(content="""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Error de Pago - CowTracker</title>
                    <meta charset="utf-8">
                    <style>
                        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f8f9fa; }
                        .container { max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        .error { color: #e74c3c; font-size: 24px; margin-bottom: 20px; }
                        .message { color: #666; margin-bottom: 30px; }
                        .button { background: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="error">❌ Error en la Transacción</div>
                        <div class="message">
                            No se pudo confirmar el pago con el banco. 
                            Si se realizó un cargo, será reversado automáticamente.
                        </div>
                        <a href="#" onclick="window.close()" class="button">Cerrar Ventana</a>
                    </div>
                </body>
                </html>
            """)
        
        # Verificar que el pago fue aprobado
        response_code = transaction_result.get('response_code', 0)
        if response_code != 0:
            print(f"❌ Pago rechazado. Código de respuesta: {response_code}")
            return HTMLResponse(content=f"""
                <!DOCTYPE html>
            <html>
                <head>
                    <title>Pago Rechazado - CowTracker</title>
                    <meta charset="utf-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f8f9fa; }}
                        .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .error {{ color: #e74c3c; font-size: 24px; margin-bottom: 20px; }}
                        .message {{ color: #666; margin-bottom: 30px; }}
                        .button {{ background: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="error">❌ Pago Rechazado</div>
                        <div class="message">
                            El pago fue rechazado por el banco (Código: {response_code}). 
                            Por favor, verifica los datos de tu tarjeta e intenta nuevamente.
                        </div>
                        <a href="#" onclick="window.close()" class="button">Cerrar Ventana</a>
                    </div>
                </body>
            </html>
            """)
        
        # ✅ Pago exitoso - Redirigir al frontend local para que maneje la actualización
        buy_order = transaction_result.get('buy_order', '')
        amount = transaction_result.get('amount', 0)
        authorization_code = transaction_result.get('authorization_code', '')
        
        print(f"✅ Pago exitoso!")
        print(f"   - Buy Order: {buy_order}")
        print(f"   - Monto: {amount}")
        print(f"   - Código de autorización: {authorization_code}")
        
        # Redirigir al frontend local para que maneje la actualización del usuario
        return HTMLResponse(content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>¡Pago Exitoso! - CowTracker Premium</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #27ae60, #2ecc71); }}
                    .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
                    .success {{ color: #27ae60; font-size: 48px; margin-bottom: 20px; }}
                    .title {{ color: #2c3e50; font-size: 28px; font-weight: bold; margin-bottom: 15px; }}
                    .message {{ color: #666; margin-bottom: 30px; font-size: 16px; line-height: 1.5; }}
                    .details {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: left; }}
                    .premium-badge {{ background: linear-gradient(45deg, #f39c12, #e67e22); color: white; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; font-weight: bold; }}
                    .loading {{ color: #27ae60; font-size: 18px; margin: 20px 0; }}
                    .button {{ background: #27ae60; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: bold; margin: 10px; }}
                    .button:hover {{ background: #229954; }}
                    .secondary-button {{ background: #3498db; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; font-weight: bold; margin: 10px; }}
                    .secondary-button:hover {{ background: #2980b9; }}
                    @media (max-width: 600px) {{ 
                        body {{ padding: 20px; }}
                        .container {{ padding: 25px; }}
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success">🎉</div>
                    <div class="title">¡Pago Procesado Exitosamente!</div>
                    <div class="premium-badge">✨ ACTIVANDO PREMIUM ✨</div>
                    <div class="message">
                        Tu pago ha sido procesado exitosamente. Serás redirigido a CowTracker para activar tu cuenta Premium.
                    </div>
                    <div class="details">
                        <strong>📋 Detalles del pago:</strong><br><br>
                        🆔 Orden: {buy_order}<br>
                        💰 Monto: ${amount:,} CLP<br>
                        🔐 Autorización: {authorization_code}<br>
                        📅 Fecha: {transaction_result.get('transaction_date', 'N/A')}
                    </div>
                    <div class="loading" id="loading">
                        🔄 Redirigiendo a CowTracker...
                    </div>
                    <div id="buttons" style="display: none;">
                        <a href="http://localhost:8081/premium/activate?order={buy_order}&amount={amount}&auth={authorization_code}" class="button">
                            🖥️ Continuar en CowTracker Local
                        </a>
                        <a href="cowtracker://premium/activate?order={buy_order}&amount={amount}&auth={authorization_code}" class="secondary-button">
                            📱 Abrir App CowTracker
                        </a>
                    </div>
                </div>
                <script>
                    // Redirección automática al frontend local después de 2 segundos
                    setTimeout(function() {{
                        try {{
                            // Redirigir al frontend local
                            window.location.href = "http://localhost:8081/premium/activate?order={buy_order}&amount={amount}&auth={authorization_code}";
                        }} catch (e) {{
                            console.error("Error en redirección:", e);
                            // Mostrar botones como fallback
                            document.getElementById('loading').style.display = 'none';
                            document.getElementById('buttons').style.display = 'block';
                        }}
                    }}, 2000);
                    
                    // Mostrar botones después de 5 segundos como fallback
                    setTimeout(function() {{
                        document.getElementById('loading').style.display = 'none';
                        document.getElementById('buttons').style.display = 'block';
                    }}, 5000);
                </script>
            </body>
            </html>
        """)
    
    except Exception as e:
        print(f"❌ Error en webpay_return: {str(e)}")
        return HTMLResponse(content=f"""
            <!DOCTYPE html>
        <html>
            <head>
                <title>Error del Sistema - CowTracker</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f8f9fa; }}
                    .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    .error {{ color: #e74c3c; font-size: 24px; margin-bottom: 20px; }}
                    .message {{ color: #666; margin-bottom: 30px; }}
                    .button {{ background: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="error">❌ Error del Sistema</div>
                    <div class="message">
                        Ocurrió un error inesperado al procesar tu pago. 
                        Por favor, contacta a soporte técnico.
                    </div>
                    <div class="message">
                        <small>Error: {str(e)}</small>
                    </div>
                    <a href="#" onclick="window.close()" class="button">Cerrar Ventana</a>
                </div>
            </body>
        </html>
        """)

@app.get("/webpay/status/{token}")
async def get_transaction_status(token: str):
    """Obtener el estado de una transacción"""
    if not webpay_service:
        raise HTTPException(
            status_code=500, 
            detail="Webpay no está configurado. Verifica las variables de entorno."
        )
    
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
    if not webpay_service:
        raise HTTPException(
            status_code=500, 
            detail="Webpay no está configurado. Verifica las variables de entorno."
        )
    
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
        "total": len(transactions_db),
        "environment": WebpayConfig.get_environment() if webpay_service else "not configured"
    }

@app.get("/transactions/{buy_order}")
async def get_transaction_by_order(buy_order: str):
    """Obtener una transacción por orden de compra"""
    transaction = next((t for t in transactions_db if t.get("buy_order") == buy_order), None)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transacción no encontrada")
    return transaction

# Endpoints para conversión de moneda
@app.get("/currency/convert")
async def convert_currency_endpoint(amount: float, from_currency: str = "CLP", to_currency: str = "USD"):
    """
    Convertir un monto entre diferentes monedas usando datos del Banco Central de Chile
    
    Args:
        amount: Cantidad a convertir
        from_currency: Moneda de origen (CLP, USD, EUR, etc.)
        to_currency: Moneda de destino (CLP, USD, EUR, etc.)
    
    Returns:
        Resultado de la conversión con tipo de cambio actual
    """
    try:
        # Intentar usar el servicio del Banco Central primero
        if bcentral_service:
            try:
                result = bcentral_service.convert_currency(amount, from_currency, to_currency)
                
                if "error" not in result:
                    return {
                        "success": True,
                        "conversion": result,
                        "formatted": {
                            "original": f"{result['from_symbol']}{amount:,.0f}" if from_currency != "CLP" else f"${amount:,.0f}",
                            "converted": f"{result['to_symbol']}{result['converted_amount']:,.0f}" if to_currency != "CLP" else f"${result['converted_amount']:,.0f}",
                            "combined": f"${amount:,.0f}/{result['converted_amount']:.0f}{result['to_symbol']}" if from_currency == "CLP" and to_currency == "USD" else f"{result['from_symbol']}{amount:,.0f}/{result['to_symbol']}{result['converted_amount']:,.0f}"
                        },
                        "source": "Banco Central de Chile"
                    }
            except Exception as e:
                print(f"⚠️ Error en servicio Banco Central: {e}")
        
        # Fallback: usar tipo de cambio aproximado
        # Tipo de cambio aproximado USD/CLP (actualizar según sea necesario)
        usd_clp_rate = 950.0  # Aproximadamente 950 pesos por dólar
        
        if from_currency == "CLP" and to_currency == "USD":
            converted_amount = amount / usd_clp_rate
            return {
                "success": True,
                "conversion": {
                    "amount": amount,
                    "from_currency": from_currency,
                    "from_symbol": "$",
                    "to_currency": to_currency,
                    "to_symbol": "US$",
                    "converted_amount": round(converted_amount, 0),
                    "rate": usd_clp_rate
                },
                "formatted": {
                    "original": f"${amount:,.0f}",
                    "converted": f"US${converted_amount:.0f}",
                    "combined": f"${amount:,.0f}/{converted_amount:.0f}USD"
                },
                "source": "Tipo de cambio aproximado"
            }
        elif from_currency == "USD" and to_currency == "CLP":
            converted_amount = amount * usd_clp_rate
            return {
                "success": True,
                "conversion": {
                    "amount": amount,
                    "from_currency": from_currency,
                    "from_symbol": "US$",
                    "to_currency": to_currency,
                    "to_symbol": "$",
                    "converted_amount": round(converted_amount, 0),
                    "rate": usd_clp_rate
                },
                "formatted": {
                    "original": f"US${amount:,.0f}",
                    "converted": f"${converted_amount:,.0f}",
                    "combined": f"US${amount:,.0f}/${converted_amount:,.0f}"
                },
                "source": "Tipo de cambio aproximado"
            }
        else:
            # Para otras conversiones, devolver el mismo valor
            return {
                "success": True,
                "conversion": {
                    "amount": amount,
                    "from_currency": from_currency,
                    "from_symbol": "$" if from_currency == "CLP" else from_currency,
                    "to_currency": to_currency,
                    "to_symbol": "$" if to_currency == "CLP" else to_currency,
                    "converted_amount": amount,
                    "rate": 1.0
                },
                "formatted": {
                    "original": f"${amount:,.0f}",
                    "converted": f"${amount:,.0f}",
                    "combined": f"${amount:,.0f}"
                },
                "source": "Sin conversión"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en conversión: {str(e)}")

@app.get("/currency/rate/{currency}")
async def get_exchange_rate_endpoint(currency: str = "USD"):
    """
    Obtener el tipo de cambio actual para una moneda específica
    
    Args:
        currency: Código de moneda (USD, EUR, etc.)
    
    Returns:
        Tipo de cambio actual
    """
    try:
        # Intentar usar el servicio del Banco Central primero
        if bcentral_service:
            try:
                rates = bcentral_service.get_exchange_rate(currency=currency)
                
                if rates:
                    current_rate = rates[0]
                    return {
                        "success": True,
                        "currency": currency,
                        "rate": current_rate["valor"],
                        "date": current_rate["fecha"],
                        "formatted_rate": f"1 {currency} = ${current_rate['valor']:,.2f} CLP",
                        "source": "Banco Central de Chile"
                    }
            except Exception as e:
                print(f"⚠️ Error en servicio Banco Central: {e}")
        
        # Fallback: usar tipo de cambio aproximado
        if currency.upper() == "USD":
            rate = 950.0
            return {
                "success": True,
                "currency": currency,
                "rate": rate,
                "date": "2024-01-01",  # Fecha aproximada
                "formatted_rate": f"1 {currency} = ${rate:,.2f} CLP",
                "source": "Tipo de cambio aproximado"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Tipo de cambio no disponible para {currency}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener tipo de cambio: {str(e)}")

# Para desarrollo local
if __name__ == "__main__":
    uvicorn.run(app, host=AppConfig.HOST, port=AppConfig.PORT, debug=AppConfig.DEBUG) 