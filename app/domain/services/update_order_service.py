from app.domain.entities.order import Order
from app.domain.ports.order_repository_port import OrderRepositoryPort
from app.domain.ports.payment_status_port import PaymentGatewayPort
from app.shared.enums.order_status import OrderStatus
from app.shared.enums.payment_status import PaymentStatus


class UpdateOrderStatusService:

    def __init__(self, order_repo: OrderRepositoryPort,payment_port: PaymentGatewayPort) -> None:
        self.order_repo = order_repo
        self.payment_port = payment_port

    def execute(self, order_id: int, new_status: OrderStatus) -> Order:
        order = self.order_repo.find_by_id(order_id)
        if order is None:
            raise ValueError("Pedido não encontrado")

        if order.status is OrderStatus.RECEIVED and new_status is OrderStatus.IN_PROGRESS:
            payment_status = self.payment_port.get_status(order_id)
            if payment_status in (PaymentStatus.CANCELED,PaymentStatus.FAILED):
                new_status = OrderStatus.CANCELED
            elif payment_status is not PaymentStatus.PAID:
                raise ValueError("Não é possível alterar o status para diferente de RECEIVED sem que o pagamento esteja aprovado.")

        allowed = {
            OrderStatus.RECEIVED: {OrderStatus.IN_PROGRESS},
            OrderStatus.IN_PROGRESS: {OrderStatus.READY},
            OrderStatus.READY: {OrderStatus.COMPLETED},
            OrderStatus.CANCELED: {OrderStatus.CANCELED},
        }
        if new_status not in allowed.get(order.status, set()):
            raise ValueError(f"Transição {order.status} → {new_status} inválida")

        order.status = new_status
        return self.order_repo.update(order)
