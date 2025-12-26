"""
LANCH - Audit logging utilities
"""

from sqlalchemy.orm import Session
from typing import Optional, Any
import json


def log_action(
    db: Session,
    usuario_id: Optional[int],
    acao: str,
    tabela: str,
    registro_id: Optional[int] = None,
    dados_anteriores: Optional[Any] = None,
    dados_novos: Optional[Any] = None,
    ip: Optional[str] = None
):
    """Log an action to the audit table"""
    from models.audit import AuditLog
    
    log_entry = AuditLog(
        usuario_id=usuario_id,
        acao=acao,
        tabela=tabela,
        registro_id=registro_id,
        dados_anteriores=json.dumps(dados_anteriores, default=str) if dados_anteriores else None,
        dados_novos=json.dumps(dados_novos, default=str) if dados_novos else None,
        ip=ip
    )
    db.add(log_entry)
