"""
LANCH - Authentication Router
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import re

from database import get_db
from models import Usuario
from schemas import Token, LoginRequest, UsuarioResponse, TokenData, ChangePasswordRequest
from utils.security import verify_password, create_access_token, decode_access_token, get_password_hash
from utils.logger import get_logger
from config import settings
from middleware import limiter

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Autenticação"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Default admin password hash for detection
DEFAULT_ADMIN_PASSWORD = "admin123"


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    """Get current authenticated user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    user = db.query(Usuario).filter(Usuario.username == username).first()
    if user is None:
        raise credentials_exception
    
    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário desativado"
        )
    
    return user


def require_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Require admin role"""
    if current_user.perfil != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores"
        )
    return current_user


def require_atendente(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Require atendente or admin role"""
    if current_user.perfil not in ["ADMIN", "ATENDENTE"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a atendentes"
        )
    return current_user


@router.get("/me", response_model=UsuarioResponse)
async def get_current_user_info(current_user: Usuario = Depends(get_current_user)):
    """Get current authenticated user information"""
    return current_user


@router.post("/token", response_model=Token)
@limiter.limit(f"{settings.LOGIN_RATE_LIMIT}/minute")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 compatible token login with rate limiting"""
    logger.info(f"Login attempt for user: {form_data.username}")
    
    user = db.query(Usuario).filter(Usuario.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        logger.warning(f"Failed login attempt for user: {form_data.username}", extra={"username": form_data.username})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.ativo:
        logger.warning(f"Login attempt for inactive user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário desativado"
        )
    
    # Check for default password
    if user.username == "admin" and verify_password(DEFAULT_ADMIN_PASSWORD, user.password_hash):
        logger.warning("Admin login with default password detected!")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Senha padrão detectada! Por segurança, você deve alterar a senha do administrador antes de usar o sistema."
        )
    
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "perfil": user.perfil}
    )
    
    logger.info(f"Successful login for user: {user.username}", extra={"user_id": user.id})
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
@limiter.limit(f"{settings.LOGIN_RATE_LIMIT}/minute")
async def login(
    request: Request,
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """Simple login endpoint with rate limiting"""
    logger.info(f"Login attempt for user: {credentials.username}")
    
    user = db.query(Usuario).filter(Usuario.username == credentials.username).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        logger.warning(f"Failed login attempt for user: {credentials.username}", extra={"username": credentials.username})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos"
        )
    
    if not user.ativo:
        logger.warning(f"Login attempt for inactive user: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário desativado"
        )
    
    # Check for default password
    if user.username == "admin" and verify_password(DEFAULT_ADMIN_PASSWORD, user.password_hash):
        logger.warning("Admin login with default password detected!")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Senha padrão detectada! Por segurança, você deve alterar a senha do administrador antes de usar o sistema."
        )
    
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "perfil": user.perfil}
    )
    
    logger.info(f"Successful login for user: {user.username}", extra={"user_id": user.id})
    
    return {"access_token": access_token, "token_type": "bearer"}


def validate_password_strength(password: str) -> bool:
    """
    Validate password strength
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha deve ter no mínimo 8 caracteres"
        )
    
    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha deve conter pelo menos uma letra maiúscula"
        )
    
    if not re.search(r"[a-z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha deve conter pelo menos uma letra minúscula"
        )
    
    if not re.search(r"\d", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha deve conter pelo menos um número"
        )
    
    return True


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Change current user password with strength validation"""
    if not verify_password(password_data.current_password, current_user.password_hash):
        logger.warning(f"Failed password change - incorrect current password for user {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )
    
    # Validate new password strength
    validate_password_strength(password_data.new_password)
    
    # Prevent using same password
    if verify_password(password_data.new_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A nova senha não pode ser igual à senha atual"
        )
    
    current_user.password_hash = get_password_hash(password_data.new_password)
    db.commit()
    
    logger.info(f"Password changed successfully for user {current_user.username}", extra={"user_id": current_user.id})
    
    return {"message": "Senha alterada com sucesso"}
