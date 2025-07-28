from abc import ABC, abstractmethod
from app.shared.enums.payment_status import PaymentStatus

class PaymentGatewayPort(ABC):
    @abstractmethod
    def get_status(self, order_id: int) -> PaymentStatus: ...

    @abstractmethod
    def create_payment(self, order_id: int, amount: float) -> tuple[str, PaymentStatus]:
        """Retorna (qr_code, status_inicial)"""
