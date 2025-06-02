import os
import requests
import xml.etree.ElementTree as ET
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Union, Any
from urllib.parse import urlencode

logger = logging.getLogger("cowtracker.bcentral")

class BCentralService:
    """
    Servicio para interactuar con la API del Banco Central de Chile
    Documentación: https://si3.bcentral.cl/estadisticas/Principal1/Web_Services/doc_es.htm
    """
    
    # Códigos de series temporales para diferentes tipos de cambio
    SERIES_CODES = {
        "DOLAR_OBSERVADO": "F073.TCO.PRE.Z.D",    # Dólar Observado
        "EURO": "F073.TCO.EUR.Z.D",               # Euro
        "UF": "F073.IPC.UF.CLF.D",                # Unidad de Fomento
        "UTM": "F074.ITM.UTM.CLP.M",              # Unidad Tributaria Mensual
        "IMACEC": "F032.PIB.IND.IMACEC.M",        # IMACEC (Índice Mensual de Actividad Económica)
        "IPC": "F074.IPC.IPC.VAR.Z.M",            # IPC (Índice de Precios al Consumidor)
        "LIBRA_ESTERLINA": "F073.TCO.GBP.Z.D",    # Libra Esterlina
        "YEN_JAPONES": "F073.TCO.JPY.Z.D",        # Yen Japonés
        "DOLAR_CANADIENSE": "F073.TCO.CAD.Z.D",   # Dólar Canadiense
        "DOLAR_AUSTRALIANO": "F073.TCO.AUD.Z.D",  # Dólar Australiano
        "YUAN_CHINO": "F073.TCO.CNY.Z.D",         # Yuan Chino
    }
    
    # Diccionario de monedas soportadas y sus símbolos
    CURRENCIES = {
        "CLP": {"name": "Peso Chileno", "symbol": "$"},
        "USD": {"name": "Dólar Estadounidense", "symbol": "US$"},
        "EUR": {"name": "Euro", "symbol": "€"},
        "GBP": {"name": "Libra Esterlina", "symbol": "£"},
        "JPY": {"name": "Yen Japonés", "symbol": "¥"},
        "CAD": {"name": "Dólar Canadiense", "symbol": "C$"},
        "AUD": {"name": "Dólar Australiano", "symbol": "A$"},
        "CNY": {"name": "Yuan Chino", "symbol": "¥"},
        "UF": {"name": "Unidad de Fomento", "symbol": "UF"},
        "UTM": {"name": "Unidad Tributaria Mensual", "symbol": "UTM"},
    }
    
    def __init__(self):
        """Inicializar el servicio con credenciales del Banco Central"""
        self.base_url = os.getenv("BCENTRAL_BASE_URL", "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx")
        self.user = os.getenv("BCENTRAL_USER")
        self.password = os.getenv("BCENTRAL_PASSWORD")
        
        if not self.user or not self.password:
            logger.warning("⚠️ Credenciales del Banco Central no configuradas correctamente")
        else:
            logger.info(f"✅ Servicio del Banco Central inicializado para usuario: {self.user}")
    
    def _build_url(self, timeseries: str, first_date: str, last_date: str, function: str = "GetSeries") -> str:
        """
        Construir URL para consultar la API del Banco Central
        
        Args:
            timeseries: Código de serie temporal
            first_date: Fecha inicial en formato YYYY-MM-DD
            last_date: Fecha final en formato YYYY-MM-DD
            function: Función API (por defecto: GetSeries)
            
        Returns:
            URL completa para la consulta
        """
        params = {
            "user": self.user,
            "pass": self.password,
            "firstdate": first_date,
            "lastdate": last_date,
            "timeseries": timeseries,
            "function": function
        }
        url = f"{self.base_url}?{urlencode(params)}"
        logger.debug(f"URL generada: {url}")
        return url
    
    def _parse_xml_response(self, xml_content: str) -> List[Dict]:
        """
        Parsear respuesta XML del Banco Central
        
        Args:
            xml_content: Contenido XML 
            
        Returns:
            Lista de diccionarios con datos
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Buscar los datos en la estructura XML
            data = []
            
            # Buscar elementos Serie
            for serie in root.findall('.//Serie'):
                serie_code = serie.get('codigo', '')
                serie_name = serie.get('nombre', '')
                serie_unit = serie.get('unidad', '')
                
                # Buscar observaciones
                for obs in serie.findall('.//Obs'):
                    fecha_str = obs.get('indexDateString', '')
                    valor_str = obs.get('value', '')
                    
                    # Convertir valor a float si es posible
                    valor = None
                    if valor_str and valor_str not in ['', 'NaN', '.']:
                        try:
                            valor = float(valor_str)
                        except ValueError:
                            valor = valor_str
                    
                    if fecha_str:
                        try:
                            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                            fecha_iso = fecha.isoformat()
                        except ValueError:
                            fecha_iso = fecha_str
                            
                        data.append({
                            'serie_codigo': serie_code,
                            'serie_nombre': serie_name,
                            'unidad': serie_unit,
                            'fecha': fecha_iso,
                            'valor': valor
                        })
            
            return data
            
        except ET.ParseError as e:
            logger.error(f"Error al parsear XML: {e}")
            return []
        except Exception as e:
            logger.error(f"Error procesando datos: {e}")
            return []
    
    def _request_series_data(self, series_code: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Obtener datos de una serie temporal
        
        Args:
            series_code: Código de la serie temporal
            start_date: Fecha inicial (YYYY-MM-DD)
            end_date: Fecha final (YYYY-MM-DD)
            
        Returns:
            Lista de datos de la serie
        """
        url = self._build_url(series_code, start_date, end_date)
        
        try:
            logger.info(f"Consultando API Banco Central: {series_code} ({start_date} a {end_date})")
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return self._parse_xml_response(response.text)
            else:
                logger.error(f"Error en API Banco Central: {response.status_code} - {response.text}")
                return []
                
        except requests.exceptions.Timeout:
            logger.error("Timeout al conectar con API Banco Central")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al conectar con API Banco Central: {e}")
            return []
    
    def get_exchange_rate(self, start_date: Optional[str] = None, end_date: Optional[str] = None, 
                         currency: str = "USD") -> List[Dict]:
        """
        Obtener tipo de cambio para una moneda específica
        
        Args:
            start_date: Fecha inicial (YYYY-MM-DD)
            end_date: Fecha final (YYYY-MM-DD)
            currency: Código de moneda (USD, EUR, GBP, etc.)
            
        Returns:
            Lista de valores del tipo de cambio
        """
        # Si no se especifican fechas, usar últimos 30 días
        if not start_date:
            end = date.today()
            start = end - timedelta(days=30)
            start_date = start.isoformat()
            end_date = end.isoformat()
        
        # Si solo se especifica fecha inicial, usar esa y el día de hoy
        if not end_date:
            end_date = date.today().isoformat()
            
        # Determinar el código de serie según la moneda
        currency_code = currency.upper()
        series_code = None
        
        if currency_code == "USD":
            series_code = self.SERIES_CODES["DOLAR_OBSERVADO"]
        elif currency_code == "EUR":
            series_code = self.SERIES_CODES["EURO"]
        elif currency_code == "GBP":
            series_code = self.SERIES_CODES["LIBRA_ESTERLINA"]
        elif currency_code == "JPY":
            series_code = self.SERIES_CODES["YEN_JAPONES"]
        elif currency_code == "CAD":
            series_code = self.SERIES_CODES["DOLAR_CANADIENSE"]
        elif currency_code == "AUD":
            series_code = self.SERIES_CODES["DOLAR_AUSTRALIANO"]
        elif currency_code == "CNY":
            series_code = self.SERIES_CODES["YUAN_CHINO"]
        else:
            logger.error(f"Moneda no soportada: {currency}")
            return []
            
        return self._request_series_data(series_code, start_date, end_date)
        
    def get_uf_value(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """
        Obtener valor de la Unidad de Fomento (UF)
        
        Args:
            start_date: Fecha inicial (YYYY-MM-DD)
            end_date: Fecha final (YYYY-MM-DD)
            
        Returns:
            Lista de valores UF
        """
        # Si no se especifican fechas, usar últimos 30 días
        if not start_date:
            end = date.today()
            start = end - timedelta(days=30)
            start_date = start.isoformat()
            end_date = end.isoformat()
        
        # Si solo se especifica fecha inicial, usar esa y el día de hoy
        if not end_date:
            end_date = date.today().isoformat()
            
        return self._request_series_data(self.SERIES_CODES["UF"], start_date, end_date)
    
    def get_utm_value(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """
        Obtener valor de la Unidad Tributaria Mensual (UTM)
        
        Args:
            start_date: Fecha inicial (YYYY-MM-DD)
            end_date: Fecha final (YYYY-MM-DD)
            
        Returns:
            Lista de valores UTM
        """
        # Si no se especifican fechas, usar últimos 6 meses
        if not start_date:
            end = date.today()
            start = end - timedelta(days=180)  # ~6 meses
            start_date = start.isoformat()
            end_date = end.isoformat()
        
        # Si solo se especifica fecha inicial, usar esa y el día de hoy
        if not end_date:
            end_date = date.today().isoformat()
            
        return self._request_series_data(self.SERIES_CODES["UTM"], start_date, end_date)
    
    def get_economic_indicators(self, specific_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener indicadores económicos para una fecha específica
        
        Args:
            specific_date: Fecha específica (YYYY-MM-DD)
            
        Returns:
            Diccionario con indicadores económicos
        """
        if not specific_date:
            specific_date = date.today().isoformat()
            
        # Obtener datos de varios indicadores
        end_date = specific_date
        start_date = (datetime.strptime(specific_date, '%Y-%m-%d') - timedelta(days=7)).strftime('%Y-%m-%d')
        
        indicators = {}
        
        # Dólar observado
        dolar_data = self._request_series_data(self.SERIES_CODES["DOLAR_OBSERVADO"], start_date, end_date)
        if dolar_data:
            indicators["dolar"] = dolar_data[-1]["valor"] if dolar_data[-1]["valor"] else None
            
        # Euro
        euro_data = self._request_series_data(self.SERIES_CODES["EURO"], start_date, end_date)
        if euro_data:
            indicators["euro"] = euro_data[-1]["valor"] if euro_data[-1]["valor"] else None
            
        # UF
        uf_data = self._request_series_data(self.SERIES_CODES["UF"], start_date, end_date)
        if uf_data:
            indicators["uf"] = uf_data[-1]["valor"] if uf_data[-1]["valor"] else None
            
        # UTM (se mantiene mensual)
        start_date_utm = (datetime.strptime(specific_date, '%Y-%m-%d') - timedelta(days=31)).strftime('%Y-%m-%d')
        utm_data = self._request_series_data(self.SERIES_CODES["UTM"], start_date_utm, end_date)
        if utm_data:
            indicators["utm"] = utm_data[-1]["valor"] if utm_data[-1]["valor"] else None
            
        # Valores adicionales para contexto
        indicators["fecha"] = specific_date
        indicators["actualizacion"] = datetime.now().isoformat()
        
        return indicators
    
    def get_available_series(self) -> Dict[str, str]:
        """
        Obtener lista de series temporales disponibles
        
        Returns:
            Diccionario con códigos y nombres de series
        """
        return {
            "DOLAR_OBSERVADO": self.SERIES_CODES["DOLAR_OBSERVADO"],
            "EURO": self.SERIES_CODES["EURO"],
            "UF": self.SERIES_CODES["UF"],
            "UTM": self.SERIES_CODES["UTM"],
            "IMACEC": self.SERIES_CODES["IMACEC"],
            "IPC": self.SERIES_CODES["IPC"],
            "LIBRA_ESTERLINA": self.SERIES_CODES["LIBRA_ESTERLINA"],
            "YEN_JAPONES": self.SERIES_CODES["YEN_JAPONES"],
            "DOLAR_CANADIENSE": self.SERIES_CODES["DOLAR_CANADIENSE"],
            "DOLAR_AUSTRALIANO": self.SERIES_CODES["DOLAR_AUSTRALIANO"],
            "YUAN_CHINO": self.SERIES_CODES["YUAN_CHINO"]
        }
    
    def get_custom_series(self, series_code: str, start_date: Optional[str] = None, 
                         end_date: Optional[str] = None) -> List[Dict]:
        """
        Obtener datos de una serie temporal personalizada
        
        Args:
            series_code: Código de la serie temporal
            start_date: Fecha inicial (YYYY-MM-DD)
            end_date: Fecha final (YYYY-MM-DD)
            
        Returns:
            Lista de datos de la serie
        """
        # Si no se especifican fechas, usar últimos 30 días
        if not start_date:
            end = date.today()
            start = end - timedelta(days=30)
            start_date = start.isoformat()
            end_date = end.isoformat()
        
        # Si solo se especifica fecha inicial, usar esa y el día de hoy
        if not end_date:
            end_date = date.today().isoformat()
            
        return self._request_series_data(series_code, start_date, end_date)
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str, 
                        conversion_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Convertir un monto entre diferentes monedas
        
        Args:
            amount: Cantidad a convertir
            from_currency: Moneda de origen (CLP, USD, EUR, UF, etc.)
            to_currency: Moneda de destino (CLP, USD, EUR, UF, etc.)
            conversion_date: Fecha para usar en la conversión (YYYY-MM-DD)
            
        Returns:
            Diccionario con resultado de la conversión
        """
        if not conversion_date:
            conversion_date = date.today().isoformat()
            
        # Validar monedas soportadas
        if from_currency not in self.CURRENCIES:
            logger.error(f"Moneda de origen no soportada: {from_currency}")
            return {"error": f"Moneda de origen no soportada: {from_currency}"}
            
        if to_currency not in self.CURRENCIES:
            logger.error(f"Moneda de destino no soportada: {to_currency}")
            return {"error": f"Moneda de destino no soportada: {to_currency}"}
        
        # Si son la misma moneda, devolver el mismo monto
        if from_currency == to_currency:
            return {
                "amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency,
                "converted_amount": amount,
                "conversion_date": conversion_date,
                "rate": 1.0
            }
            
        # Caso especial: conversión entre CLP y otras monedas
        if from_currency == "CLP" or to_currency == "CLP":
            # Obtener el tipo de cambio necesario
            currency_code = to_currency if from_currency == "CLP" else from_currency
            
            # Manejar casos especiales: UF y UTM
            if currency_code == "UF":
                rates = self.get_uf_value(start_date=conversion_date, end_date=conversion_date)
            elif currency_code == "UTM":
                rates = self.get_utm_value(start_date=conversion_date, end_date=conversion_date)
            else:
                rates = self.get_exchange_rate(start_date=conversion_date, end_date=conversion_date, 
                                             currency=currency_code)
                
            if not rates:
                logger.error(f"No se encontró tipo de cambio para {currency_code} en {conversion_date}")
                return {"error": f"No se encontró tipo de cambio para {currency_code} en {conversion_date}"}
                
            # Obtener el tipo de cambio
            rate = rates[0]["valor"]
            
            # Realizar conversión
            if from_currency == "CLP":
                converted_amount = amount / rate
            else:
                converted_amount = amount * rate
                
            return {
                "amount": amount,
                "from_currency": from_currency,
                "from_symbol": self.CURRENCIES[from_currency]["symbol"],
                "to_currency": to_currency,
                "to_symbol": self.CURRENCIES[to_currency]["symbol"],
                "converted_amount": round(converted_amount, 2),
                "conversion_date": conversion_date,
                "rate": rate
            }
            
        # Caso general: conversión entre dos monedas extranjeras
        # Primero convertimos a CLP y luego a la moneda de destino
        # from_currency → CLP → to_currency
        
        # Paso 1: Convertir a CLP
        clp_conversion = self.convert_currency(amount, from_currency, "CLP", conversion_date)
        if "error" in clp_conversion:
            return clp_conversion
            
        # Paso 2: Convertir de CLP a la moneda de destino
        result = self.convert_currency(clp_conversion["converted_amount"], "CLP", to_currency, conversion_date)
        
        # Añadir información adicional
        if "error" not in result:
            result["original_amount"] = amount
            result["from_currency"] = from_currency
            result["intermediate_clp"] = clp_conversion["converted_amount"]
            
        return result
        
    def get_currency_symbols(self) -> Dict[str, Dict[str, str]]:
        """
        Obtener símbolos y nombres de las monedas soportadas
        
        Returns:
            Diccionario con información de las monedas
        """
        return self.CURRENCIES