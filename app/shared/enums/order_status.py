from enum import Enum as PyEnum

class OrderStatus(str, PyEnum):
    RECEIVED = "Recebido"
    IN_PROGRESS = "Em Preparação"
    READY = "Pronto"
    COMPLETED = "Finalizado"
    CANCELED = "Cancelado"