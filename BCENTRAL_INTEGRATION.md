# 🏦 Integración API Banco Central de Chile

## Descripción

Esta integración permite acceder a los datos económicos oficiales del Banco Central de Chile directamente desde la API de CowTracker. La implementación sigue la documentación oficial disponible en: https://si3.bcentral.cl/estadisticas/Principal1/Web_Services/doc_es.htm

## Configuración

### Variables de Entorno (.env)

```properties
# Configuración Banco Central
BCENTRAL_BASE_URL=https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx
BCENTRAL_USER=tu_usuario@example.com
BCENTRAL_PASSWORD=tu_password_aqui
```

## Endpoints Disponibles

### 📈 Tipo de Cambio USD/CLP

**GET** `/bcentral/exchange-rate`

Parámetros opcionales:
- `start_date`: Fecha inicial (YYYY-MM-DD)
- `end_date`: Fecha final (YYYY-MM-DD)

```bash
curl "http://localhost:8000/bcentral/exchange-rate?start_date=2024-01-01&end_date=2024-01-31"
```

### 🏠 Valor UF (Unidad de Fomento)

**GET** `/bcentral/uf`

Parámetros opcionales:
- `start_date`: Fecha inicial (YYYY-MM-DD)
- `end_date`: Fecha final (YYYY-MM-DD)

```bash
curl "http://localhost:8000/bcentral/uf?start_date=2024-01-01&end_date=2024-01-31"
```

### 📋 Valor UTM (Unidad Tributaria Mensual)

**GET** `/bcentral/utm`

Parámetros opcionales:
- `start_date`: Fecha inicial (YYYY-MM-DD)
- `end_date`: Fecha final (YYYY-MM-DD)

```bash
curl "http://localhost:8000/bcentral/utm?start_date=2024-01-01&end_date=2024-01-31"
```

### 📊 Indicadores Económicos del Día

**GET** `/bcentral/economic-indicators`

Parámetros opcionales:
- `date`: Fecha específica (YYYY-MM-DD)

```bash
curl "http://localhost:8000/bcentral/economic-indicators?date=2024-01-15"
```

### 📋 Series Disponibles

**GET** `/bcentral/series`

Retorna una lista de las series más comunes disponibles.

```bash
curl "http://localhost:8000/bcentral/series"
```

### 🔧 Serie Personalizada

**GET** `/bcentral/series/{series_code}`

Parámetros:
- `series_code`: Código de la serie temporal
- `start_date`: Fecha inicial (opcional)
- `end_date`: Fecha final (opcional)

```bash
curl "http://localhost:8000/bcentral/series/F073.TCO.PRE.Z.D?start_date=2024-01-01&end_date=2024-01-31"
```

## Códigos de Series Más Comunes

| Código | Descripción |
|--------|-------------|
| `F073.TCO.PRE.Z.D` | Tipo de cambio USD/CLP |
| `F073.UF.PRE.Z.D` | Unidad de Fomento (UF) |
| `F073.UTM.PRE.Z.M` | Unidad Tributaria Mensual (UTM) |
| `F072.IPC.PRE.Z.M` | Índice de Precios al Consumidor (IPC) |
| `F032.IPM.FRU.Z.M` | Índice de Producción Manufacturera |
| `F031.INE.DESE.Z.M` | Tasa de Desempleo |

## Estructura de Respuesta

```json
{
  "success": true,
  "data": [
    {
      "serie": "F073.TCO.PRE.Z.D",
      "fecha": "2024-01-01",
      "valor": 920.15
    }
  ],
  "series": "Tipo de cambio USD/CLP",
  "source": "Banco Central de Chile"
}
```

## Manejo de Errores

La API retorna errores HTTP estándar:

- **400 Bad Request**: Parámetros inválidos
- **500 Internal Server Error**: Error en la consulta al Banco Central o procesamiento de datos

```json
{
  "detail": "Error al obtener tipo de cambio: mensaje de error"
}
```

## Pruebas

### Documentación Interactiva
Visita `http://localhost:8000/docs` para probar los endpoints desde la documentación automática de FastAPI.

### Página de Pruebas HTML
Abre `test_bcentral.html` en tu navegador para una interfaz amigable de pruebas.

### Ejemplos con curl

```bash
# Obtener tipo de cambio actual
curl "http://localhost:8000/bcentral/exchange-rate"

# Obtener UF del último mes
curl "http://localhost:8000/bcentral/uf?start_date=2024-05-01&end_date=2024-05-31"

# Obtener todos los indicadores de un día específico
curl "http://localhost:8000/bcentral/economic-indicators?date=2024-01-15"
```

## Limitaciones y Consideraciones

1. **Autenticación**: Requiere credenciales válidas del Banco Central de Chile
2. **Límites de Rate**: El Banco Central puede tener límites en las consultas por minuto/hora
3. **Disponibilidad de Datos**: Algunos datos pueden no estar disponibles para fechas muy recientes o muy antiguas
4. **Formato de Fechas**: Todas las fechas deben estar en formato YYYY-MM-DD
5. **Timeout**: Las consultas tienen un timeout de 30 segundos

## Casos de Uso en CowTracker

### Valorización de Ganado en UF
```python
# Convertir el precio de una vaca a UF
uf_value = await get_uf_value("2024-01-15", "2024-01-15")
cow_price_clp = 1500000
cow_price_uf = cow_price_clp / uf_value[0]["valor"]
```

### Conversión a USD
```python
# Convertir precio a USD
exchange_rate = await get_exchange_rate("2024-01-15", "2024-01-15")
cow_price_usd = cow_price_clp / exchange_rate[0]["valor"]
```

### Reportes Económicos
```python
# Generar reporte con contexto económico
indicators = await get_economic_indicators("2024-01-15")
report = {
    "cattle_sales": sales_data,
    "economic_context": indicators
}
```

## Soporte

Para problemas relacionados con la API del Banco Central, consulta:
- [Documentación Oficial](https://si3.bcentral.cl/estadisticas/Principal1/Web_Services/doc_es.htm)
- [Portal del Banco Central](https://www.bcentral.cl/)

Para problemas con la integración en CowTracker, revisa los logs del servidor y verifica la configuración de las credenciales.
