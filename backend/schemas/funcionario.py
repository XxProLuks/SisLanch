"""
LANCH - Pydantic Schemas for Employees
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FuncionarioBase(BaseModel):
    matricula: str
    cpf: str
    nome: str
    setor: str
    centro_custo: str
    limite_mensal: float = 500.00


class FuncionarioCreate(FuncionarioBase):
    pass


class FuncionarioUpdate(BaseModel):
    nome: Optional[str] = None
    setor: Optional[str] = None
    centro_custo: Optional[str] = None
    limite_mensal: Optional[float] = None
    ativo: Optional[bool] = None


class FuncionarioResponse(FuncionarioBase):
    id: int
    ativo: bool
    criado_em: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FuncionarioConsumo(FuncionarioResponse):
    """Employee with current consumption info"""
    valor_consumido: float = 0.0
    saldo_disponivel: float = 0.0
