import os
import requests
from typing import Dict

from dotenv import load_dotenv

load_dotenv()
CATALOG_BASE_URL = os.getenv("CATALOG_URL", "http://catalog-api:8000")


class ProductCatalogGateway:
    def get_product(self, product_id: str) -> Dict:
        resp = requests.get(f"{CATALOG_BASE_URL}/products/{product_id}", timeout=5)
        if resp.status_code == 404:
            raise ValueError(f"Produto {product_id} não encontrado")
        resp.raise_for_status()
        return resp.json()

    def reserve_stock(self, product_id: str, qty: int) -> None:
        resp = requests.post(
            f"{CATALOG_BASE_URL}/products/{product_id}/reserve",
            json={"qty": qty},
            timeout=5,
        )
        if resp.status_code == 409:
            raise ValueError(f"Estoque insuficiente para {product_id}")
        resp.raise_for_status()
