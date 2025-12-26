"""
LANCH - Pedido Model
"""

from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class TipoCliente(str, enum.Enum):
    FUNCIONARIO = "FUNCIONARIO"
    PACIENTE = "PACIENTE"


class StatusPedido(str, enum.Enum):
    PENDENTE = "PENDENTE"
    PREPARANDO = "PREPARANDO"
    PRONTO = "PRONTO"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"


class FormaPagamento(str, enum.Enum):
    CONVENIO = "CONVENIO"
    PIX = "PIX"
    CARTAO = "CARTAO"
    DINHEIRO = "DINHEIRO"


class Pedido(Base):
    __tablename__ = "pedidos"
    
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String, unique=True, nullable=False, index=True)
    tipo_cliente = Column(String, nullable=False)
    funcionario_id = Column(Integer, ForeignKey("funcionarios.id"), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    valor_total = Column(Numeric(10, 2), nullable=False, default=0)
    status = Column(String, nullable=False, default="PENDENTE")
    forma_pagamento = Column(String, nullable=False)
    competencia_id = Column(Integer, ForeignKey("competencias.id"), nullable=True)
    observacao = Column(Text, nullable=True)
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    funcionario = relationship("Funcionario", back_populates="pedidos")
    usuario = relationship("Usuario")
    competencia = relationship("Competencia", back_populates="pedidos")
    itens = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "numero": self.numero,
            "tipo_cliente": self.tipo_cliente,
            "funcionario_id": self.funcionario_id,
            "funcionario_nome": self.funcionario.nome if self.funcionario else None,
            "funcionario_matricula": self.funcionario.matricula if self.funcionario else None,
            "valor_total": float(self.valor_total),
            "status": self.status,
            "forma_pagamento": self.forma_pagamento,
            "observacao": self.observacao,
            "criado_em": str(self.criado_em) if self.criado_em else None,
            "itens": [item.to_dict() for item in self.itens] if self.itens else []
        }


class ItemPedido(Base):
    __tablename__ = "itens_pedido"
    
    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id", ondelete="CASCADE"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    
    # Relationships
    pedido = relationship("Pedido", back_populates="itens")
    produto = relationship("Produto")
    
    def to_dict(self):
        return {
            "id": self.id,
            "produto_id": self.produto_id,
            "produto_nome": self.produto.nome if self.produto else None,
            "quantidade": self.quantidade,
            "preco_unitario": float(self.preco_unitario),
            "subtotal": float(self.subtotal)
        }
