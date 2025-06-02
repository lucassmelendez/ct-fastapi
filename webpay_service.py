from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.options import Options
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_api_keys import IntegrationApiKeys
from transbank.common.integration_type import IntegrationType
import uuid
from datetime import datetime
from typing import Dict, Any

class WebpayService:
    def __init__(self, environment: str = "integration"):
        """
        Inicializa el servicio de Webpay Plus
        
        Args:
            environment: "integration" para pruebas, "production" para producción
        """
        if environment == "integration":
            self.options = Options(
                commerce_code=IntegrationCommerceCodes.WEBPAY_PLUS,
                api_key=IntegrationApiKeys.WEBPAY,
                integration_type=IntegrationType.TEST
            )
        else:
            # Para producción, deberás configurar tus credenciales reales
            self.options = Options(
                commerce_code="TU_CODIGO_COMERCIO",  # Reemplazar con código real
                api_key="TU_API_KEY",  # Reemplazar con API key real
                integration_type=IntegrationType.LIVE
            )
        
        self.transaction = Transaction(self.options)
    
    def create_transaction(self, amount: int, buy_order: str = None, session_id: str = None, return_url: str = None) -> Dict[str, Any]:
        """
        Crea una nueva transacción en Webpay Plus
        
        Args:
            amount: Monto en pesos chilenos
            buy_order: Orden de compra (opcional, se genera automáticamente)
            session_id: ID de sesión (opcional, se genera automáticamente)
            return_url: URL de retorno después del pago
            
        Returns:
            Dict con token y URL de redirección
        """
        try:
            # Generar valores por defecto si no se proporcionan
            if not buy_order:
                buy_order = f"cow_order_{uuid.uuid4().hex[:8]}"
            
            if not session_id:
                session_id = f"session_{uuid.uuid4().hex[:8]}"
            
            if not return_url:
                return_url = "http://localhost:8000/webpay/return"  # URL por defecto
            
            # Crear la transacción
            response = self.transaction.create(
                buy_order=buy_order,
                session_id=session_id,
                amount=amount,
                return_url=return_url
            )
            
            return {
                "success": True,
                "token": response.token,
                "url": response.url,
                "buy_order": buy_order,
                "session_id": session_id,
                "amount": amount,
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error al crear la transacción"
            }
    
    def confirm_transaction(self, token: str) -> Dict[str, Any]:
        """
        Confirma una transacción después del pago
        
        Args:
            token: Token de la transacción
            
        Returns:
            Dict con los detalles de la transacción confirmada
        """
        try:
            response = self.transaction.commit(token)
            
            return {
                "success": True,
                "vci": response.vci,
                "amount": response.amount,
                "status": response.status,
                "buy_order": response.buy_order,
                "session_id": response.session_id,
                "card_detail": {
                    "card_number": response.card_detail.card_number if hasattr(response, 'card_detail') else None
                },
                "accounting_date": response.accounting_date,
                "transaction_date": response.transaction_date,
                "authorization_code": response.authorization_code,
                "payment_type_code": response.payment_type_code,
                "response_code": response.response_code,
                "installments_number": response.installments_number
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error al confirmar la transacción"
            }
    
    def get_transaction_status(self, token: str) -> Dict[str, Any]:
        """
        Obtiene el estado de una transacción
        
        Args:
            token: Token de la transacción
            
        Returns:
            Dict con el estado de la transacción
        """
        try:
            response = self.transaction.status(token)
            
            return {
                "success": True,
                "vci": response.vci,
                "amount": response.amount,
                "status": response.status,
                "buy_order": response.buy_order,
                "session_id": response.session_id,
                "card_detail": {
                    "card_number": response.card_detail.card_number if hasattr(response, 'card_detail') else None
                },
                "accounting_date": response.accounting_date,
                "transaction_date": response.transaction_date,
                "authorization_code": response.authorization_code,
                "payment_type_code": response.payment_type_code,
                "response_code": response.response_code,
                "installments_number": response.installments_number
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error al obtener el estado de la transacción"
            }
    
    def refund_transaction(self, token: str, amount: int) -> Dict[str, Any]:
        """
        Anula o reversa una transacción
        
        Args:
            token: Token de la transacción
            amount: Monto a anular
            
        Returns:
            Dict con el resultado de la anulación
        """
        try:
            response = self.transaction.refund(token, amount)
            
            return {
                "success": True,
                "type": response.type,
                "authorization_code": response.authorization_code,
                "authorization_date": response.authorization_date,
                "nullified_amount": response.nullified_amount,
                "balance": response.balance,
                "response_code": response.response_code
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error al anular la transacción"
            } 