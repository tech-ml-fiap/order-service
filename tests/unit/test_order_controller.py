from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.security import HTTPAuthorizationCredentials

import app.adapters.driver.controllers.order_controller as oc
from app.domain.entities.order import Order
from app.domain.entities.item import OrderItem
from app.shared.enums.order_status import OrderStatus

# ------------------------------------------------------------------ helpers
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


# ------------------------------------------------------------------ stubs de domínio
class _OKCreate:  # para CreateOrderService
    def __init__(self, *_, **__): ...
    def execute(self, *_, **__):
        return _order(), "QR-CODE"  # (Order, qr)


class _OKGet:  # para Get/List services
    def __init__(self, *_, **__): ...
    def execute(self, *_, **__):
        return _order()


class _OKUpdate:
    def __init__(self, *_, **__): ...
    def execute(self, *_, **__):
        return _order(status=OrderStatus.IN_PROGRESS)


class _Err:
    def __init__(self, *_, **__): ...
    def execute(self, *_, **__):
        raise ValueError("boom")


# ------------------------------------------------------------------ dummies de gateways (HTTP)
class _DummyPaymentGateway:
    def __init__(self, *_, **__): ...
    def create_payment(self, *_):        # usado em POST /orders
        return "QR-DUMMY", None
    def get_status(self, *_):            # usado em PATCH /orders/{id}/status
        from app.shared.enums.payment_status import PaymentStatus
        return PaymentStatus.PAID


class _DummyAuthGateway:
    def __init__(self, *_, **__): ...
    def verify_token(self, *_):          # nunca falha nos testes
        return 42


# ------------------------------------------------------------------ wiring do FastAPI
app = FastAPI()
app.include_router(oc.router)

# ignora acesso ao banco
app.dependency_overrides[oc.get_db_session] = lambda: None

# stub global do bearer (sem token)
class _FakeSecurity:
    async def __call__(self, *_, **__):
        return None  # ou HTTPAuthorizationCredentials("Bearer", "fake")

oc.security = _FakeSecurity()

# gateways HTTP padrão para qualquer rota que não seja monkey-patched
oc.PaymentGatewayHttp = _DummyPaymentGateway
oc.CustomerAuthHttp = _DummyAuthGateway

client = TestClient(app)


# ------------------------------------------------------------------ testes
def test_create_order_ok(monkeypatch):
    monkeypatch.setattr(oc, "CreateOrderService", lambda *_: _OKCreate())
    resp = client.post("/orders", json={"items": [{"product_id": "P", "quantity": 1}]})
    assert resp.status_code == 201
    body = resp.json()
    assert body["qr_code"] == "QR-CODE"
    assert body["items"][0]["name"] == "Burger"


def test_create_order_error(monkeypatch):
    monkeypatch.setattr(oc, "CreateOrderService", lambda *_: _Err())
    resp = client.post("/orders", json={"items": [{"product_id": "P", "quantity": 1}]})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "boom"


def test_list_orders(monkeypatch):
    class _List(_OKGet):
        def execute(self, status=None, prioritized=False):
            assert status in (None, OrderStatus.READY)
            return [_order(status=status or OrderStatus.RECEIVED)]

    monkeypatch.setattr(oc, "ListOrdersService", lambda repo: _List())

    # todos
    assert client.get("/orders").status_code == 200
    # filtrado
    assert (
        client.get("/orders", params={"status": OrderStatus.READY.value}).status_code
        == 200
    )
    # ativos ordenados
    assert client.get("/orders/active").status_code == 200


def test_get_order_found(monkeypatch):
    monkeypatch.setattr(oc, "GetOrderByIdService", lambda repo: _OKGet())
    resp = client.get("/orders/1")
    assert resp.status_code == 200 and resp.json()["id"] == 1


def test_get_order_not_found(monkeypatch):
    class _NoneSvc:
        def __init__(self, *_, **__): ...
        def execute(self, *_, **__): return None

    monkeypatch.setattr(oc, "GetOrderByIdService", lambda repo: _NoneSvc())
    assert client.get("/orders/999").status_code == 404


def test_update_status_ok(monkeypatch):
    monkeypatch.setattr(oc, "UpdateOrderStatusService", lambda repo, pay: _OKUpdate())
    resp = client.patch(
        "/orders/1/status", params={"status": OrderStatus.IN_PROGRESS.value}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == OrderStatus.IN_PROGRESS.value


def test_update_status_error(monkeypatch):
    monkeypatch.setattr(oc, "UpdateOrderStatusService", lambda repo, pay: _Err())
    resp = client.patch(
        "/orders/1/status", params={"status": OrderStatus.IN_PROGRESS.value}
    )
    assert resp.status_code == 400 and resp.json()["detail"] == "boom"
