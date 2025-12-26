"""
LANCH - Pydantic Schemas for Products
"""

from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


class CategoriaBase(BaseModel):
    nome: str


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaResponse(CategoriaBase):
    id: int
    ativo: bool
    
    class Config:
        from_attributes = True


class ProdutoBase(BaseModel):
    nome: str
    categoria_id: int
    preco: float
    controlar_estoque: bool = False
    estoque_atual: int = 0


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoUpdate(BaseModel):
    nome: Optional[str] = None
    categoria_id: Optional[int] = None
    preco: Optional[float] = None
    ativo: Optional[bool] = None
    controlar_estoque: Optional[bool] = None
    estoque_atual: Optional[int] = None


class ProdutoResponse(ProdutoBase):
    id: int
    categoria_nome: Optional[str] = None
    ativo: bool
    controlar_estoque: bool
    estoque_atual: int
    
    class Config:
        from_attributes = True
