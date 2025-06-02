# CowTracker API - Backend FastAPI

API REST para el sistema de seguimiento de ganado CowTracker, desarrollada con FastAPI y optimizada para despliegue en Vercel.

## 🚀 Características

- **FastAPI**: Framework moderno y rápido para APIs
- **Documentación automática**: Swagger UI y ReDoc incluidos
- **CORS configurado**: Listo para frontend
- **Validación de datos**: Con Pydantic
- **Optimizado para Vercel**: Configuración lista para despliegue

## 📋 Endpoints Disponibles

### Información General
- `GET /` - Mensaje de bienvenida
- `GET /health` - Estado de salud de la API
- `GET /docs` - Documentación Swagger UI
- `GET /redoc` - Documentación ReDoc

### Gestión de Vacas
- `GET /cows` - Obtener todas las vacas
- `GET /cows/{cow_id}` - Obtener una vaca específica
- `POST /cows` - Crear una nueva vaca
- `PUT /cows/{cow_id}` - Actualizar una vaca
- `DELETE /cows/{cow_id}` - Eliminar una vaca

### Filtros
- `GET /cows/breed/{breed}` - Filtrar por raza
- `GET /cows/health/{status}` - Filtrar por estado de salud

## 🛠️ Instalación Local

1. **Clonar el repositorio**
```bash
cd ct-FastApi
```

2. **Crear entorno virtual**
```bash
python -m venv venv
```

3. **Activar entorno virtual**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

5. **Ejecutar la aplicación**
```bash
python main.py
```

La API estará disponible en: `http://localhost:8000`

## 🌐 Despliegue en Vercel

### Opción 1: Desde GitHub
1. Sube tu código a un repositorio de GitHub
2. Conecta tu cuenta de Vercel con GitHub
3. Importa el proyecto desde Vercel Dashboard
4. Vercel detectará automáticamente la configuración

### Opción 2: Vercel CLI
1. **Instalar Vercel CLI**
```bash
npm i -g vercel
```

2. **Iniciar sesión**
```bash
vercel login
```

3. **Desplegar**
```bash
vercel
```

4. **Desplegar a producción**
```bash
vercel --prod
```

## 📝 Ejemplo de Uso

### Crear una nueva vaca
```bash
curl -X POST "https://tu-api.vercel.app/cows" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Luna",
       "breed": "Holstein",
       "age": 2,
       "weight": 500.0,
       "health_status": "healthy"
     }'
```

### Obtener todas las vacas
```bash
curl "https://tu-api.vercel.app/cows"
```

## 🔧 Estructura del Proyecto

```
ct-FastApi/
├── main.py              # Aplicación principal FastAPI
├── api/
│   └── index.py         # Punto de entrada para Vercel
├── requirements.txt     # Dependencias Python
├── vercel.json         # Configuración de Vercel
└── README.md           # Este archivo
```

## 📊 Modelo de Datos

### Cow (Vaca)
```json
{
  "id": 1,
  "name": "Bessie",
  "breed": "Holstein",
  "age": 3,
  "weight": 650.5,
  "health_status": "healthy"
}
```

## 🔒 Consideraciones de Seguridad

- En producción, configura CORS con dominios específicos
- Implementa autenticación y autorización según sea necesario
- Usa variables de entorno para configuraciones sensibles
- Considera implementar rate limiting

## 🗄️ Base de Datos

Actualmente usa una base de datos en memoria para demostración. Para producción, considera:
- PostgreSQL con SQLAlchemy
- MongoDB con Motor
- SQLite para proyectos pequeños

## 📚 Documentación API

Una vez desplegada, la documentación estará disponible en:
- Swagger UI: `https://tu-api.vercel.app/docs`
- ReDoc: `https://tu-api.vercel.app/redoc` 