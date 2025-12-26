"""
LANCH - Setor (Department/Cost Center) Model
Organizational structure for employee grouping and consumption tracking
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Setor(Base):
    """Department/Cost Center model"""
    __tablename__ = "setores"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, unique=True)
    codigo = Column(String(20), nullable=True, unique=True)  # Cost center code
    centro_custo = Column(String(50), nullable=True)
    
    # Limits
    limite_mensal = Column(Numeric(10, 2), nullable=True)  # Monthly limit for entire sector
    limite_por_funcionario = Column(Numeric(10, 2), nullable=True)  # Default limit per employee
    
    # Details
    responsavel = Column(String(100), nullable=True)  # Responsible person
    email_responsavel = Column(String(100), nullable=True)
    descricao = Column(Text, nullable=True)
    
    # Status
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    funcionarios = relationship("Funcionario", back_populates="setor")
    
    def __repr__(self):
        return f"<Setor {self.nome} ({self.centro_custo})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "codigo": self.codigo,
            "centro_custo": self.centro_custo,
            "limite_mensal": float(self.limite_mensal) if self.limite_mensal else None,
            "limite_por_funcionario": float(self.limite_por_funcionario) if self.limite_por_funcionario else None,
            "responsavel": self.responsavel,
            "email_responsavel": self.email_responsavel,
            "descricao": self.descricao,
            "ativo": self.ativo
        }
