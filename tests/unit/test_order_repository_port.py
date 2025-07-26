import pytest

from app.domain.ports.order_repository_port import OrderRepositoryPort
from app.domain.entities.order import Order
from app.shared.enums.order_status import OrderStatus


class DummyRepo(OrderRepositoryPort):

    def __init__(self):
        self._store: dict[int, Order] = {}
        self._pk = 1

    def create(self, order: Order) -> Order:
        order.id = self._pk
        self._store[self._pk] = order
        self._pk += 1
        return order

    def find_by_id(self, order_id: int):
        return self._store.get(order_id)

    def find_all(self, status: OrderStatus | None = None):
        return [
            o for o in self._store.values()
            if status is None or o.status == status
        ]

    def find_by_client(self, client_id: int):
        return [o for o in self._store.values() if o.client_id == client_id]

    def update(self, order: Order) -> Order:
        if order.id not in self._store:
            raise ValueError("not found")
        self._store[order.id] = order
        return order

    def delete(self, order_id: int):
        self._store.pop(order_id, None)


def test_cannot_instantiate_abstract():
    with pytest.raises(TypeError):
        OrderRepositoryPort()


def test_missing_one_method():
    class BadRepo(OrderRepositoryPort):
        def create(self, order): ...
        def find_by_id(self, order_id): ...
        def find_all(self, status): ...
        def find_by_client(self, client_id): ...
        def update(self, order): ...
    with pytest.raises(TypeError):
        BadRepo()


def test_dummy_repo_full_cycle():
    repo = DummyRepo()
    order = Order(client_id=1, amount=0.0)
    created = repo.create(order)

    assert repo.find_by_id(created.id) is created
    assert repo.find_all()[0] is created
    assert repo.find_by_client(1)[0] is created

    created.amount = 99.9
    assert repo.update(created).amount == 99.9

    repo.delete(created.id)
    assert repo.find_by_id(created.id) is None
