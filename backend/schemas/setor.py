"""
LANCH - Setor (Department) Schemas
Pydantic schemas for department/cost center management
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class SetorBase(BaseModel):
    """Base schema for sectors"""
    nome: str = Field(..., min_length=2, max_length=100, description="Department name")
    codigo: Optional[str] = Field(None, max_length=20, description="Cost center code")
    centro_custo: Optional[str] = Field(None, max_length=50, description="Cost center")
    limite_mensal: Optional[float] = Field(None, ge=0, description="Monthly limit for sector")
    limite_por_funcionario: Optional[float] = Field(None, ge=0, description="Default limit per employee")
    responsavel: Optional[str] = Field(None, max_length=100, description="Responsible person")
    email_responsavel: Optional[str] = Field(None, max_length=100, description="Responsible email")
    descricao: Optional[str] = Field(None, max_length=500)


class SetorCreate(SetorBase):
    """Schema for creating a sector"""
    pass


class SetorUpdate(BaseModel):
    """Schema for updating a sector"""
    nome: Optional[str] = Field(None, min_length=2, max_length=100)
    codigo: Optional[str] = Field(None, max_length=20)
    centro_custo: Optional[str] = Field(None, max_length=50)
    limite_mensal: Optional[float] = Field(None, ge=0)
    limite_por_funcionario: Optional[float] = Field(None, ge=0)
    responsavel: Optional[str] = Field(None, max_length=100)
    email_responsavel: Optional[str] = Field(None, max_length=100)
    descricao: Optional[str] = Field(None, max_length=500)
    ativo: Optional[bool] = None


class SetorResponse(SetorBase):
    """Schema for sector response"""
    id: int
    ativo: bool
    criado_em: datetime
    atualizado_em: Optional[datetime]
    total_funcionarios: Optional[int] = 0
    consumo_atual: Optional[float] = 0
    
    class Config:
        from_attributes = True


class SetorResumo(BaseModel):
    """Sector summary with consumption data"""
    id: int
    nome: str
    codigo: Optional[str]
    centro_custo: Optional[str]
    limite_mensal: Optional[float]
    total_funcionarios: int
    consumo_mes_atual: float
    percentual_consumido: float
    saldo_disponivel: Optional[float]


class ConsumoSetorReport(BaseModel):
    """Consumption report by sector"""
    setor_id: int
    setor_nome: str
    centro_custo: Optional[str]
    limite_mensal: Optional[float]
    total_funcionarios: int
    consumo_total: float
    consumo_medio_funcionario: float
    funcionarios: List[dict]
