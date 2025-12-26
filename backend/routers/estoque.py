"""
LANCH - Stock Management Router
API endpoints for stock control
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_db
from models import Usuario, Produto
from models.estoque import StockMovement
from schemas.estoque import (
    StockMovementCreate, StockMovementResponse,
    StockAdjustment, StockAlert, StockSummary, MovementType
)
from routers.auth import require_admin, get_current_user
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/estoque", tags=["Estoque"])


@router.post("/entrada", response_model=StockMovementResponse)
async def registrar_entrada(
    movement: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Register stock entry (purchase, delivery)
    """
    # Validate product exists
    produto = db.query(Produto).filter(Produto.id == movement.produto_id).first()
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    # Create movement record
    quantidade_anterior = produto.estoque_atual
    quantidade_nova = quantidade_anterior + movement.quantidade
    
    stock_movement = StockMovement(
        produto_id=movement.produto_id,
        tipo=MovementType.ENTRADA.value,
        quantidade=movement.quantidade,
        quantidade_anterior=quantidade_anterior,
        quantidade_nova=quantidade_nova,
        motivo=movement.motivo,
        referencia=movement.referencia,
        usuario_id=current_user.id
    )
    
    # Update product stock
    produto.estoque_atual = quantidade_nova
    
    db.add(stock_movement)
    db.commit()
    db.refresh(stock_movement)
    
    logger.info(f"Stock entry: +{movement.quantidade} for product {produto.nome}", 
                extra={"user_id": current_user.id, "product_id": produto.id})
    
    return _format_movement_response(stock_movement, db)


@router.post("/saida", response_model=StockMovementResponse)
async def registrar_saida(
    movement: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Register manual stock exit (waste, loss, etc.)
    """
    produto = db.query(Produto).filter(Produto.id == movement.produto_id).first()
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    if produto.estoque_atual < movement.quantidade:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estoque insuficiente. Disponível: {produto.estoque_atual}"
        )
    
    quantidade_anterior = produto.estoque_atual
    quantidade_nova = quantidade_anterior - movement.quantidade
    
    stock_movement = StockMovement(
        produto_id=movement.produto_id,
        tipo=MovementType.SAIDA.value,
        quantidade=movement.quantidade,
        quantidade_anterior=quantidade_anterior,
        quantidade_nova=quantidade_nova,
        motivo=movement.motivo or "Saída manual",
        referencia=movement.referencia,
        usuario_id=current_user.id
    )
    
    produto.estoque_atual = quantidade_nova
    
    db.add(stock_movement)
    db.commit()
    db.refresh(stock_movement)
    
    logger.info(f"Stock exit: -{movement.quantidade} for product {produto.nome}",
                extra={"user_id": current_user.id, "product_id": produto.id})
    
    return _format_movement_response(stock_movement, db)


@router.post("/ajuste", response_model=StockMovementResponse)
async def ajustar_estoque(
    adjustment: StockAdjustment,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Adjust inventory to specific quantity (inventory count)
    """
    produto = db.query(Produto).filter(Produto.id == adjustment.produto_id).first()
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    quantidade_anterior = produto.estoque_atual
    diferenca = adjustment.nova_quantidade - quantidade_anterior
    
    if diferenca == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nova quantidade é igual à atual. Nenhum ajuste necessário."
        )
    
    stock_movement = StockMovement(
        produto_id=adjustment.produto_id,
        tipo=MovementType.AJUSTE.value,
        quantidade=abs(diferenca),
        quantidade_anterior=quantidade_anterior,
        quantidade_nova=adjustment.nova_quantidade,
        motivo=adjustment.motivo,
        usuario_id=current_user.id
    )
    
    produto.estoque_atual = adjustment.nova_quantidade
    
    db.add(stock_movement)
    db.commit()
    db.refresh(stock_movement)
    
    logger.info(f"Stock adjustment: {quantidade_anterior} -> {adjustment.nova_quantidade} for product {produto.nome}",
                extra={"user_id": current_user.id, "product_id": produto.id})
    
    return _format_movement_response(stock_movement, db)


@router.get("/movimentacoes", response_model=List[StockMovementResponse])
async def listar_movimentacoes(
    produto_id: Optional[int] = None,
    tipo: Optional[str] = None,
    dias: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    List stock movements with filtering options
    """
    data_inicio = datetime.utcnow() - timedelta(days=dias)
    
    query = db.query(StockMovement).filter(StockMovement.criado_em >= data_inicio)
    
    if produto_id:
        query = query.filter(StockMovement.produto_id == produto_id)
    
    if tipo:
        query = query.filter(StockMovement.tipo == tipo.upper())
    
    movements = query.order_by(StockMovement.criado_em.desc()).limit(limit).all()
    
    return [_format_movement_response(m, db) for m in movements]


@router.get("/alertas", response_model=List[StockAlert])
async def listar_alertas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    List products below minimum stock level
    """
    from models import Categoria
    
    produtos = db.query(Produto).filter(
        Produto.controlar_estoque == True,
        Produto.ativo == True,
        Produto.estoque_atual <= Produto.estoque_minimo
    ).all()
    
    alertas = []
    for p in produtos:
        categoria = db.query(Categoria).filter(Categoria.id == p.categoria_id).first()
        deficit = p.estoque_minimo - p.estoque_atual
        
        if p.estoque_atual == 0:
            status = "CRITICAL"
        elif deficit > 0:
            status = "LOW"
        else:
            status = "OK"
        
        alertas.append(StockAlert(
            produto_id=p.id,
            produto_nome=p.nome,
            categoria_nome=categoria.nome if categoria else None,
            estoque_atual=p.estoque_atual,
            estoque_minimo=p.estoque_minimo,
            deficit=deficit,
            status=status
        ))
    
    # Sort by deficit (most critical first)
    alertas.sort(key=lambda x: (-1 if x.status == "CRITICAL" else 0, -x.deficit))
    
    return alertas


@router.get("/resumo", response_model=StockSummary)
async def resumo_estoque(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Get stock summary with alerts and recent movements
    """
    # Total products with stock control
    total_produtos = db.query(Produto).filter(
        Produto.controlar_estoque == True,
        Produto.ativo == True
    ).count()
    
    # Products below minimum
    produtos_abaixo = db.query(Produto).filter(
        Produto.controlar_estoque == True,
        Produto.ativo == True,
        Produto.estoque_atual < Produto.estoque_minimo
    ).count()
    
    # Products with zero stock
    produtos_zerados = db.query(Produto).filter(
        Produto.controlar_estoque == True,
        Produto.ativo == True,
        Produto.estoque_atual == 0
    ).count()
    
    # Last 10 movements
    ultimas = db.query(StockMovement).order_by(
        StockMovement.criado_em.desc()
    ).limit(10).all()
    
    # Get alerts
    alertas_response = await listar_alertas(db, current_user)
    
    return StockSummary(
        total_produtos=total_produtos,
        produtos_abaixo_minimo=produtos_abaixo,
        produtos_zerados=produtos_zerados,
        ultimas_movimentacoes=[_format_movement_response(m, db) for m in ultimas],
        alertas=alertas_response[:10]
    )


@router.put("/produto/{produto_id}/limites")
async def atualizar_limites_estoque(
    produto_id: int,
    estoque_minimo: int = Query(..., ge=0),
    estoque_maximo: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Update stock minimum/maximum limits for a product
    """
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    produto.estoque_minimo = estoque_minimo
    produto.estoque_maximo = estoque_maximo
    produto.controlar_estoque = True
    
    db.commit()
    
    return {
        "message": "Limites de estoque atualizados",
        "produto_id": produto_id,
        "estoque_minimo": estoque_minimo,
        "estoque_maximo": estoque_maximo
    }


def _format_movement_response(movement: StockMovement, db: Session) -> StockMovementResponse:
    """Helper to format movement response with related names"""
    produto = db.query(Produto).filter(Produto.id == movement.produto_id).first()
    usuario = db.query(Usuario).filter(Usuario.id == movement.usuario_id).first() if movement.usuario_id else None
    
    return StockMovementResponse(
        id=movement.id,
        produto_id=movement.produto_id,
        produto_nome=produto.nome if produto else None,
        tipo=movement.tipo,
        quantidade=movement.quantidade,
        quantidade_anterior=movement.quantidade_anterior,
        quantidade_nova=movement.quantidade_nova,
        motivo=movement.motivo,
        referencia=movement.referencia,
        usuario_id=movement.usuario_id,
        usuario_nome=usuario.nome_completo if usuario else None,
        criado_em=movement.criado_em
    )
