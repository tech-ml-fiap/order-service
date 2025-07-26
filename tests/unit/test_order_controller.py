from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.adapters.driver.controllers.order_controller as oc
from app.shared.enums.order_status import OrderStatus
from app.domain.entities.order import Order
from app.domain.entities.item import OrderItem


def sample_order(order_id=1, status=OrderStatus.RECEIVED) -> Order:
    return Order(
        id=order_id,
        client_id=None,
        status=status,
        amount=20.0,
        items=[OrderItem(id=10, product_id="SKU", name="Burger", quantity=2, price=10)],
    )


class _OkSvc:
    def __init__(self, *_): ...
    def execute(self, *_, **__):
        return sample_order()


class _ErrSvc:
    def __init__(self, *_): ...
    def execute(self, *_, **__):
        raise ValueError("boom")


app = FastAPI()
app.include_router(oc.router)
app.dependency_overrides[oc.get_db_session] = lambda: None
client = TestClient(app)


def test_create_order_success(monkeypatch):
    monkeypatch.setattr(oc, "CreateOrderService", _OkSvc)
    resp = client.post("/orders", json={"items": [{"product_id": "P", "quantity": 1}]})
    assert resp.status_code == 201
    assert resp.json()["items"][0]["name"] == "Burger"


def test_create_order_error(monkeypatch):
    monkeypatch.setattr(oc, "CreateOrderService", _ErrSvc)
    resp = client.post("/orders", json={"items": [{"product_id": "P", "quantity": 1}]})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "boom"


def test_list_orders(monkeypatch):
    class _Svc(_OkSvc):
        def execute(self, status=None):
            assert status in (None, OrderStatus.READY)
            return [sample_order()]
    monkeypatch.setattr(oc, "ListOrdersService", lambda repo: _Svc())

    assert client.get("/orders").status_code == 200

    assert client.get("/orders", params={"status": OrderStatus.READY.value}).status_code == 200


def test_get_order_found(monkeypatch):
    monkeypatch.setattr(oc, "GetOrderByIdService", lambda repo: _OkSvc())
    resp = client.get("/orders/1")
    assert resp.status_code == 200 and resp.json()["id"] == 1


def test_get_order_not_found(monkeypatch):
    class _NoneSvc:
        def __init__(self, *_): ...
        def execute(self, *_): return None
    monkeypatch.setattr(oc, "GetOrderByIdService", lambda repo: _NoneSvc())
    assert client.get("/orders/999").status_code == 404


def test_update_status_success(monkeypatch):
    class _UpdateSvc(_OkSvc):
        def execute(self, *_): return sample_order(status=OrderStatus.IN_PROGRESS)
    monkeypatch.setattr(oc, "UpdateOrderStatusService", lambda repo: _UpdateSvc())
    resp = client.patch("/orders/1/status", params={"status": OrderStatus.IN_PROGRESS.value})
    assert resp.status_code == 200
    assert resp.json()["status"] == OrderStatus.IN_PROGRESS.value


def test_update_status_error(monkeypatch):
    monkeypatch.setattr(oc, "UpdateOrderStatusService", lambda repo: _ErrSvc())
    resp = client.patch("/orders/1/status", params={"status": OrderStatus.IN_PROGRESS.value})
    assert resp.status_code == 400 and resp.json()["detail"] == "boom"
