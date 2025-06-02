from transbank.webpay.webpay_plus.transaction import Transaction
import uuid
from datetime import datetime
from typing import Dict, Any
from config import WebpayConfig

class WebpayService:
    def __init__(self, environment: str = None):
        """
        Inicializa el servicio de Webpay Plus
        
        Args:
            environment: "integration" para pruebas, "production" para producción
                        Si no se especifica, se obtiene de las variables de entorno
        """
        # Usar el ambiente especificado o el de la configuración
        if environment:
            self.environment = environment
        else:
            self.environment = WebpayConfig.get_environment()
        
        try:
            # Configurar las credenciales según la documentación oficial
            # El SDK viene preconfigurado para integración por defecto
            if self.environment == "production":
                # Para producción, configurar las credenciales específicas
                Transaction.commerce_code = WebpayConfig.get_commerce_code()
                Transaction.api_key = WebpayConfig.get_api_key()
                # En producción se debe configurar para LIVE
                # Transaction.integration_type = IntegrationType.LIVE
            else:
                # Para integración, usar las credenciales por defecto o configuradas
                Transaction.commerce_code = WebpayConfig.get_commerce_code()
                Transaction.api_key = WebpayConfig.get_api_key()
                # Para integración se mantiene el valor por defecto TEST
            
            # Crear instancia de transacción
            self.transaction = Transaction()
            
        except ValueError as e:
            raise ValueError(f"Error de configuración de Webpay: {str(e)}")
    
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
                return_url = WebpayConfig.get_return_url()
            
            print(f"🔄 Creando transacción Webpay:")
            print(f"   - Amount: {amount}")
            print(f"   - Buy Order: {buy_order}")
            print(f"   - Session ID: {session_id}")
            print(f"   - Return URL: {return_url}")
            print(f"   - Environment: {self.environment}")
            
            # Crear la transacción
            response = self.transaction.create(
                buy_order=buy_order,
                session_id=session_id,
                amount=amount,
                return_url=return_url
            )
            
            print(f"📥 Respuesta de Webpay: {type(response)}")
            print(f"📥 Contenido: {response}")
            
            # Manejar tanto objetos como diccionarios
            if hasattr(response, 'token') and hasattr(response, 'url'):
                # Es un objeto con atributos
                token = response.token
                url = response.url
            elif isinstance(response, dict):
                # Es un diccionario
                token = response.get('token')
                url = response.get('url')
            else:
                # Intentar acceder como atributos primero, luego como diccionario
                try:
                    token = getattr(response, 'token', None)
                    url = getattr(response, 'url', None)
                except:
                    token = response.get('token') if hasattr(response, 'get') else None
                    url = response.get('url') if hasattr(response, 'get') else None
            
            if not token or not url:
                raise ValueError(f"Respuesta inválida de Webpay. Token: {token}, URL: {url}")
            
            result = {
                "success": True,
                "token": token,
                "url": url,
                "buy_order": buy_order,
                "session_id": session_id,
                "amount": amount,
                "environment": self.environment,
                "created_at": datetime.now().isoformat()
            }
            
            print(f"✅ Transacción creada exitosamente: {result}")
            return result
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error al crear transacción: {error_msg}")
            print(f"❌ Tipo de error: {type(e)}")
            
            return {
                "success": False,
                "error": error_msg,
                "message": "Error al crear la transacción",
                "environment": self.environment
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
            print(f"🔄 Confirmando transacción con token: {token}")
            response = self.transaction.commit(token)
            
            print(f"📥 Tipo de respuesta de Webpay: {type(response)}")
            print(f"📥 Respuesta completa: {response}")
            
            # Si la respuesta es un diccionario, devolverlo directamente
            if isinstance(response, dict):
                if 'error' in response:
                    print(f"❌ Error reportado por Webpay: {response['error']}")
                    return {
                        "success": False,
                        "error": response.get('error', 'Error desconocido'),
                        "message": "Error al confirmar la transacción",
                        "environment": self.environment
                    }
                
                # Si es un diccionario de éxito, agregar success
                response_with_success = {
                    "success": True,
                    "environment": self.environment,
                    **response
                }
                return response_with_success
                
            # Crear una estructura consistente a partir de un objeto de respuesta
            try:
                return {
                    "success": True,
                    "vci": getattr(response, 'vci', None),
                    "amount": getattr(response, 'amount', 0),
                    "status": getattr(response, 'status', None),
                    "buy_order": getattr(response, 'buy_order', None),
                    "session_id": getattr(response, 'session_id', None),
                    "card_detail": {
                        "card_number": getattr(response.card_detail, 'card_number', None) if hasattr(response, 'card_detail') else None
                    },
                    "accounting_date": getattr(response, 'accounting_date', None),
                    "transaction_date": getattr(response, 'transaction_date', None),
                    "authorization_code": getattr(response, 'authorization_code', None),
                    "payment_type_code": getattr(response, 'payment_type_code', None),
                    "response_code": getattr(response, 'response_code', None),
                    "installments_number": getattr(response, 'installments_number', None),
                    "environment": self.environment
                }
            except AttributeError as attr_error:
                print(f"❌ Error de atributo: {attr_error}")
                # Intentar acceder como diccionario si falla como atributo
                return {
                    "success": True,
                    "vci": response.get('vci') if hasattr(response, 'get') else None,
                    "amount": response.get('amount', 0) if hasattr(response, 'get') else 0,
                    "status": response.get('status') if hasattr(response, 'get') else None,
                    "buy_order": response.get('buy_order') if hasattr(response, 'get') else None,
                    "session_id": response.get('session_id') if hasattr(response, 'get') else None,
                    "card_detail": {
                        "card_number": response.get('card_detail', {}).get('card_number') if hasattr(response, 'get') else None
                    },
                    "accounting_date": response.get('accounting_date') if hasattr(response, 'get') else None,
                    "transaction_date": response.get('transaction_date') if hasattr(response, 'get') else None,
                    "authorization_code": response.get('authorization_code') if hasattr(response, 'get') else None,
                    "payment_type_code": response.get('payment_type_code') if hasattr(response, 'get') else None,
                    "response_code": response.get('response_code') if hasattr(response, 'get') else None,
                    "installments_number": response.get('installments_number') if hasattr(response, 'get') else None,
                    "environment": self.environment
                }
                
        except Exception as e:
            print(f"❌ Error en confirm_transaction: {str(e)}")
            print(f"❌ Tipo de error: {type(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "message": "Error al confirmar la transacción",
                "environment": self.environment
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
                "installments_number": response.installments_number,
                "environment": self.environment
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error al obtener el estado de la transacción",
                "environment": self.environment
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
                "response_code": response.response_code,
                "environment": self.environment
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error al anular la transacción",
                "environment": self.environment
            } 