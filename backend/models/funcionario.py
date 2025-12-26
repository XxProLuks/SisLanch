"""
LANCH - Funcionario Model
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Funcionario(Base):
    __tablename__ = "funcionarios"
    
    id = Column(Integer, primary_key=True, index=True)
    matricula = Column(String, unique=True, nullable=False, index=True)
    cpf = Column(String, unique=True, nullable=False, index=True)
    nome = Column(String, nullable=False)
    
    # Legacy fields (kept for backward compatibility)
    setor_nome = Column("setor", String, nullable=True)  # Renamed to setor_nome
    centro_custo = Column(String, nullable=True)
    
    # New sector relationship
    setor_id = Column(Integer, ForeignKey("setores.id"), nullable=True)
    
    limite_mensal = Column(Numeric(10, 2), nullable=False, default=500.00)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    setor = relationship("Setor", back_populates="funcionarios")
    consumos = relationship("ConsumoMensal", back_populates="funcionario")
    pedidos = relationship("Pedido", back_populates="funcionario")
    
    def to_dict(self):
        return {
            "id": self.id,
            "matricula": self.matricula,
            "cpf": self.cpf,
            "nome": self.nome,
            "setor": self.setor.nome if self.setor else self.setor_nome,
            "setor_id": self.setor_id,
            "centro_custo": self.setor.centro_custo if self.setor else self.centro_custo,
            "limite_mensal": float(self.limite_mensal),
            "ativo": self.ativo,
            "criado_em": str(self.criado_em) if self.criado_em else None
        }

