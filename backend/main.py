"""
LANCH - Sistema de Lanchonete Hospitalar
Main Application Entry Point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import os
from pathlib import Path

from config import settings
from database import init_db
from routers import (
    auth_router, produtos_router, funcionarios_router,
    pedidos_router, competencias_router, relatorios_router,
    admin_router, audit_router, estoque_router, caixa_router,
    setores_router, print_router
)
from middleware import limiter, RateLimitMiddleware
from middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from utils.logger import setup_logging, get_logger
from utils.env_validator import validate_environment

# Setup logging
logger = setup_logging(
    log_dir=settings.LOG_DIR,
    log_level=settings.LOG_LEVEL,
    max_bytes=settings.LOG_MAX_BYTES,
    backup_count=settings.LOG_BACKUP_COUNT
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and validate configuration on startup"""
    print("=" * 60)
    print("🚀 Iniciando LANCH - Sistema de Lanchonete Hospitalar")
    print("=" * 60)
    
    # Validate environment configuration
    print("🔍 Validando configuração...")
    if not validate_environment():
        print("\n❌ Falha na validação do ambiente. Corrija os erros acima.")
        raise SystemExit(1)
    
    # Create required directories
    print("📁 Verificando diretórios necessários...")
    base_path = Path(__file__).parent.parent
    required_dirs = ['logs', 'exports', 'backups']
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✓ Criado: {dir_name}/")
    
    # Validate configuration
    print(f"📋 Versão: {settings.APP_VERSION}")
    print(f"🔧 Ambiente: {'PRODUÇÃO' if settings.is_production else 'DESENVOLVIMENTO'}")
    print(f"🔒 CORS Origens: {', '.join(settings.cors_origins)}")
    
    # Security warnings
    if settings.DEBUG:
        print("⚠️  AVISO: Modo DEBUG está ATIVO - NÃO usar em produção!")
    
    if "localhost" in settings.ALLOWED_ORIGINS and settings.is_production:
        print("⚠️  AVISO: CORS permite localhost em produção!")
    
    # Initialize database
    print("💾 Inicializando banco de dados...")
    init_db()
    print("✅ Banco de dados inicializado")
    
    logger.info(
        "Application started",
        extra={"version": settings.APP_VERSION, "environment": "production" if settings.is_production else "development"}
    )
    
    print("=" * 60)
    print("✅ Aplicação iniciada com sucesso!")
    print("=" * 60)
    
    yield
    
    logger.info("Application shutting down")
    print("👋 Encerrando aplicação")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Sistema de gestão para lanchonete hospitalar com suporte a convênio de funcionários e vendas à vista.",
    lifespan=lifespan
)

# Add exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Add rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration - Using environment-configured origins
# Special handling for local files (null origin) in development
allowed_origins = settings.cors_origins.copy()

# In development mode, also allow all origins for easier testing
if settings.DEBUG:
    print("⚠️  DEBUG mode: CORS accepting all origins for development")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all in debug mode
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["Content-Type", "Authorization"],
    )
else:
    # Production: strict CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["Content-Type", "Authorization"],
    )

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(auth_router)
app.include_router(produtos_router)
app.include_router(funcionarios_router)
app.include_router(pedidos_router)
app.include_router(competencias_router)
app.include_router(relatorios_router)
app.include_router(admin_router)
app.include_router(audit_router)
app.include_router(estoque_router)
app.include_router(caixa_router)
app.include_router(setores_router)
app.include_router(print_router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check for monitoring"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
