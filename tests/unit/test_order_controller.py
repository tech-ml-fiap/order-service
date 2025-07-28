from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.security import HTTPAuthorizationCredentials

import app.adapters.driver.controllers.order_controller as oc
from app.shared.enums.order_status import OrderStatus
from app.domain.entities.order import Order
from app.domain.entities.item import OrderItem

def _order(
    order_id: int = 1,
    status: OrderStatus = OrderStatus.RECEIVED,
    client_id: int | None = 10,
) -> Order:
    return Order(
        id=order_id,
        client_id=client_id,
        status=status,
        amount=20.0,
        items=[OrderItem(id=99, product_id="SKU", name="Burger", quantity=2, price=10)],
    )


class _OK:
    def __init__(self, *_, **__): ...
    def execute(self, *_, **__):
        return _order(), "QR-CODE"

    def verify_token(self, *_):
        return 10
    def create_payment(self, *_):
        return "QR-CODE", None


class _ERR(_OK):
    """Fake service que levanta falha de domínio."""
    def execute(self, *_, **__):
        raise ValueError("boom")


class _NONE(_OK):
    """Fake service que devolve None (not-found)."""
    def execute(self, *_, **__):
        return None


app = FastAPI()
app.include_router(oc.router)

app = FastAPI()
app.include_router(oc.router)


app.dependency_overrides[oc.get_db_session] = lambda: None

class _FakeSecurity:
    async def __call__(self, *_, **__):

        return None


oc.security = _FakeSecurity()

client = TestClient(app)


def _fake_security(auth: str | None = None):
    if auth:
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=auth)
    return None

oc.security.__call__ = lambda *_, **__: _fake_security(None)



def test_create_order_ok(monkeypatch):
    monkeypatch.setattr(oc, "CreateOrderService", lambda *_: _OK())
    monkeypatch.setattr(oc, "PaymentGatewayHttp", lambda *_: _OK())
    monkeypatch.setattr(oc, "CustomerAuthHttp", lambda *_: _OK())

    resp = client.post("/orders", json={"items": [{"product_id": "P", "quantity": 1}]})
    assert resp.status_code == 201
    assert resp.json()["qr_code"] == "QR-CODE"
    assert resp.json()["items"][0]["name"] == "Burger"


def test_create_order_error(monkeypatch):
    monkeypatch.setattr(oc, "CreateOrderService", lambda *_: _ERR())
    resp = client.post("/orders", json={"items": [{"product_id": "P", "quantity": 1}]})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "boom"


def test_list_orders(monkeypatch):
    class _List(_OK):
        def execute(self, status=None, prioritized=False):
            assert status in (None, OrderStatus.READY)
            return [_order(status=status or OrderStatus.RECEIVED)]

    monkeypatch.setattr(oc, "ListOrdersService", lambda repo: _List())


    assert client.get("/orders").status_code == 200

    assert (
        client.get("/orders", params={"status": OrderStatus.READY.value}).status_code
        == 200
    )

    monkeypatch.setattr(oc, "ListOrdersService", lambda repo: _List())
    assert client.get("/orders/active").status_code == 200

# ------------------------------------------------------------------ stubs

class _OKGet:
    """Imita Get/List services que devolvem Order(s) apenas."""
    def __init__(self, *_, **__): ...
    def execute(self, *_, **__):
        return _order()


def test_get_order_found(monkeypatch):
    monkeypatch.setattr(oc, "GetOrderByIdService", lambda repo: _OKGet())
    resp = client.get("/orders/1")
    assert resp.status_code == 200 and resp.json()["id"] == 1


def test_get_order_not_found(monkeypatch):
    monkeypatch.setattr(oc, "GetOrderByIdService", lambda repo: _NONE())
    assert client.get("/orders/999").status_code == 404


def test_update_status_ok(monkeypatch):
    class _Update(_OK):
        def execute(self, *_):
            return _order(status=OrderStatus.IN_PROGRESS)

    monkeypatch.setattr(oc, "UpdateOrderStatusService", lambda repo, pay: _Update())
    resp = client.patch(
        "/orders/1/status", params={"status": OrderStatus.IN_PROGRESS.value}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == OrderStatus.IN_PROGRESS.value


def test_update_status_error(monkeypatch):
    monkeypatch.setattr(oc, "UpdateOrderStatusService", lambda repo, pay: _ERR())
    resp = client.patch(
        "/orders/1/status", params={"status": OrderStatus.IN_PROGRESS.value}
    )
    assert resp.status_code == 400 and resp.json()["detail"] == "boom"
