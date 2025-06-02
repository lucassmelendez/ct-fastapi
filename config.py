import os
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env si existe
load_dotenv()

class WebpayConfig:
    """Configuración para Webpay Plus"""
    
    @classmethod
    def get_environment(cls) -> str:
        """Obtiene el ambiente desde variables de entorno"""
        return os.getenv("WEBPAY_ENVIRONMENT", "integration")
    
    @classmethod
    def get_commerce_code(cls) -> str:
        """Obtiene el código de comercio según el ambiente"""
        env = cls.get_environment()
        if env == "production":
            commerce_code = os.getenv("WEBPAY_COMMERCE_CODE_PROD")
            if not commerce_code:
                raise ValueError("WEBPAY_COMMERCE_CODE_PROD no está configurado para producción")
            return commerce_code
        else:
            commerce_code = os.getenv("WEBPAY_COMMERCE_CODE")
            if not commerce_code:
                raise ValueError("WEBPAY_COMMERCE_CODE no está configurado. Copia env.template a .env y configura las variables.")
            return commerce_code
    
    @classmethod
    def get_api_key(cls) -> str:
        """Obtiene la API key según el ambiente"""
        env = cls.get_environment()
        if env == "production":
            api_key = os.getenv("WEBPAY_API_KEY_PROD")
            if not api_key:
                raise ValueError("WEBPAY_API_KEY_PROD no está configurado para producción")
            return api_key
        else:
            api_key = os.getenv("WEBPAY_API_KEY")
            if not api_key:
                raise ValueError("WEBPAY_API_KEY no está configurado. Copia env.template a .env y configura las variables.")
            return api_key
    
    @classmethod
    def get_return_url(cls) -> str:
        """Obtiene la URL de retorno"""
        return os.getenv("WEBPAY_RETURN_URL", "http://localhost:8000/webpay/return")
    
    @classmethod
    def get_integration_host(cls) -> str:
        """Obtiene el host de integración"""
        return os.getenv("WEBPAY_INTEGRATION_HOST", "https://webpay3gint.transbank.cl")
    
    @classmethod
    def get_production_host(cls) -> str:
        """Obtiene el host de producción"""
        return os.getenv("WEBPAY_PRODUCTION_HOST", "https://webpay3g.transbank.cl")
    
    @classmethod
    def get_host(cls) -> str:
        """Obtiene el host según el ambiente"""
        env = cls.get_environment()
        if env == "production":
            return cls.get_production_host()
        else:
            return cls.get_integration_host()

class AppConfig:
    """Configuración general de la aplicación"""
    
    HOST = os.getenv("APP_HOST", "0.0.0.0")
    PORT = int(os.getenv("APP_PORT", "8000"))
    DEBUG = os.getenv("APP_DEBUG", "true").lower() == "true"
    
    # CORS
    @classmethod
    def get_cors_origins(cls) -> list:
        """Obtiene los orígenes permitidos para CORS"""
        # Orígenes por defecto para desarrollo y producción
        default_origins = [
            "http://localhost:3000",
            "http://localhost:8080", 
            "http://localhost:8081",  # React Native/Expo
            "http://127.0.0.1:5500",
            "http://127.0.0.1:8081",  # React Native/Expo alternativo
            "http://192.168.1.1:8081", # Para dispositivos móviles en red local
            "http://192.168.0.1:8081", # Para dispositivos móviles en red local
            "http://10.0.2.2:8081",   # Para emulador Android
            "https://ct-fastapi.vercel.app",  # Tu dominio de Vercel
            "*"  # Permitir todos los orígenes (solo para desarrollo)
        ]
        
        origins_str = os.getenv("CORS_ORIGINS", ",".join(default_origins))
        origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
        
        # Si estamos en desarrollo, agregar algunos orígenes adicionales comunes
        if cls.DEBUG:
            additional_dev_origins = [
                "http://localhost:19006",  # Expo web
                "http://localhost:19000",  # Expo DevTools
                "exp://localhost:19000",   # Expo app
                "exp://127.0.0.1:19000",   # Expo app alternativo
            ]
            origins.extend(additional_dev_origins)
        
        return list(set(origins))  # Eliminar duplicados
    
    # Base de datos
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cowtracker.db")
    
    # Logs
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO") 