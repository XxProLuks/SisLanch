"""
LANCH - Stock Movement Model
Tracks all stock entries, exits, and adjustments
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database import Base


class MovementType(str, enum.Enum):
    """Types of stock movements"""
    ENTRADA = "ENTRADA"      # Stock entry (purchase, delivery)
    SAIDA = "SAIDA"          # Manual exit (waste, loss)
    AJUSTE = "AJUSTE"        # Inventory adjustment
    VENDA = "VENDA"          # Sale (automatic on order)


class StockMovement(Base):
    """Stock movement tracking model"""
    __tablename__ = "movimentacoes_estoque"
    
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    tipo = Column(String(20), nullable=False)  # ENTRADA, SAIDA, AJUSTE, VENDA
    quantidade = Column(Integer, nullable=False)
    quantidade_anterior = Column(Integer, default=0)
    quantidade_nova = Column(Integer, default=0)
    motivo = Column(Text, nullable=True)
    referencia = Column(String(100), nullable=True)  # e.g., order_id, invoice number
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    produto = relationship("Produto", back_populates="movimentacoes")
    usuario = relationship("Usuario")
    
    def __repr__(self):
        return f"<StockMovement {self.tipo} {self.quantidade} of product {self.produto_id}>"
