"""
LANCH - Products Router
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Produto, Categoria, Usuario
from schemas import (
    ProdutoCreate, ProdutoUpdate, ProdutoResponse,
    CategoriaCreate, CategoriaResponse
)
from routers.auth import get_current_user, require_admin
from utils.audit import log_action

router = APIRouter(prefix="/produtos", tags=["Produtos"])


# ==================== CATEGORIAS ====================

@router.get("/categorias", response_model=List[CategoriaResponse])
async def listar_categorias(
    ativo: bool = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """List all categories"""
    query = db.query(Categoria)
    if ativo is not None:
        query = query.filter(Categoria.ativo == ativo)
    return query.order_by(Categoria.nome).all()


@router.post("/categorias", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
async def criar_categoria(
    categoria: CategoriaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Create a new category"""
    existing = db.query(Categoria).filter(Categoria.nome == categoria.nome).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Categoria já existe"
        )
    
    db_categoria = Categoria(**categoria.model_dump())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    
    log_action(db, current_user.id, "CRIAR", "categorias", db_categoria.id, None, db_categoria.to_dict())
    db.commit()
    
    return db_categoria


@router.put("/categorias/{categoria_id}", response_model=CategoriaResponse)
async def atualizar_categoria(
    categoria_id: int,
    ativo: bool,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Update category status"""
    categoria = db.query(Categoria).filter(Categoria.id == categoria_id).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    dados_anteriores = categoria.to_dict()
    categoria.ativo = ativo
    db.commit()
    
    log_action(db, current_user.id, "ATUALIZAR", "categorias", categoria.id, dados_anteriores, categoria.to_dict())
    db.commit()
    
    return categoria


# ==================== PRODUTOS ====================

@router.get("", response_model=List[ProdutoResponse])
async def listar_produtos(
    ativo: bool = None,
    categoria_id: int = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """List all products with optional filters"""
    query = db.query(Produto)
    
    if ativo is not None:
        query = query.filter(Produto.ativo == ativo)
    if categoria_id is not None:
        query = query.filter(Produto.categoria_id == categoria_id)
    
    produtos = query.order_by(Produto.nome).all()
    return [p.to_dict() for p in produtos]


@router.get("/{produto_id}", response_model=ProdutoResponse)
async def obter_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Get a single product by ID"""
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto.to_dict()


@router.post("", response_model=ProdutoResponse, status_code=status.HTTP_201_CREATED)
async def criar_produto(
    produto: ProdutoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Create a new product"""
    # Validate category exists
    categoria = db.query(Categoria).filter(Categoria.id == produto.categoria_id).first()
    if not categoria:
        raise HTTPException(status_code=400, detail="Categoria não encontrada")
    
    db_produto = Produto(**produto.model_dump())
    db.add(db_produto)
    db.commit()
    db.refresh(db_produto)
    
    log_action(db, current_user.id, "CRIAR", "produtos", db_produto.id, None, db_produto.to_dict())
    db.commit()
    
    return db_produto.to_dict()


@router.put("/{produto_id}", response_model=ProdutoResponse)
async def atualizar_produto(
    produto_id: int,
    produto: ProdutoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Update an existing product"""
    db_produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not db_produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    dados_anteriores = db_produto.to_dict()
    
    update_data = produto.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_produto, key, value)
    
    db.commit()
    db.refresh(db_produto)
    
    log_action(db, current_user.id, "ATUALIZAR", "produtos", db_produto.id, dados_anteriores, db_produto.to_dict())
    db.commit()
    
    return db_produto.to_dict()


@router.delete("/{produto_id}")
async def desativar_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Deactivate a product (soft delete)"""
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    dados_anteriores = produto.to_dict()
    produto.ativo = False
    db.commit()
    
    log_action(db, current_user.id, "DESATIVAR", "produtos", produto.id, dados_anteriores, produto.to_dict())
    db.commit()
    
    return {"message": "Produto desativado com sucesso"}
