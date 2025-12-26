"""
LANCH - Stock Schemas
Pydantic schemas for stock management
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MovementType(str, Enum):
    """Types of stock movements"""
    ENTRADA = "ENTRADA"
    SAIDA = "SAIDA"
    AJUSTE = "AJUSTE"
    VENDA = "VENDA"


class StockMovementCreate(BaseModel):
    """Schema for creating a stock movement"""
    produto_id: int = Field(..., gt=0, description="Product ID")
    tipo: MovementType = Field(..., description="Movement type")
    quantidade: int = Field(..., gt=0, description="Quantity to move")
    motivo: Optional[str] = Field(None, max_length=500, description="Reason for movement")
    referencia: Optional[str] = Field(None, max_length=100, description="Reference (invoice, order)")


class StockMovementResponse(BaseModel):
    """Schema for stock movement response"""
    id: int
    produto_id: int
    produto_nome: Optional[str] = None
    tipo: str
    quantidade: int
    quantidade_anterior: int
    quantidade_nova: int
    motivo: Optional[str]
    referencia: Optional[str]
    usuario_id: Optional[int]
    usuario_nome: Optional[str] = None
    criado_em: datetime
    
    class Config:
        from_attributes = True


class StockAdjustment(BaseModel):
    """Schema for adjusting inventory to a specific quantity"""
    produto_id: int = Field(..., gt=0)
    nova_quantidade: int = Field(..., ge=0, description="New stock quantity")
    motivo: str = Field(..., min_length=3, description="Reason for adjustment")


class StockAlert(BaseModel):
    """Schema for stock alerts"""
    produto_id: int
    produto_nome: str
    categoria_nome: Optional[str]
    estoque_atual: int
    estoque_minimo: int
    deficit: int
    status: str  # CRITICAL, LOW, OK


class StockSummary(BaseModel):
    """Schema for stock summary"""
    total_produtos: int
    produtos_abaixo_minimo: int
    produtos_zerados: int
    ultimas_movimentacoes: List[StockMovementResponse]
    alertas: List[StockAlert]
