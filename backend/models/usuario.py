"""
LANCH - Usuario Model
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from database import Base
import enum


class PerfilUsuario(str, enum.Enum):
    ADMIN = "ADMIN"
    ATENDENTE = "ATENDENTE"
    COZINHA = "COZINHA"


class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    nome = Column(String, nullable=False)
    perfil = Column(String, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "nome": self.nome,
            "perfil": self.perfil,
            "ativo": self.ativo,
            "criado_em": str(self.criado_em) if self.criado_em else None
        }
