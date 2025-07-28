import os, httpx
from app.domain.ports.customer_auth_port import CustomerAuthPort

class CustomerAuthHttp(CustomerAuthPort):
    def __init__(self, base_url: str | None = None, client: httpx.Client | None = None):
        self.base_url = (base_url or os.getenv("CUSTOMER_SERVICE_URL")).rstrip("/")
        self.client = client or httpx.Client(timeout=5)

    def verify_token(self, token: str) -> int:
        resp = self.client.post(f"{self.base_url}/api/auth", json={"token": token})
        if resp.status_code == 200:
            data = resp.json()
            return data["id"]
        elif resp.status_code in (400, 401):
            raise ValueError("Token inválido")
        else:
            raise ValueError("Cliente não encontrado ou inativo")