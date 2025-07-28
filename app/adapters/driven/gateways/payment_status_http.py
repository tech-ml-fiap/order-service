import httpx
from typing import Optional, Tuple

from app.domain.ports.payment_status_port import PaymentGatewayPort
from app.shared.enums.payment_status import PaymentStatus


class PaymentGatewayHttp(PaymentGatewayPort):
    def __init__(self, base_url: str, client: Optional[httpx.Client] = None):
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(timeout=5)

    def get_status(self, order_id: int) -> PaymentStatus:  # noqa: D401
        resp = self.client.get(f"{self.base_url}/api/payment/{order_id}")
        resp.raise_for_status()
        data = resp.json()
        return PaymentStatus(data["status"])

    def create_payment(self, order_id: int, amount: float) -> Tuple[str, PaymentStatus]:
        resp = self.client.post(
            f"{self.base_url}/api/payment",
            json={"order_id": order_id, "amount": amount},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["qr_data"], PaymentStatus.PENDING
