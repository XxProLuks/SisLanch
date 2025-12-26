"""
LANCH - Database connection and session management
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings
import os

# Ensure database directory exists
os.makedirs(os.path.dirname(settings.DATABASE_URL.replace("sqlite:///", "")), exist_ok=True)

# Create engine with SQLite optimizations
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=settings.DEBUG
)

# Enable foreign keys for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize the database with schema"""
    from models import usuario, categoria, produto, funcionario, competencia, pedido, audit
    
    Base.metadata.create_all(bind=engine)
    
    # Create initial data
    db = SessionLocal()
    try:
        _create_initial_data(db)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error creating initial data: {e}")
    finally:
        db.close()


def _create_initial_data(db):
    """Create initial data if not exists"""
    from models.usuario import Usuario
    from models.categoria import Categoria
    from models.competencia import Competencia
    from utils.security import get_password_hash
    from datetime import datetime
    
    # Check if admin exists
    admin = db.query(Usuario).filter(Usuario.username == "admin").first()
    if not admin:
        admin = Usuario(
            username="admin",
            password_hash=get_password_hash("admin123"),
            nome="Administrador",
            perfil="ADMIN",
            ativo=True
        )
        db.add(admin)
    
    # Create default categories
    default_categories = ["Lanches", "Bebidas", "Salgados", "Doces", "Refeições"]
    for cat_name in default_categories:
        cat = db.query(Categoria).filter(Categoria.nome == cat_name).first()
        if not cat:
            db.add(Categoria(nome=cat_name, ativo=True))
    
    # Create current competency
    now = datetime.now()
    comp = db.query(Competencia).filter(
        Competencia.ano == now.year,
        Competencia.mes == now.month
    ).first()
    if not comp:
        db.add(Competencia(ano=now.year, mes=now.month, status="ABERTA"))
