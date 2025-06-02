# CowTracker API - Backend FastAPI con Webpay Plus

API REST para el sistema de seguimiento de ganado CowTracker, desarrollada con FastAPI y con integración completa de Webpay Plus para procesamiento de pagos, optimizada para despliegue en Vercel.

## 🚀 Características

- **FastAPI**: Framework moderno y rápido para APIs
- **Webpay Plus**: Integración completa con el sistema de pagos de Transbank
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

### 💳 Webpay Plus - Pagos
- `POST /webpay/create-transaction` - Crear una nueva transacción de pago
- `POST /cows/{cow_id}/purchase` - Iniciar compra de una vaca específica
- `POST /webpay/confirm` - Confirmar una transacción (webhook)
- `GET /webpay/return` - Página de retorno después del pago
- `GET /webpay/status/{token}` - Obtener estado de una transacción
- `POST /webpay/refund/{token}` - Anular/reversar una transacción

### Gestión de Transacciones
- `GET /transactions` - Obtener todas las transacciones
- `GET /transactions/{buy_order}` - Obtener transacción por orden de compra

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

## 🧪 Pruebas con Webpay Plus

### Datos de Prueba (Ambiente de Integración)
- **Tarjeta de Crédito:** 4051 8856 0044 6623
- **CVV:** 123
- **Fecha de vencimiento:** Cualquier fecha futura (ej: 12/25)
- **RUT:** 11.111.111-1

### Página de Prueba
Abre el archivo `test_webpay.html` en tu navegador para probar la integración completa.

## 💳 Flujo de Pago Webpay Plus

1. **Crear Transacción**: El cliente solicita una transacción
2. **Redirección**: Se redirige al usuario a Webpay Plus
3. **Pago**: El usuario ingresa sus datos de tarjeta
4. **Retorno**: Webpay redirige de vuelta a tu aplicación
5. **Confirmación**: Se confirma automáticamente la transacción
6. **Resultado**: Se muestra el resultado del pago

## 📝 Ejemplos de Uso

### Crear una transacción de pago
```bash
curl -X POST "http://localhost:8000/webpay/create-transaction" \
     -H "Content-Type: application/json" \
     -d '{
       "amount": 50000,
       "description": "Compra de vaca Holstein",
       "return_url": "http://localhost:8000/webpay/return"
     }'
```

### Comprar una vaca específica
```bash
curl -X POST "http://localhost:8000/cows/1/purchase" \
     -H "Content-Type: application/json" \
     -d '{
       "cow_id": 1,
       "buyer_name": "Juan Pérez",
       "buyer_email": "juan@email.com"
     }'
```

### Obtener estado de una transacción
```bash
curl "http://localhost:8000/webpay/status/TOKEN_AQUI"
```

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

## 🔧 Estructura del Proyecto

```
ct-FastApi/
├── main.py              # Aplicación principal FastAPI
├── webpay_service.py    # Servicio de Webpay Plus
├── api/
│   └── index.py         # Punto de entrada para Vercel
├── requirements.txt     # Dependencias Python
├── vercel.json         # Configuración de Vercel
├── test_webpay.html    # Página de prueba
├── runtime.txt         # Versión de Python
├── .gitignore          # Archivos a ignorar
└── README.md           # Este archivo
```

## 📊 Modelos de Datos

### Cow (Vaca)
```json
{
  "id": 1,
  "name": "Bessie",
  "breed": "Holstein",
  "age": 3,
  "weight": 650.5,
  "health_status": "healthy",
  "price": 1500000
}
```

### Payment Request (Solicitud de Pago)
```json
{
  "amount": 50000,
  "buy_order": "cow_order_12345",
  "session_id": "session_67890",
  "return_url": "http://localhost:8000/webpay/return",
  "description": "Compra de vaca Holstein"
}
```

### Transaction Response (Respuesta de Transacción)
```json
{
  "success": true,
  "token": "e9d555262db0f989e49d724b4db0b0af367cc415cde41f500a776550fc5fddd7",
  "url": "https://webpay3gint.transbank.cl/webpayserver/initTransaction",
  "buy_order": "cow_order_12345",
  "amount": 50000
}
```

## 🔒 Configuración de Producción

Para usar en producción, debes:

1. **Obtener credenciales reales** de Transbank
2. **Configurar variables de entorno**:
```bash
WEBPAY_COMMERCE_CODE=tu_codigo_comercio
WEBPAY_API_KEY=tu_api_key_real
WEBPAY_ENVIRONMENT=production
```

3. **Actualizar el servicio**:
```python
# En webpay_service.py
webpay_service = WebpayService(environment="production")
```

4. **Configurar CORS** con dominios específicos
5. **Implementar HTTPS** (requerido por Webpay)

## 🔒 Consideraciones de Seguridad

- **HTTPS obligatorio** en producción para Webpay
- Configurar CORS con dominios específicos
- Validar siempre las respuestas de Webpay
- Implementar logs de transacciones
- Usar variables de entorno para credenciales
- Implementar rate limiting para endpoints de pago

## 🗄️ Base de Datos

Actualmente usa una base de datos en memoria para demostración. Para producción, considera:
- **PostgreSQL** con SQLAlchemy para transacciones
- **Redis** para cache de sesiones
- **MongoDB** para logs de transacciones
- **SQLite** para proyectos pequeños

## 📚 Documentación API

Una vez desplegada, la documentación estará disponible en:
- **Swagger UI**: `https://tu-api.vercel.app/docs`
- **ReDoc**: `https://tu-api.vercel.app/redoc`

## 🆘 Solución de Problemas

### Error: "Token no válido"
- Verifica que el token no haya expirado (5 minutos)
- Asegúrate de usar el token correcto en la confirmación

### Error: "Transacción rechazada"
- Verifica los datos de la tarjeta de prueba
- Asegúrate de estar en el ambiente correcto (integración/producción)

### Error de CORS
- Configura los orígenes permitidos en el middleware CORS
- Verifica que el frontend esté en un dominio permitido

## 📞 Soporte

Para más información sobre Webpay Plus:
- [Documentación oficial de Transbank](https://www.transbankdevelopers.cl/)
- [SDK Python de Transbank](https://github.com/TransbankDevelopers/transbank-sdk-python) 