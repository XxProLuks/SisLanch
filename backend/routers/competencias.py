"""
LANCH - Competencias (Monthly Closing) Router
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime
import io

from database import get_db
from models import Competencia, ConsumoMensal, Funcionario, Pedido, Usuario
from schemas import CompetenciaFechamento
from routers.auth import get_current_user, require_admin
from utils.audit import log_action
from services.export_service import export_to_excel, export_to_csv

router = APIRouter(prefix="/competencias", tags=["Competências"])


@router.get("", response_model=List[dict])
async def listar_competencias(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """List all competencies"""
    competencias = db.query(Competencia).order_by(
        Competencia.ano.desc(), Competencia.mes.desc()
    ).all()
    
    result = []
    for c in competencias:
        # Get consumption totals
        consumo_total = db.query(func.sum(ConsumoMensal.valor_total)).filter(
            ConsumoMensal.competencia_id == c.id
        ).scalar() or 0
        
        total_funcionarios = db.query(ConsumoMensal).filter(
            ConsumoMensal.competencia_id == c.id,
            ConsumoMensal.valor_total > 0
        ).count()
        
        result.append({
            **c.to_dict(),
            "valor_total": float(consumo_total),
            "total_funcionarios": total_funcionarios
        })
    
    return result


@router.get("/atual", response_model=dict)
async def obter_competencia_atual(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Get current open competency"""
    competencia = db.query(Competencia).filter(
        Competencia.status == "ABERTA"
    ).first()
    
    if not competencia:
        raise HTTPException(status_code=404, detail="Não há competência aberta")
    
    # Get summary
    consumos = db.query(ConsumoMensal).filter(
        ConsumoMensal.competencia_id == competencia.id
    ).all()
    
    valor_total = sum(float(c.valor_total) for c in consumos)
    
    return {
        **competencia.to_dict(),
        "valor_total": valor_total,
        "total_funcionarios": len([c for c in consumos if c.valor_total > 0])
    }


@router.get("/{competencia_id}/consumos")
async def listar_consumos_competencia(
    competencia_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """List all consumption records for a competency"""
    competencia = db.query(Competencia).filter(Competencia.id == competencia_id).first()
    if not competencia:
        raise HTTPException(status_code=404, detail="Competência não encontrada")
    
    consumos = db.query(ConsumoMensal).filter(
        ConsumoMensal.competencia_id == competencia_id
    ).join(Funcionario).order_by(Funcionario.nome).all()
    
    result = []
    for c in consumos:
        if c.valor_total > 0:
            result.append({
                "funcionario_id": c.funcionario_id,
                "matricula": c.funcionario.matricula,
                "nome": c.funcionario.nome,
                "setor": c.funcionario.setor,
                "centro_custo": c.funcionario.centro_custo,
                "valor_total": float(c.valor_total)
            })
    
    return {
        "competencia": competencia.to_dict(),
        "consumos": result,
        "total_geral": sum(item["valor_total"] for item in result)
    }


@router.post("/nova")
async def criar_competencia(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Create a new competency (next month)"""
    # Get latest competency
    ultima = db.query(Competencia).order_by(
        Competencia.ano.desc(), Competencia.mes.desc()
    ).first()
    
    if ultima:
        if ultima.mes == 12:
            novo_ano = ultima.ano + 1
            novo_mes = 1
        else:
            novo_ano = ultima.ano
            novo_mes = ultima.mes + 1
    else:
        now = datetime.now()
        novo_ano = now.year
        novo_mes = now.month
    
    # Check if already exists
    existing = db.query(Competencia).filter(
        Competencia.ano == novo_ano,
        Competencia.mes == novo_mes
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Competência já existe")
    
    nova = Competencia(ano=novo_ano, mes=novo_mes, status="ABERTA")
    db.add(nova)
    db.commit()
    db.refresh(nova)
    
    log_action(db, current_user.id, "CRIAR", "competencias", nova.id, None, nova.to_dict())
    db.commit()
    
    return nova.to_dict()


@router.post("/{competencia_id}/fechar")
async def fechar_competencia(
    competencia_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Close a competency (no more orders allowed)"""
    competencia = db.query(Competencia).filter(Competencia.id == competencia_id).first()
    if not competencia:
        raise HTTPException(status_code=404, detail="Competência não encontrada")
    
    if competencia.status == "FECHADA":
        raise HTTPException(status_code=400, detail="Competência já está fechada")
    
    # Close competency
    dados_anteriores = competencia.to_dict()
    competencia.status = "FECHADA"
    competencia.fechada_em = datetime.now()
    competencia.fechada_por = current_user.id
    
    db.commit()
    
    log_action(db, current_user.id, "FECHAR", "competencias", competencia.id, dados_anteriores, competencia.to_dict())
    db.commit()
    
    # Auto create next competency
    if competencia.mes == 12:
        prox_ano = competencia.ano + 1
        prox_mes = 1
    else:
        prox_ano = competencia.ano
        prox_mes = competencia.mes + 1
    
    prox_comp = db.query(Competencia).filter(
        Competencia.ano == prox_ano,
        Competencia.mes == prox_mes
    ).first()
    
    if not prox_comp:
        prox_comp = Competencia(ano=prox_ano, mes=prox_mes, status="ABERTA")
        db.add(prox_comp)
        db.commit()
    
    return {
        "message": "Competência fechada com sucesso",
        "competencia_fechada": competencia.to_dict(),
        "proxima_competencia": prox_comp.to_dict()
    }


@router.get("/{competencia_id}/export/excel")
async def exportar_excel(
    competencia_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Export competency consumption to Excel"""
    competencia = db.query(Competencia).filter(Competencia.id == competencia_id).first()
    if not competencia:
        raise HTTPException(status_code=404, detail="Competência não encontrada")
    
    consumos = db.query(ConsumoMensal).filter(
        ConsumoMensal.competencia_id == competencia_id,
        ConsumoMensal.valor_total > 0
    ).join(Funcionario).order_by(Funcionario.nome).all()
    
    # Build data
    data = []
    for c in consumos:
        data.append({
            "matricula": c.funcionario.matricula,
            "nome": c.funcionario.nome,
            "setor": c.funcionario.setor,
            "centro_custo": c.funcionario.centro_custo,
            "valor_total": float(c.valor_total),
            "competencia": f"{competencia.mes:02d}/{competencia.ano}"
        })
    
    # Generate Excel
    excel_buffer = export_to_excel(data, competencia)
    
    filename = f"desconto_folha_{competencia.mes:02d}_{competencia.ano}.xlsx"
    
    return Response(
        content=excel_buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{competencia_id}/export/csv")
async def exportar_csv(
    competencia_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Export competency consumption to CSV (TOTVS RM compatible)"""
    competencia = db.query(Competencia).filter(Competencia.id == competencia_id).first()
    if not competencia:
        raise HTTPException(status_code=404, detail="Competência não encontrada")
    
    consumos = db.query(ConsumoMensal).filter(
        ConsumoMensal.competencia_id == competencia_id,
        ConsumoMensal.valor_total > 0
    ).join(Funcionario).order_by(Funcionario.nome).all()
    
    # Build data
    data = []
    for c in consumos:
        data.append({
            "matricula": c.funcionario.matricula,
            "nome": c.funcionario.nome,
            "setor": c.funcionario.setor,
            "centro_custo": c.funcionario.centro_custo,
            "valor_total": float(c.valor_total),
            "competencia": f"{competencia.mes:02d}/{competencia.ano}"
        })
    
    # Generate CSV
    csv_content = export_to_csv(data, competencia)
    
    filename = f"desconto_folha_{competencia.mes:02d}_{competencia.ano}.csv"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
