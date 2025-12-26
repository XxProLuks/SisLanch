"""
LANCH - Produto Model
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Produto(Base):
    __tablename__ = "produtos"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    preco = Column(Numeric(10, 2), nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    controlar_estoque = Column(Boolean, default=False)
    estoque_atual = Column(Integer, default=0)
    estoque_minimo = Column(Integer, default=0)
    estoque_maximo = Column(Integer, default=0)
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    categoria = relationship("Categoria", back_populates="produtos")
    movimentacoes = relationship("StockMovement", back_populates="produto")
    
    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "categoria_id": self.categoria_id,
            "categoria_nome": self.categoria.nome if self.categoria else None,
            "preco": float(self.preco),
            "ativo": self.ativo,
            "controlar_estoque": self.controlar_estoque,
            "estoque_atual": self.estoque_atual
        }
