from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

# Crear la aplicación FastAPI
app = FastAPI(
    title="CowTracker API",
    description="API para el sistema de seguimiento de ganado",
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

# Base de datos simulada (en producción usarías una base de datos real)
cows_db = [
    {"id": 1, "name": "Bessie", "breed": "Holstein", "age": 3, "weight": 650.5, "health_status": "healthy"},
    {"id": 2, "name": "Daisy", "breed": "Jersey", "age": 2, "weight": 450.0, "health_status": "healthy"},
    {"id": 3, "name": "Moo", "breed": "Angus", "age": 4, "weight": 800.0, "health_status": "sick"}
]

# Rutas de la API
@app.get("/")
async def root():
    return {"message": "Bienvenido a CowTracker API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "CowTracker API"}

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

# Para desarrollo local
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 