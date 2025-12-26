"""
LANCH - Competencia Model
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class StatusCompetencia(str, enum.Enum):
    ABERTA = "ABERTA"
    FECHADA = "FECHADA"


class Competencia(Base):
    __tablename__ = "competencias"
    
    id = Column(Integer, primary_key=True, index=True)
    ano = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="ABERTA")
    fechada_em = Column(DateTime, nullable=True)
    fechada_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    criado_em = Column(DateTime, server_default=func.now())
    
    # Relationships
    consumos = relationship("ConsumoMensal", back_populates="competencia")
    pedidos = relationship("Pedido", back_populates="competencia")
    
    def to_dict(self):
        return {
            "id": self.id,
            "ano": self.ano,
            "mes": self.mes,
            "referencia": f"{self.mes:02d}/{self.ano}",
            "status": self.status,
            "fechada_em": str(self.fechada_em) if self.fechada_em else None
        }


class ConsumoMensal(Base):
    __tablename__ = "consumos_mensais"
    
    id = Column(Integer, primary_key=True, index=True)
    funcionario_id = Column(Integer, ForeignKey("funcionarios.id"), nullable=False)
    competencia_id = Column(Integer, ForeignKey("competencias.id"), nullable=False)
    valor_total = Column(Integer, nullable=False, default=0)
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    funcionario = relationship("Funcionario", back_populates="consumos")
    competencia = relationship("Competencia", back_populates="consumos")
    
    def to_dict(self):
        return {
            "id": self.id,
            "funcionario_id": self.funcionario_id,
            "funcionario_nome": self.funcionario.nome if self.funcionario else None,
            "competencia_id": self.competencia_id,
            "valor_total": float(self.valor_total) / 100,
            "referencia": self.competencia.to_dict()["referencia"] if self.competencia else None
        }
