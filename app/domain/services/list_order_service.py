from typing import List, Optional
from app.domain.entities.order import Order
from app.domain.ports.order_repository_port import OrderRepositoryPort
from app.shared.enums.order_status import OrderStatus

class ListOrdersService:
    def __init__(self, repo: OrderRepositoryPort):
        self.repo = repo

    def execute(self, status: Optional[OrderStatus] = None, prioritized: bool = False):
        if prioritized and status is None:
            return self.repo.find_active_sorted_orders()
        return self.repo.find_all(status=status)

class GetOrderByIdService:
    def __init__(self, repo: OrderRepositoryPort):
        self.repo = repo
    def execute(self, order_id: int) -> Optional[Order]:
        return self.repo.find_by_id(order_id)

class ListOrdersByClientService:
    def __init__(self, repo: OrderRepositoryPort):
        self.repo = repo
    def execute(self, client_id: int) -> List[Order]:
        return self.repo.find_by_client(client_id)
