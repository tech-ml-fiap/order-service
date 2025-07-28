from abc import ABC, abstractmethod

class CustomerAuthPort(ABC):
    @abstractmethod
    def verify_token(self, token: str) -> int:
        """Retorna o ID do cliente se válido. Lança ValueError se inválido."""