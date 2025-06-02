#!/usr/bin/env python3
"""
Ejemplo de uso de la API del Banco Central de Chile en CowTracker
Demuestra cómo integrar datos económicos en aplicaciones de negocio
"""

import asyncio
import aiohttp
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional

class BCentralAPIClient:
    """Cliente para consumir la API del Banco Central a través de CowTracker"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    async def get_exchange_rate(self, start_date: str = None, end_date: str = None) -> Dict:
        """Obtener tipo de cambio USD/CLP"""
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        return await self._make_request("/bcentral/exchange-rate", params)
    
    async def get_uf_value(self, start_date: str = None, end_date: str = None) -> Dict:
        """Obtener valor de la UF"""
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        return await self._make_request("/bcentral/uf", params)
    
    async def get_utm_value(self, start_date: str = None, end_date: str = None) -> Dict:
        """Obtener valor de la UTM"""
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        
        return await self._make_request("/bcentral/utm", params)
    
    async def get_economic_indicators(self, date: str = None) -> Dict:
        """Obtener indicadores económicos del día"""
        params = {}
        if date:
            params['date'] = date
        
        return await self._make_request("/bcentral/economic-indicators", params)
    
    async def get_custom_series(self, series_code: str, start_date: str, end_date: str) -> Dict:
        """Obtener serie personalizada"""
        params = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        return await self._make_request(f"/bcentral/series/{series_code}", params)
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Realizar petición HTTP a la API"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.json()
                    raise Exception(f"Error {response.status}: {error_data.get('detail', 'Error desconocido')}")

class CowPriceAnalyzer:
    """Analizador de precios de ganado con contexto económico"""
    
    def __init__(self):
        self.api_client = BCentralAPIClient()
    
    async def analyze_cow_pricing(self, cow_price_clp: float, analysis_date: str = None) -> Dict:
        """
        Analizar el precio de una vaca en diferentes contextos económicos
        
        Args:
            cow_price_clp: Precio de la vaca en pesos chilenos
            analysis_date: Fecha del análisis (YYYY-MM-DD)
        
        Returns:
            Diccionario con análisis completo de precios
        """
        if not analysis_date:
            analysis_date = date.today().strftime("%Y-%m-%d")
        
        try:
            # Obtener indicadores económicos
            indicators = await self.api_client.get_economic_indicators(analysis_date)
            
            analysis = {
                "cow_price_clp": cow_price_clp,
                "analysis_date": analysis_date,
                "conversions": {},
                "economic_context": indicators.get("indicators", {}),
                "recommendations": []
            }
            
            # Conversión a UF
            if indicators["indicators"].get("uf"):
                uf_value = indicators["indicators"]["uf"]["valor"]
                cow_price_uf = cow_price_clp / uf_value
                analysis["conversions"]["uf"] = {
                    "value": round(cow_price_uf, 2),
                    "unit": "UF",
                    "uf_rate": uf_value
                }
                
                # Recomendación basada en UF
                if cow_price_uf < 30:
                    analysis["recommendations"].append("Precio competitivo en UF, buena oportunidad de compra")
                elif cow_price_uf > 50:
                    analysis["recommendations"].append("Precio alto en UF, considerar negociación")
            
            # Conversión a USD
            if indicators["indicators"].get("exchange_rate"):
                usd_rate = indicators["indicators"]["exchange_rate"]["valor"]
                cow_price_usd = cow_price_clp / usd_rate
                analysis["conversions"]["usd"] = {
                    "value": round(cow_price_usd, 2),
                    "unit": "USD",
                    "exchange_rate": usd_rate
                }
                
                # Recomendación basada en USD
                if cow_price_usd < 1500:
                    analysis["recommendations"].append("Precio atractivo en USD para exportación")
                elif cow_price_usd > 2500:
                    analysis["recommendations"].append("Precio elevado en USD, evaluar mercado local")
            
            # Conversión a UTM (para efectos tributarios)
            if indicators["indicators"].get("utm"):
                utm_value = indicators["indicators"]["utm"]["valor"]
                cow_price_utm = cow_price_clp / utm_value
                analysis["conversions"]["utm"] = {
                    "value": round(cow_price_utm, 2),
                    "unit": "UTM",
                    "utm_rate": utm_value
                }
            
            return analysis
            
        except Exception as e:
            return {
                "error": str(e),
                "cow_price_clp": cow_price_clp,
                "analysis_date": analysis_date
            }
    
    async def track_price_trends(self, days_back: int = 30) -> Dict:
        """
        Analizar tendencias de indicadores económicos para pricing
        
        Args:
            days_back: Días hacia atrás para el análisis
        
        Returns:
            Análisis de tendencias
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days_back)
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        try:
            # Obtener datos históricos
            exchange_data = await self.api_client.get_exchange_rate(start_str, end_str)
            uf_data = await self.api_client.get_uf_value(start_str, end_str)
            
            trends = {
                "period": f"{start_str} to {end_str}",
                "exchange_rate": self._analyze_trend(exchange_data.get("data", [])),
                "uf": self._analyze_trend(uf_data.get("data", [])),
                "recommendations": []
            }
            
            # Generar recomendaciones basadas en tendencias
            if trends["exchange_rate"].get("trend") == "increasing":
                trends["recommendations"].append("Dólar al alza: considerar ventas en USD o retener inventario")
            elif trends["exchange_rate"].get("trend") == "decreasing":
                trends["recommendations"].append("Dólar a la baja: oportunidad para importar insumos")
            
            if trends["uf"].get("trend") == "increasing":
                trends["recommendations"].append("UF al alza: precios en UF pueden ser más estables")
            
            return trends
            
        except Exception as e:
            return {"error": str(e)}
    
    def _analyze_trend(self, data: List[Dict]) -> Dict:
        """Analizar tendencia de una serie de datos"""
        if len(data) < 2:
            return {"trend": "insufficient_data"}
        
        values = [float(item["valor"]) for item in data if item.get("valor")]
        if len(values) < 2:
            return {"trend": "insufficient_data"}
        
        first_value = values[0]
        last_value = values[-1]
        change_percent = ((last_value - first_value) / first_value) * 100
        
        trend = "stable"
        if change_percent > 2:
            trend = "increasing"
        elif change_percent < -2:
            trend = "decreasing"
        
        return {
            "trend": trend,
            "first_value": first_value,
            "last_value": last_value,
            "change_percent": round(change_percent, 2),
            "min_value": min(values),
            "max_value": max(values),
            "avg_value": round(sum(values) / len(values), 2)
        }

async def example_usage():
    """Ejemplo de uso de las clases"""
    analyzer = CowPriceAnalyzer()
    
    print("🐄 CowTracker - Análisis de Precios con Banco Central")
    print("=" * 60)
    
    # Ejemplo 1: Análisis de precio individual
    print("\\n📊 Análisis de Precio Individual")
    cow_price = 1500000  # $1,500,000 CLP
    analysis = await analyzer.analyze_cow_pricing(cow_price)
    
    if "error" not in analysis:
        print(f"Precio original: ${analysis['cow_price_clp']:,.0f} CLP")
        print(f"Fecha de análisis: {analysis['analysis_date']}")
        
        if "uf" in analysis["conversions"]:
            uf_data = analysis["conversions"]["uf"]
            print(f"Precio en UF: {uf_data['value']} UF (1 UF = ${uf_data['uf_rate']:,.0f})")
        
        if "usd" in analysis["conversions"]:
            usd_data = analysis["conversions"]["usd"]
            print(f"Precio en USD: ${usd_data['value']:,.0f} USD (1 USD = ${usd_data['exchange_rate']:,.0f})")
        
        if analysis["recommendations"]:
            print("\\nRecomendaciones:")
            for rec in analysis["recommendations"]:
                print(f"• {rec}")
    else:
        print(f"Error en análisis: {analysis['error']}")
    
    # Ejemplo 2: Análisis de tendencias
    print("\\n📈 Análisis de Tendencias (últimos 30 días)")
    trends = await analyzer.track_price_trends(30)
    
    if "error" not in trends:
        print(f"Período: {trends['period']}")
        
        if "exchange_rate" in trends:
            ex_trend = trends["exchange_rate"]
            print(f"Tipo de cambio: {ex_trend.get('trend', 'N/A')} ({ex_trend.get('change_percent', 0)}%)")
        
        if "uf" in trends:
            uf_trend = trends["uf"]
            print(f"UF: {uf_trend.get('trend', 'N/A')} ({uf_trend.get('change_percent', 0)}%)")
        
        if trends["recommendations"]:
            print("\\nRecomendaciones estratégicas:")
            for rec in trends["recommendations"]:
                print(f"• {rec}")
    else:
        print(f"Error en análisis de tendencias: {trends['error']}")

    # Ejemplo 3: Comparación de múltiples vacas
    print("\\n🐮 Comparación de Múltiples Vacas")
    cow_prices = [1200000, 1500000, 1800000, 2200000]  # Diferentes precios
    
    for i, price in enumerate(cow_prices, 1):
        analysis = await analyzer.analyze_cow_pricing(price)
        if "error" not in analysis and "uf" in analysis["conversions"]:
            uf_price = analysis["conversions"]["uf"]["value"]
            print(f"Vaca {i}: ${price:,.0f} CLP = {uf_price:.1f} UF")

if __name__ == "__main__":
    print("Iniciando ejemplo de uso de API Banco Central...")
    print("Asegúrate de que el servidor FastAPI esté ejecutándose en http://localhost:8000")
    print()
    
    try:
        asyncio.run(example_usage())
    except KeyboardInterrupt:
        print("\\n🛑 Interrumpido por el usuario")
    except Exception as e:
        print(f"\\n❌ Error: {e}")
        print("\\n💡 Verifica que:")
        print("   1. El servidor FastAPI esté ejecutándose")
        print("   2. Las credenciales del Banco Central estén configuradas")
        print("   3. Tengas conexión a internet")
