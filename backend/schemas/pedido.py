"""
LANCH - Pydantic Schemas for Orders
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ItemPedidoCreate(BaseModel):
    produto_id: int
    quantidade: int


class ItemPedidoResponse(BaseModel):
    id: int
    produto_id: int
    produto_nome: Optional[str] = None
    quantidade: int
    preco_unitario: float
    subtotal: float
    
    class Config:
        from_attributes = True


class PedidoCreate(BaseModel):
    tipo_cliente: str  # FUNCIONARIO or PACIENTE
    funcionario_id: Optional[int] = None
    matricula: Optional[str] = None  # Alternative to funcionario_id
    forma_pagamento: str
    observacao: Optional[str] = None
    itens: List[ItemPedidoCreate]


class PedidoUpdate(BaseModel):
    status: Optional[str] = None
    observacao: Optional[str] = None


class PedidoResponse(BaseModel):
    id: int
    numero: str
    tipo_cliente: str
    funcionario_id: Optional[int] = None
    funcionario_nome: Optional[str] = None
    funcionario_matricula: Optional[str] = None
    valor_total: float
    status: str
    forma_pagamento: str
    observacao: Optional[str] = None
    criado_em: Optional[datetime] = None
    itens: List[ItemPedidoResponse] = []
    
    class Config:
        from_attributes = True


class PedidoCozinha(BaseModel):
    """Simplified order for kitchen display"""
    id: int
    numero: str
    tipo_cliente: str
    cliente: str
    status: str
    observacao: Optional[str] = None
    criado_em: datetime
    itens: str  # Concatenated items string
    tempo_espera: int  # Minutes waiting
