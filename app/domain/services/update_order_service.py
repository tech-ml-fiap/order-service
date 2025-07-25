from app.domain.entities.order import Order
from app.domain.ports.order_repository_port import OrderRepositoryPort
from app.shared.enums.order_status import OrderStatus


class UpdateOrderStatusService:

    def __init__(self, order_repo: OrderRepositoryPort) -> None:
        self.order_repo = order_repo

    def execute(self, order_id: int, new_status: OrderStatus) -> Order:
        order = self.order_repo.find_by_id(order_id)
        if order is None:
            raise ValueError("Pedido não encontrado")

        allowed = {
            OrderStatus.RECEIVED: {OrderStatus.IN_PROGRESS},
            OrderStatus.IN_PROGRESS: {OrderStatus.READY},
            OrderStatus.READY: {OrderStatus.COMPLETED},
        }
        if new_status not in allowed.get(order.status, set()):
            raise ValueError(f"Transição {order.status} → {new_status} inválida")

        order.status = new_status
        return self.order_repo.update(order)
