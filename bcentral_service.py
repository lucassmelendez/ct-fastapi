import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, date
from typing import List, Dict, Optional
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)

class BCentralService:
    """
    Servicio para interactuar con la API del Banco Central de Chile
    Documentación: https://si3.bcentral.cl/estadisticas/Principal1/Web_Services/doc_es.htm
    """
    
    def __init__(self):
        self.base_url = os.getenv("BCENTRAL_BASE_URL", "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx")
        self.user = os.getenv("BCENTRAL_USER")
        self.password = os.getenv("BCENTRAL_PASSWORD")
        
        if not self.user or not self.password:
            logger.warning("Credenciales del Banco Central no configuradas")
    
    def _build_url(self, timeseries: str, first_date: str, last_date: str, function: str = "GetSeries") -> str:
        """
        Construye la URL para la API del Banco Central
        
        Args:
            timeseries: Código de la serie temporal
            first_date: Fecha inicial (YYYY-MM-DD)
            last_date: Fecha final (YYYY-MM-DD)
            function: Función a ejecutar (GetSeries por defecto)
        
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
        return f"{self.base_url}?{urlencode(params)}"
    
    def _parse_xml_response(self, xml_content: str) -> List[Dict]:
        """
        Parsea la respuesta XML del Banco Central
        
        Args:
            xml_content: Contenido XML de la respuesta
            
        Returns:
            Lista de diccionarios con los datos parseados
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Buscar los datos en la estructura XML
            # El formato puede variar según la API, ajustar según sea necesario
            data = []
            
            # Buscar elementos Serie
            for serie in root.findall('.//Serie'):
                serie_code = serie.get('codigo', '')
                
                # Buscar observaciones
                for obs in serie.findall('.//Obs'):
                    fecha = obs.get('indexDateString', '')
                    valor = obs.get('value', '')
                    
                    if fecha and valor:
                        data.append({
                            'serie': serie_code,
                            'fecha': fecha,
                            'valor': float(valor) if valor.replace('.', '').replace('-', '').isdigit() else None
                        })
            
            return data
            
        except ET.ParseError as e:
            logger.error(f"Error parsing XML: {e}")
            return []
        except Exception as e:
            logger.error(f"Error processing data: {e}")
            return []
    
    def get_exchange_rate(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        Obtiene el tipo de cambio USD/CLP
        
        Args:
            start_date: Fecha inicial (YYYY-MM-DD). Si no se especifica, usa fecha actual
            end_date: Fecha final (YYYY-MM-DD). Si no se especifica, usa fecha actual
        
        Returns:
            Lista con los datos del tipo de cambio
        """
        if not start_date:
            start_date = date.today().strftime("%Y-%m-%d")
        if not end_date:
            end_date = start_date
            
        # Código de serie para tipo de cambio USD/CLP
        timeseries = "F073.TCO.PRE.Z.D"
        
        return self._get_series_data(timeseries, start_date, end_date)
    
    def get_uf_value(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        Obtiene el valor de la UF (Unidad de Fomento)
        
        Args:
            start_date: Fecha inicial (YYYY-MM-DD)
            end_date: Fecha final (YYYY-MM-DD)
        
        Returns:
            Lista con los valores de la UF
        """
        if not start_date:
            start_date = date.today().strftime("%Y-%m-%d")
        if not end_date:
            end_date = start_date
            
        # Código de serie para UF
        timeseries = "F073.UF.PRE.Z.D"
        
        return self._get_series_data(timeseries, start_date, end_date)
    
    def get_utm_value(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        Obtiene el valor de la UTM (Unidad Tributaria Mensual)
        
        Args:
            start_date: Fecha inicial (YYYY-MM-DD)
            end_date: Fecha final (YYYY-MM-DD)
        
        Returns:
            Lista con los valores de la UTM
        """
        if not start_date:
            start_date = date.today().strftime("%Y-%m-%d")
        if not end_date:
            end_date = start_date
            
        # Código de serie para UTM
        timeseries = "F073.UTM.PRE.Z.M"
        
        return self._get_series_data(timeseries, start_date, end_date)
    
    def _get_series_data(self, timeseries: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Método genérico para obtener datos de series temporales
        
        Args:
            timeseries: Código de la serie temporal
            start_date: Fecha inicial
            end_date: Fecha final
            
        Returns:
            Lista con los datos de la serie
        """
        if not self.user or not self.password:
            raise ValueError("Credenciales del Banco Central no configuradas")
        
        try:
            url = self._build_url(timeseries, start_date, end_date)
            
            logger.info(f"Consultando Banco Central: {timeseries} desde {start_date} hasta {end_date}")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # La respuesta debería ser XML
            if response.headers.get('content-type', '').startswith('text/xml') or \
               response.headers.get('content-type', '').startswith('application/xml'):
                return self._parse_xml_response(response.text)
            else:
                logger.warning(f"Respuesta no es XML: {response.headers.get('content-type')}")
                return []
                
        except requests.RequestException as e:
            logger.error(f"Error en la consulta al Banco Central: {e}")
            raise
        except Exception as e:
            logger.error(f"Error procesando respuesta del Banco Central: {e}")
            raise
    
    def get_available_series(self) -> List[str]:
        """
        Retorna una lista de las series más comunes disponibles
        
        Returns:
            Lista de códigos de series con descripción
        """
        return [
            "F073.TCO.PRE.Z.D - Tipo de cambio USD/CLP",
            "F073.UF.PRE.Z.D - Unidad de Fomento (UF)",
            "F073.UTM.PRE.Z.M - Unidad Tributaria Mensual (UTM)",
            "F072.IPC.PRE.Z.M - Índice de Precios al Consumidor (IPC)",
            "F032.IPM.FRU.Z.M - Índice de Producción Manufacturera",
            "F031.INE.DESE.Z.M - Tasa de Desempleo"
        ]
