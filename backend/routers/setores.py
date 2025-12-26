"""
LANCH - Setor (Department) Router
API endpoints for department/cost center management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, date

from database import get_db
from models import Usuario, Funcionario, ConsumoMensal, Competencia
from models.setor import Setor
from schemas.setor import (
    SetorCreate, SetorUpdate, SetorResponse,
    SetorResumo, ConsumoSetorReport
)
from routers.auth import require_admin, get_current_user
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/setores", tags=["Setores"])


@router.get("", response_model=List[SetorResponse])
async def listar_setores(
    ativo: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    List all sectors/departments
    """
    query = db.query(Setor)
    
    if ativo is not None:
        query = query.filter(Setor.ativo == ativo)
    
    setores = query.order_by(Setor.nome).all()
    
    return [_format_setor_response(s, db) for s in setores]


@router.get("/resumo", response_model=List[SetorResumo])
async def resumo_setores(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Get summary of all sectors with current consumption
    """
    # Get current competency
    competencia = db.query(Competencia).filter(
        Competencia.status == "ABERTA"
    ).order_by(Competencia.ano.desc(), Competencia.mes.desc()).first()
    
    setores = db.query(Setor).filter(Setor.ativo == True).all()
    resumos = []
    
    for setor in setores:
        # Count employees
        total_funcionarios = db.query(Funcionario).filter(
            Funcionario.setor_id == setor.id,
            Funcionario.ativo == True
        ).count()
        
        # Calculate consumption for current month
        consumo_mes = 0
        if competencia:
            funcionario_ids = db.query(Funcionario.id).filter(
                Funcionario.setor_id == setor.id
            ).all()
            funcionario_ids = [f[0] for f in funcionario_ids]
            
            if funcionario_ids:
                consumo = db.query(func.sum(ConsumoMensal.valor_consumido)).filter(
                    ConsumoMensal.funcionario_id.in_(funcionario_ids),
                    ConsumoMensal.competencia_id == competencia.id
                ).scalar() or 0
                consumo_mes = float(consumo)
        
        # Calculate percentage
        limite = float(setor.limite_mensal) if setor.limite_mensal else None
        percentual = (consumo_mes / limite * 100) if limite and limite > 0 else 0
        saldo = limite - consumo_mes if limite else None
        
        resumos.append(SetorResumo(
            id=setor.id,
            nome=setor.nome,
            codigo=setor.codigo,
            centro_custo=setor.centro_custo,
            limite_mensal=limite,
            total_funcionarios=total_funcionarios,
            consumo_mes_atual=consumo_mes,
            percentual_consumido=round(percentual, 2),
            saldo_disponivel=round(saldo, 2) if saldo else None
        ))
    
    return resumos


@router.get("/{setor_id}", response_model=SetorResponse)
async def get_setor(
    setor_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Get sector by ID
    """
    setor = db.query(Setor).filter(Setor.id == setor_id).first()
    
    if not setor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setor não encontrado"
        )
    
    return _format_setor_response(setor, db)


@router.post("", response_model=SetorResponse)
async def criar_setor(
    dados: SetorCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Create a new sector/department
    """
    # Check if name already exists
    existing = db.query(Setor).filter(Setor.nome == dados.nome).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um setor com este nome"
        )
    
    # Check if code already exists
    if dados.codigo:
        existing = db.query(Setor).filter(Setor.codigo == dados.codigo).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe um setor com este código"
            )
    
    setor = Setor(
        nome=dados.nome,
        codigo=dados.codigo,
        centro_custo=dados.centro_custo,
        limite_mensal=dados.limite_mensal,
        limite_por_funcionario=dados.limite_por_funcionario,
        responsavel=dados.responsavel,
        email_responsavel=dados.email_responsavel,
        descricao=dados.descricao
    )
    
    db.add(setor)
    db.commit()
    db.refresh(setor)
    
    logger.info(f"Sector created: {setor.nome}",
                extra={"user_id": current_user.id, "setor_id": setor.id})
    
    return _format_setor_response(setor, db)


@router.put("/{setor_id}", response_model=SetorResponse)
async def atualizar_setor(
    setor_id: int,
    dados: SetorUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Update a sector
    """
    setor = db.query(Setor).filter(Setor.id == setor_id).first()
    
    if not setor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setor não encontrado"
        )
    
    # Check name uniqueness if changing
    if dados.nome and dados.nome != setor.nome:
        existing = db.query(Setor).filter(Setor.nome == dados.nome).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Já existe um setor com este nome"
            )
    
    # Update fields
    update_data = dados.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(setor, field, value)
    
    setor.atualizado_em = datetime.utcnow()
    
    db.commit()
    db.refresh(setor)
    
    logger.info(f"Sector updated: {setor.nome}",
                extra={"user_id": current_user.id, "setor_id": setor.id})
    
    return _format_setor_response(setor, db)


@router.delete("/{setor_id}")
async def excluir_setor(
    setor_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Delete (deactivate) a sector
    """
    setor = db.query(Setor).filter(Setor.id == setor_id).first()
    
    if not setor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setor não encontrado"
        )
    
    # Check if there are employees
    funcionarios_count = db.query(Funcionario).filter(
        Funcionario.setor_id == setor_id,
        Funcionario.ativo == True
    ).count()
    
    if funcionarios_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Não é possível excluir. Existem {funcionarios_count} funcionários ativos neste setor."
        )
    
    setor.ativo = False
    db.commit()
    
    logger.info(f"Sector deactivated: {setor.nome}",
                extra={"user_id": current_user.id, "setor_id": setor.id})
    
    return {"message": "Setor desativado com sucesso"}


@router.get("/{setor_id}/consumo", response_model=ConsumoSetorReport)
async def consumo_setor(
    setor_id: int,
    competencia_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Get detailed consumption report for a sector
    """
    setor = db.query(Setor).filter(Setor.id == setor_id).first()
    
    if not setor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setor não encontrado"
        )
    
    # Get competency
    if competencia_id:
        competencia = db.query(Competencia).filter(Competencia.id == competencia_id).first()
    else:
        competencia = db.query(Competencia).filter(
            Competencia.status == "ABERTA"
        ).order_by(Competencia.ano.desc(), Competencia.mes.desc()).first()
    
    # Get employees in this sector
    funcionarios = db.query(Funcionario).filter(
        Funcionario.setor_id == setor_id,
        Funcionario.ativo == True
    ).all()
    
    funcionarios_data = []
    total_consumo = 0
    
    for func in funcionarios:
        consumo = 0
        if competencia:
            cm = db.query(ConsumoMensal).filter(
                ConsumoMensal.funcionario_id == func.id,
                ConsumoMensal.competencia_id == competencia.id
            ).first()
            if cm:
                consumo = float(cm.valor_consumido)
        
        total_consumo += consumo
        
        funcionarios_data.append({
            "id": func.id,
            "nome": func.nome,
            "matricula": func.matricula,
            "limite_mensal": float(func.limite_mensal) if func.limite_mensal else None,
            "consumo": consumo,
            "saldo": float(func.limite_mensal) - consumo if func.limite_mensal else None
        })
    
    # Sort by consumption descending
    funcionarios_data.sort(key=lambda x: x["consumo"], reverse=True)
    
    media = total_consumo / len(funcionarios) if funcionarios else 0
    
    return ConsumoSetorReport(
        setor_id=setor.id,
        setor_nome=setor.nome,
        centro_custo=setor.centro_custo,
        limite_mensal=float(setor.limite_mensal) if setor.limite_mensal else None,
        total_funcionarios=len(funcionarios),
        consumo_total=round(total_consumo, 2),
        consumo_medio_funcionario=round(media, 2),
        funcionarios=funcionarios_data
    )


def _format_setor_response(setor: Setor, db: Session) -> SetorResponse:
    """Format sector response with stats"""
    # Count employees
    total_funcionarios = db.query(Funcionario).filter(
        Funcionario.setor_id == setor.id,
        Funcionario.ativo == True
    ).count()
    
    # Get current consumption
    competencia = db.query(Competencia).filter(
        Competencia.status == "ABERTA"
    ).order_by(Competencia.ano.desc(), Competencia.mes.desc()).first()
    
    consumo_atual = 0
    if competencia:
        funcionario_ids = db.query(Funcionario.id).filter(
            Funcionario.setor_id == setor.id
        ).all()
        funcionario_ids = [f[0] for f in funcionario_ids]
        
        if funcionario_ids:
            consumo = db.query(func.sum(ConsumoMensal.valor_consumido)).filter(
                ConsumoMensal.funcionario_id.in_(funcionario_ids),
                ConsumoMensal.competencia_id == competencia.id
            ).scalar() or 0
            consumo_atual = float(consumo)
    
    return SetorResponse(
        id=setor.id,
        nome=setor.nome,
        codigo=setor.codigo,
        centro_custo=setor.centro_custo,
        limite_mensal=float(setor.limite_mensal) if setor.limite_mensal else None,
        limite_por_funcionario=float(setor.limite_por_funcionario) if setor.limite_por_funcionario else None,
        responsavel=setor.responsavel,
        email_responsavel=setor.email_responsavel,
        descricao=setor.descricao,
        ativo=setor.ativo,
        criado_em=setor.criado_em,
        atualizado_em=setor.atualizado_em,
        total_funcionarios=total_funcionarios,
        consumo_atual=consumo_atual
    )
