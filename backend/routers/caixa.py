"""
LANCH - Cash Register Router
API endpoints for financial management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal

from database import get_db
from models import Usuario, Pedido
from models.caixa import Caixa, TransacaoCaixa, CaixaStatus, TransactionType
from schemas.caixa import (
    CaixaOpen, CaixaClose, CaixaResponse, CaixaResumo,
    TransacaoCreate, TransacaoResponse, SangriaCreate, SuprimentoCreate,
    RelatorioFinanceiro
)
from routers.auth import require_admin, get_current_user
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/caixa", tags=["Caixa"])


def _get_or_create_today_caixa(db: Session) -> Caixa:
    """Get today's cash register or return None if not opened"""
    today = date.today()
    return db.query(Caixa).filter(Caixa.data == today).first()


@router.post("/abrir", response_model=CaixaResponse)
async def abrir_caixa(
    dados: CaixaOpen,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Open cash register for today
    """
    today = date.today()
    
    # Check if already opened
    existing = db.query(Caixa).filter(Caixa.data == today).first()
    if existing:
        if existing.status == CaixaStatus.ABERTO.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Caixa já está aberto hoje"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Caixa de hoje já foi fechado"
        )
    
    # Create new cash register
    caixa = Caixa(
        data=today,
        valor_abertura=dados.valor_abertura,
        status=CaixaStatus.ABERTO.value,
        usuario_abertura_id=current_user.id,
        aberto_em=datetime.utcnow()
    )
    
    db.add(caixa)
    
    # Add initial change as transaction if > 0
    if dados.valor_abertura > 0:
        transacao = TransacaoCaixa(
            caixa=caixa,
            tipo=TransactionType.TROCO.value,
            valor=dados.valor_abertura,
            descricao="Abertura de caixa - Troco inicial",
            usuario_id=current_user.id
        )
        db.add(transacao)
    
    db.commit()
    db.refresh(caixa)
    
    logger.info(f"Cash register opened with R${dados.valor_abertura}",
                extra={"user_id": current_user.id, "caixa_id": caixa.id})
    
    return _format_caixa_response(caixa, db)


@router.post("/fechar", response_model=CaixaResponse)
async def fechar_caixa(
    dados: CaixaClose,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Close cash register for today
    """
    caixa = _get_or_create_today_caixa(db)
    
    if not caixa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum caixa aberto hoje"
        )
    
    if caixa.status == CaixaStatus.FECHADO.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Caixa já está fechado"
        )
    
    # Calculate expected value
    resumo = _calculate_caixa_summary(caixa, db)
    
    caixa.valor_fechamento = dados.valor_fechamento
    caixa.valor_esperado = resumo["valor_esperado"]
    caixa.diferenca = dados.valor_fechamento - resumo["valor_esperado"]
    caixa.status = CaixaStatus.FECHADO.value
    caixa.usuario_fechamento_id = current_user.id
    caixa.fechado_em = datetime.utcnow()
    caixa.observacoes = dados.observacoes
    
    db.commit()
    db.refresh(caixa)
    
    logger.info(f"Cash register closed. Expected: R${resumo['valor_esperado']}, Actual: R${dados.valor_fechamento}",
                extra={"user_id": current_user.id, "caixa_id": caixa.id, "diferenca": float(caixa.diferenca)})
    
    return _format_caixa_response(caixa, db)


@router.get("/hoje", response_model=Optional[CaixaResponse])
async def get_caixa_hoje(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Get today's cash register status
    """
    caixa = _get_or_create_today_caixa(db)
    
    if not caixa:
        return None
    
    return _format_caixa_response(caixa, db)


@router.get("/resumo", response_model=CaixaResumo)
async def get_resumo_caixa(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Get current cash register summary for closing
    """
    caixa = _get_or_create_today_caixa(db)
    
    if not caixa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum caixa aberto hoje"
        )
    
    summary = _calculate_caixa_summary(caixa, db)
    
    return CaixaResumo(
        caixa_id=caixa.id,
        data=caixa.data,
        status=caixa.status,
        valor_abertura=float(caixa.valor_abertura or 0),
        total_vendas=summary["total_vendas"],
        total_sangrias=summary["total_sangrias"],
        total_suprimentos=summary["total_suprimentos"],
        valor_esperado=summary["valor_esperado"],
        transacoes_count=summary["transacoes_count"],
        vendas_dinheiro=summary["vendas_dinheiro"],
        vendas_cartao=summary["vendas_cartao"],
        vendas_pix=summary["vendas_pix"],
        vendas_convenio=summary["vendas_convenio"]
    )


@router.post("/sangria", response_model=TransacaoResponse)
async def registrar_sangria(
    dados: SangriaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Register cash withdrawal (sangria)
    """
    caixa = _get_or_create_today_caixa(db)
    
    if not caixa or caixa.status != CaixaStatus.ABERTO.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Caixa não está aberto"
        )
    
    transacao = TransacaoCaixa(
        caixa_id=caixa.id,
        tipo=TransactionType.SANGRIA.value,
        valor=dados.valor,
        descricao=dados.motivo,
        usuario_id=current_user.id
    )
    
    db.add(transacao)
    db.commit()
    db.refresh(transacao)
    
    logger.info(f"Cash withdrawal: R${dados.valor} - {dados.motivo}",
                extra={"user_id": current_user.id, "caixa_id": caixa.id})
    
    return _format_transacao_response(transacao, db)


@router.post("/suprimento", response_model=TransacaoResponse)
async def registrar_suprimento(
    dados: SuprimentoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Register cash addition (suprimento/troco)
    """
    caixa = _get_or_create_today_caixa(db)
    
    if not caixa or caixa.status != CaixaStatus.ABERTO.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Caixa não está aberto"
        )
    
    transacao = TransacaoCaixa(
        caixa_id=caixa.id,
        tipo=TransactionType.SUPRIMENTO.value,
        valor=dados.valor,
        descricao=dados.descricao or "Suprimento de caixa",
        usuario_id=current_user.id
    )
    
    db.add(transacao)
    db.commit()
    db.refresh(transacao)
    
    logger.info(f"Cash addition: R${dados.valor}",
                extra={"user_id": current_user.id, "caixa_id": caixa.id})
    
    return _format_transacao_response(transacao, db)


@router.get("/transacoes", response_model=List[TransacaoResponse])
async def listar_transacoes(
    data: Optional[date] = None,
    tipo: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    List transactions for a specific date
    """
    target_date = data or date.today()
    
    caixa = db.query(Caixa).filter(Caixa.data == target_date).first()
    if not caixa:
        return []
    
    query = db.query(TransacaoCaixa).filter(TransacaoCaixa.caixa_id == caixa.id)
    
    if tipo:
        query = query.filter(TransacaoCaixa.tipo == tipo.upper())
    
    transacoes = query.order_by(TransacaoCaixa.criado_em.desc()).all()
    
    return [_format_transacao_response(t, db) for t in transacoes]


@router.get("/historico", response_model=List[CaixaResponse])
async def listar_historico(
    dias: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    List cash register history
    """
    data_inicio = date.today() - timedelta(days=dias)
    
    caixas = db.query(Caixa).filter(
        Caixa.data >= data_inicio
    ).order_by(Caixa.data.desc()).all()
    
    return [_format_caixa_response(c, db) for c in caixas]


@router.get("/relatorio", response_model=RelatorioFinanceiro)
async def relatorio_financeiro(
    data_inicio: date = Query(...),
    data_fim: date = Query(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Financial report for a date range
    """
    if data_fim < data_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data fim deve ser maior ou igual à data início"
        )
    
    # Get all transactions in range
    caixas = db.query(Caixa).filter(
        and_(Caixa.data >= data_inicio, Caixa.data <= data_fim)
    ).all()
    
    caixa_ids = [c.id for c in caixas]
    
    transacoes = db.query(TransacaoCaixa).filter(
        TransacaoCaixa.caixa_id.in_(caixa_ids),
        TransacaoCaixa.tipo == TransactionType.VENDA.value
    ).all()
    
    # Calculate totals
    total_vendas = sum(float(t.valor) for t in transacoes)
    total_pedidos = len(transacoes)
    ticket_medio = total_vendas / total_pedidos if total_pedidos > 0 else 0
    
    # Group by payment method
    vendas_por_pagamento = {
        "DINHEIRO": 0,
        "CARTAO": 0,
        "PIX": 0,
        "CONVENIO": 0
    }
    
    for t in transacoes:
        if t.forma_pagamento in vendas_por_pagamento:
            vendas_por_pagamento[t.forma_pagamento] += float(t.valor)
    
    # Group by day
    vendas_por_dia = []
    for caixa in caixas:
        day_transacoes = [t for t in transacoes if t.caixa_id == caixa.id]
        total = sum(float(t.valor) for t in day_transacoes)
        vendas_por_dia.append({
            "data": caixa.data.isoformat(),
            "total": total,
            "pedidos": len(day_transacoes)
        })
    
    return RelatorioFinanceiro(
        data_inicio=data_inicio,
        data_fim=data_fim,
        total_vendas=total_vendas,
        total_pedidos=total_pedidos,
        ticket_medio=round(ticket_medio, 2),
        vendas_por_dia=vendas_por_dia,
        vendas_por_pagamento=vendas_por_pagamento
    )


# ==================== Helper Functions ====================

def _calculate_caixa_summary(caixa: Caixa, db: Session) -> dict:
    """Calculate cash register summary"""
    transacoes = db.query(TransacaoCaixa).filter(
        TransacaoCaixa.caixa_id == caixa.id
    ).all()
    
    total_vendas = sum(float(t.valor) for t in transacoes if t.tipo == TransactionType.VENDA.value)
    total_sangrias = sum(float(t.valor) for t in transacoes if t.tipo == TransactionType.SANGRIA.value)
    total_suprimentos = sum(float(t.valor) for t in transacoes if t.tipo in [TransactionType.SUPRIMENTO.value, TransactionType.TROCO.value])
    
    # Sales by payment method
    vendas_dinheiro = sum(float(t.valor) for t in transacoes if t.tipo == TransactionType.VENDA.value and t.forma_pagamento == "DINHEIRO")
    vendas_cartao = sum(float(t.valor) for t in transacoes if t.tipo == TransactionType.VENDA.value and t.forma_pagamento == "CARTAO")
    vendas_pix = sum(float(t.valor) for t in transacoes if t.tipo == TransactionType.VENDA.value and t.forma_pagamento == "PIX")
    vendas_convenio = sum(float(t.valor) for t in transacoes if t.tipo == TransactionType.VENDA.value and t.forma_pagamento == "CONVENIO")
    
    # Expected value in cash drawer = opening + cash sales + additions - withdrawals
    # Note: Convenio doesn't count as cash
    valor_esperado = float(caixa.valor_abertura or 0) + vendas_dinheiro + total_suprimentos - total_sangrias
    
    return {
        "total_vendas": total_vendas,
        "total_sangrias": total_sangrias,
        "total_suprimentos": total_suprimentos,
        "valor_esperado": round(valor_esperado, 2),
        "transacoes_count": len(transacoes),
        "vendas_dinheiro": vendas_dinheiro,
        "vendas_cartao": vendas_cartao,
        "vendas_pix": vendas_pix,
        "vendas_convenio": vendas_convenio
    }


def _format_caixa_response(caixa: Caixa, db: Session) -> CaixaResponse:
    """Format cash register response"""
    summary = _calculate_caixa_summary(caixa, db)
    
    usuario_abertura = db.query(Usuario).filter(Usuario.id == caixa.usuario_abertura_id).first() if caixa.usuario_abertura_id else None
    usuario_fechamento = db.query(Usuario).filter(Usuario.id == caixa.usuario_fechamento_id).first() if caixa.usuario_fechamento_id else None
    
    return CaixaResponse(
        id=caixa.id,
        data=caixa.data,
        status=caixa.status,
        valor_abertura=float(caixa.valor_abertura or 0),
        valor_fechamento=float(caixa.valor_fechamento) if caixa.valor_fechamento else None,
        valor_esperado=float(caixa.valor_esperado) if caixa.valor_esperado else summary["valor_esperado"],
        diferenca=float(caixa.diferenca) if caixa.diferenca else None,
        usuario_abertura_id=caixa.usuario_abertura_id,
        usuario_abertura_nome=usuario_abertura.nome_completo if usuario_abertura else None,
        usuario_fechamento_id=caixa.usuario_fechamento_id,
        usuario_fechamento_nome=usuario_fechamento.nome_completo if usuario_fechamento else None,
        aberto_em=caixa.aberto_em,
        fechado_em=caixa.fechado_em,
        observacoes=caixa.observacoes,
        total_vendas=summary["total_vendas"],
        total_dinheiro=summary["vendas_dinheiro"],
        total_cartao=summary["vendas_cartao"],
        total_pix=summary["vendas_pix"],
        total_convenio=summary["vendas_convenio"]
    )


def _format_transacao_response(transacao: TransacaoCaixa, db: Session) -> TransacaoResponse:
    """Format transaction response"""
    usuario = db.query(Usuario).filter(Usuario.id == transacao.usuario_id).first() if transacao.usuario_id else None
    pedido = db.query(Pedido).filter(Pedido.id == transacao.pedido_id).first() if transacao.pedido_id else None
    
    return TransacaoResponse(
        id=transacao.id,
        caixa_id=transacao.caixa_id,
        tipo=transacao.tipo,
        valor=float(transacao.valor),
        forma_pagamento=transacao.forma_pagamento,
        pedido_id=transacao.pedido_id,
        pedido_numero=pedido.numero if pedido else None,
        descricao=transacao.descricao,
        usuario_id=transacao.usuario_id,
        usuario_nome=usuario.nome_completo if usuario else None,
        criado_em=transacao.criado_em
    )
