from typing import Any, Dict

import pytest
import responses
from pytest_bdd import given, when, then, scenarios, parsers

from app.adapters.driven.gateways.product_catalog_gateway import (
    ProductCatalogGateway,
    CATALOG_BASE_URL,
)

scenarios("../features")
gateway = ProductCatalogGateway()


# ───────────── fixtures ─────────────
@pytest.fixture
def ctx():
    return {}


@pytest.fixture(autouse=True)
def mock_rs():
    with responses.RequestsMock() as rs:
        yield rs


# ───────────── helpers ─────────────
def _stub_get(rs: responses.RequestsMock, pid: str, body: Dict[str, Any], status: int):
    rs.add(
        responses.GET,
        f"{CATALOG_BASE_URL}/products/{pid}",
        json=body,
        status=status,
    )

def _stub_reserve(rs, pid: str, qty: int, status: int):
    url = f"{CATALOG_BASE_URL}/products/{pid}/reserve"
    if status == 204:
        # 204 não deve conter body
        rs.add(responses.POST, url, status=204)
    else:
        rs.add(responses.POST, url, json={"error": "no stock"}, status=status)


# ───────────── GIVEN ─────────────
@given(parsers.parse('um produto "{pid}" existe no catálogo'))
def _(pid, mock_rs):
    _stub_get(mock_rs, pid, {"id": pid, "name": "Banana"}, 200)

@given(parsers.parse('nenhum produto "{pid}" existe no catálogo'))
def _(pid, mock_rs):
    _stub_get(mock_rs, pid, {"detail": "not found"}, 404)

@given(parsers.parse('o produto "{pid}" possui estoque'))
def _(pid, mock_rs):
    _stub_reserve(mock_rs, pid, qty=2, status=204)

@given(parsers.parse('o produto "{pid}" não possui estoque suficiente'))
def _(pid, mock_rs):
    _stub_reserve(mock_rs, pid, qty=5, status=409)


# ───────────── WHEN ─────────────
@when(parsers.parse('eu chamar get_product com "{pid}"'))
def _(pid, ctx):
    try:
        ctx["result"] = gateway.get_product(pid)
    except Exception as exc:
        ctx["error"] = exc

@when(parsers.parse('eu reservar {qty:d} unidades de "{pid}"'))
def _(pid, qty: int, ctx):
    try:
        gateway.reserve_stock(pid, qty)
    except Exception as exc:
        ctx["error"] = exc


# ───────────── THEN ─────────────
@then("devo receber os dados do produto")
def _(ctx):
    assert ctx["result"]["name"] == "Banana"

@then(parsers.parse('deve lançar erro "{msg}"'))
def _(msg, ctx):
    err = ctx.get("error")
    assert isinstance(err, ValueError)
    assert str(err) == msg

@then("a reserva deve acontecer sem erros")
def _(ctx):
    assert "error" not in ctx
