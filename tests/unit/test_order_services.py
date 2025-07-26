import pytest

from app.domain.entities.order import Order
from app.domain.entities.item import OrderItem
from app.shared.enums.order_status import OrderStatus

from app.domain.services.create_order_service import CreateOrderService
from app.domain.services.list_order_service import (
    ListOrdersService,
    GetOrderByIdService,
    ListOrdersByClientService,
)
from app.domain.services.update_order_service import UpdateOrderStatusService
from app.domain.ports.order_repository_port import OrderRepositoryPort


class DummyRepo(OrderRepositoryPort):
    def __init__(self):
        self.store: dict[int, Order] = {}
        self._pk = 1
        self.last_status = None

    def create(self, order: Order) -> Order:
        order.id = self._pk
        self.store[self._pk] = order
        self._pk += 1
        return order
    def find_by_id(self, oid: int):
        return self.store.get(oid)
    def find_all(self, status=None):
        self.last_status = status
        return [
            o for o in self.store.values()
            if status is None or o.status == status
        ]
    def find_by_client(self, cid: int):
        return [o for o in self.store.values() if o.client_id == cid]
    def update(self, order: Order):
        if order.id not in self.store:
            raise ValueError("not found")
        self.store[order.id] = order
        return order
    def delete(self, oid: int): self.store.pop(oid, None)

    def find_active_sorted_orders(self) -> list[Order]:
        return sorted(
            [o for o in self.orders if o.status != OrderStatus.COMPLETED and o.active],
            key=lambda o: (
                {
                    OrderStatus.READY: 1,
                    OrderStatus.IN_PROGRESS: 2,
                    OrderStatus.RECEIVED: 3,
                }.get(o.status, 9999),
                o.id,
            ),
        )

class DummyCatalog:
    def __init__(self, stock=10, price=5):
        self.stock = stock
        self.price = price
        self.reserved = 0
    def get_product(self, pid):
        return {"id": pid, "name": "Burger", "stock": self.stock, "price": self.price}
    def reserve_stock(self, pid, qty):
        self.stock -= qty
        self.reserved += qty


def test_create_order_success():
    repo = DummyRepo()
    catalog = DummyCatalog(stock=5, price=4)
    service = CreateOrderService(repo, catalog)

    order = Order(items=[OrderItem(product_id="SKU", quantity=2)])
    created = service.execute(order)

    assert created.amount == 8.0
    assert created.items[0].name == "Burger"
    assert catalog.reserved == 2


def test_create_order_insufficient_stock():
    repo = DummyRepo()
    catalog = DummyCatalog(stock=1, price=3)
    service = CreateOrderService(repo, catalog)

    with pytest.raises(ValueError, match="Estoque insuficiente"):
        service.execute(Order(items=[OrderItem(product_id="SKU", quantity=5)]))


def test_list_services():
    repo = DummyRepo()
    repo.create(Order(client_id=1, status=OrderStatus.RECEIVED))
    repo.create(Order(client_id=2, status=OrderStatus.READY))

    assert len(ListOrdersService(repo).execute()) == 2
    ready = ListOrdersService(repo).execute(OrderStatus.READY)
    assert len(ready) == 1 and ready[0].status == OrderStatus.READY
    assert repo.last_status == OrderStatus.READY

    got = GetOrderByIdService(repo).execute(1)
    assert got.id == 1

    assert len(ListOrdersByClientService(repo).execute(2)) == 1


def test_update_status_success():
    repo = DummyRepo()
    order = repo.create(Order(status=OrderStatus.RECEIVED))
    updated = UpdateOrderStatusService(repo).execute(order.id, OrderStatus.IN_PROGRESS)
    assert updated.status == OrderStatus.IN_PROGRESS


def test_update_status_invalid_transition():
    repo = DummyRepo()
    order = repo.create(Order(status=OrderStatus.RECEIVED))
    with pytest.raises(ValueError, match="inválida"):
        UpdateOrderStatusService(repo).execute(order.id, OrderStatus.COMPLETED)


def test_update_status_not_found():
    repo = DummyRepo()
    with pytest.raises(ValueError, match="Pedido não encontrado"):
        UpdateOrderStatusService(repo).execute(999, OrderStatus.READY)
