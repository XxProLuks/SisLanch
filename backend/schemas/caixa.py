"""
LANCH - Financial Schemas
Pydantic schemas for cash register management
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class CaixaStatus(str, Enum):
    ABERTO = "ABERTO"
    FECHADO = "FECHADO"


class TransactionType(str, Enum):
    VENDA = "VENDA"
    SANGRIA = "SANGRIA"
    SUPRIMENTO = "SUPRIMENTO"
    TROCO = "TROCO"


class PaymentMethod(str, Enum):
    DINHEIRO = "DINHEIRO"
    CARTAO = "CARTAO"
    PIX = "PIX"
    CONVENIO = "CONVENIO"


# ==================== Caixa Schemas ====================

class CaixaOpen(BaseModel):
    """Schema for opening cash register"""
    valor_abertura: float = Field(..., ge=0, description="Opening cash amount")


class CaixaClose(BaseModel):
    """Schema for closing cash register"""
    valor_fechamento: float = Field(..., ge=0, description="Actual closing amount")
    observacoes: Optional[str] = Field(None, max_length=500)


class CaixaResponse(BaseModel):
    """Schema for cash register response"""
    id: int
    data: date
    status: str
    valor_abertura: float
    valor_fechamento: Optional[float]
    valor_esperado: Optional[float]
    diferenca: Optional[float]
    usuario_abertura_id: Optional[int]
    usuario_abertura_nome: Optional[str] = None
    usuario_fechamento_id: Optional[int]
    usuario_fechamento_nome: Optional[str] = None
    aberto_em: Optional[datetime]
    fechado_em: Optional[datetime]
    observacoes: Optional[str]
    total_vendas: Optional[float] = 0
    total_dinheiro: Optional[float] = 0
    total_cartao: Optional[float] = 0
    total_pix: Optional[float] = 0
    total_convenio: Optional[float] = 0
    
    class Config:
        from_attributes = True


# ==================== Transaction Schemas ====================

class TransacaoCreate(BaseModel):
    """Schema for creating a transaction"""
    tipo: TransactionType
    valor: float = Field(..., gt=0)
    descricao: Optional[str] = Field(None, max_length=200)


class SangriaCreate(BaseModel):
    """Schema for cash withdrawal (sangria)"""
    valor: float = Field(..., gt=0, description="Withdrawal amount")
    motivo: str = Field(..., min_length=3, max_length=200, description="Reason for withdrawal")


class SuprimentoCreate(BaseModel):
    """Schema for cash addition (suprimento)"""
    valor: float = Field(..., gt=0, description="Addition amount")
    descricao: Optional[str] = Field(None, max_length=200)


class TransacaoResponse(BaseModel):
    """Schema for transaction response"""
    id: int
    caixa_id: int
    tipo: str
    valor: float
    forma_pagamento: Optional[str]
    pedido_id: Optional[int]
    pedido_numero: Optional[str] = None
    descricao: Optional[str]
    usuario_id: Optional[int]
    usuario_nome: Optional[str] = None
    criado_em: datetime
    
    class Config:
        from_attributes = True


# ==================== Report Schemas ====================

class CaixaResumo(BaseModel):
    """Summary of cash register for closing"""
    caixa_id: int
    data: date
    status: str
    valor_abertura: float
    total_vendas: float
    total_sangrias: float
    total_suprimentos: float
    valor_esperado: float
    transacoes_count: int
    
    # By payment method
    vendas_dinheiro: float
    vendas_cartao: float
    vendas_pix: float
    vendas_convenio: float


class RelatorioFinanceiro(BaseModel):
    """Financial report for a period"""
    data_inicio: date
    data_fim: date
    total_vendas: float
    total_pedidos: int
    ticket_medio: float
    vendas_por_dia: List[dict]
    vendas_por_pagamento: dict
