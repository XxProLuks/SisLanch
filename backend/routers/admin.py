"""
LANCH - Admin Router
"""

import shutil
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from models import Usuario
from schemas import UsuarioCreate, UsuarioResponse
from routers.auth import require_admin
from utils.security import get_password_hash
from utils.logger import get_logger
from config import settings

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = get_logger(__name__)


@router.post("/usuarios", response_model=UsuarioResponse, dependencies=[Depends(require_admin)])
async def criar_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db)
):
    """
    Criar novo usuário do sistema (Admin, Atendente ou Cozinha)
    Requer permissão de administrador
    """
    # Verificar se username já existe
    existing_user = db.query(Usuario).filter(Usuario.username == usuario.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de usuário já existe"
        )
    
    # Validar perfil
    valid_perfis = ["ADMIN", "ATENDENTE", "COZINHA"]
    if usuario.perfil not in valid_perfis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Perfil inválido. Deve ser um de: {', '.join(valid_perfis)}"
        )
    
    # Criar novo usuário
    novo_usuario = Usuario(
        username=usuario.username,
        password_hash=get_password_hash(usuario.password),
        nome=usuario.nome,
        perfil=usuario.perfil,
        ativo=True
    )
    
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    
    logger.info(f"Novo usuário criado: {usuario.username} ({usuario.perfil})")
    
    return novo_usuario


@router.post("/backup", dependencies=[Depends(require_admin)])
async def backup_database():
    """Create a backup of the SQLite database"""
    # Source database path
    # settings.DATABASE_URL is like "sqlite:///../database/lanch.db"
    # We need to resolve the actual path.
    # Assuming standard structure: c:\Lanch\database\lanch.db
    
    # We can rely on relative path from config or absolute path convention
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "lanch.db")
    
    if not os.path.exists(db_path):
        # Callback to relative path if absolute failed
        db_path = "../database/lanch.db"
        if not os.path.exists(db_path):
             raise HTTPException(status_code=500, detail="Database file not found")

    backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"lanch_backup_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        shutil.copy2(db_path, backup_path)
        return {"message": "Backup created successfully", "filename": backup_filename, "path": backup_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

