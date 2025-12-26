"""
LANCH - Cash Register Model (Caixa)
Financial control for daily cash management
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Date, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime, date
import enum

from database import Base


class CaixaStatus(str, enum.Enum):
    """Cash register status"""
    ABERTO = "ABERTO"
    FECHADO = "FECHADO"


class TransactionType(str, enum.Enum):
    """Types of cash transactions"""
    VENDA = "VENDA"           # Sale from order
    SANGRIA = "SANGRIA"       # Cash withdrawal
    SUPRIMENTO = "SUPRIMENTO" # Cash addition (change)
    TROCO = "TROCO"           # Initial change fund


class Caixa(Base):
    """Cash register model - one per day"""
    __tablename__ = "caixa"
    
    id = Column(Integer, primary_key=True, index=True)
    data = Column(Date, nullable=False, unique=True, index=True)
    
    # Opening
    valor_abertura = Column(Numeric(10, 2), default=0)
    usuario_abertura_id = Column(Integer, ForeignKey("usuarios.id"))
    aberto_em = Column(DateTime)
    
    # Closing
    valor_fechamento = Column(Numeric(10, 2), nullable=True)
    valor_esperado = Column(Numeric(10, 2), nullable=True)  # Calculated expected value
    diferenca = Column(Numeric(10, 2), nullable=True)       # Expected vs actual
    usuario_fechamento_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fechado_em = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(20), default=CaixaStatus.ABERTO.value)
    observacoes = Column(Text, nullable=True)
    
    # Relationships
    usuario_abertura = relationship("Usuario", foreign_keys=[usuario_abertura_id])
    usuario_fechamento = relationship("Usuario", foreign_keys=[usuario_fechamento_id])
    transacoes = relationship("TransacaoCaixa", back_populates="caixa")
    
    def __repr__(self):
        return f"<Caixa {self.data} - {self.status}>"


class TransacaoCaixa(Base):
    """Cash transaction model"""
    __tablename__ = "transacoes_caixa"
    
    id = Column(Integer, primary_key=True, index=True)
    caixa_id = Column(Integer, ForeignKey("caixa.id"), nullable=False)
    
    tipo = Column(String(20), nullable=False)  # VENDA, SANGRIA, SUPRIMENTO, TROCO
    valor = Column(Numeric(10, 2), nullable=False)
    forma_pagamento = Column(String(20), nullable=True)  # DINHEIRO, CARTAO, PIX, CONVENIO
    
    # Reference
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=True)
    descricao = Column(Text, nullable=True)
    
    # Audit
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    caixa = relationship("Caixa", back_populates="transacoes")
    pedido = relationship("Pedido")
    usuario = relationship("Usuario")
    
    def __repr__(self):
        return f"<TransacaoCaixa {self.tipo} R${self.valor}>"
