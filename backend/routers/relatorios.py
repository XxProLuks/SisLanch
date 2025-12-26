"""
LANCH - Reports Router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List

from database import get_db
from models import Pedido, ItemPedido, Produto, Categoria, Funcionario, Usuario, AuditLog
from routers.auth import get_current_user, require_admin

router = APIRouter(prefix="/relatorios", tags=["Relatórios"])


@router.get("/vendas-diarias")
async def relatorio_vendas_diarias(
    data_inicio: str = None,
    data_fim: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Daily sales report"""
    if not data_inicio:
        data_inicio = datetime.now().strftime("%Y-%m-%d")
    if not data_fim:
        data_fim = data_inicio
    
    query = db.query(
        func.date(Pedido.criado_em).label("data"),
        func.count(Pedido.id).label("total_pedidos"),
        func.sum(Pedido.valor_total).label("valor_total")
    ).filter(
        func.date(Pedido.criado_em) >= data_inicio,
        func.date(Pedido.criado_em) <= data_fim,
        Pedido.status != "CANCELADO"
    ).group_by(func.date(Pedido.criado_em)).order_by(func.date(Pedido.criado_em))
    
    result = []
    for row in query.all():
        # Get breakdown by type
        funcionarios = db.query(func.count(Pedido.id), func.sum(Pedido.valor_total)).filter(
            func.date(Pedido.criado_em) == row.data,
            Pedido.tipo_cliente == "FUNCIONARIO",
            Pedido.status != "CANCELADO"
        ).first()
        
        pacientes = db.query(func.count(Pedido.id), func.sum(Pedido.valor_total)).filter(
            func.date(Pedido.criado_em) == row.data,
            Pedido.tipo_cliente == "PACIENTE",
            Pedido.status != "CANCELADO"
        ).first()
        
        result.append({
            "data": str(row.data),
            "total_pedidos": row.total_pedidos,
            "valor_total": float(row.valor_total or 0),
            "funcionarios": {
                "quantidade": funcionarios[0] or 0,
                "valor": float(funcionarios[1] or 0)
            },
            "pacientes": {
                "quantidade": pacientes[0] or 0,
                "valor": float(pacientes[1] or 0)
            }
        })
    
    return result


@router.get("/formas-pagamento")
async def relatorio_formas_pagamento(
    data_inicio: str = None,
    data_fim: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Payment methods report"""
    if not data_inicio:
        data_inicio = datetime.now().strftime("%Y-%m-%d")
    if not data_fim:
        data_fim = data_inicio
    
    query = db.query(
        Pedido.forma_pagamento,
        func.count(Pedido.id).label("quantidade"),
        func.sum(Pedido.valor_total).label("valor")
    ).filter(
        func.date(Pedido.criado_em) >= data_inicio,
        func.date(Pedido.criado_em) <= data_fim,
        Pedido.status != "CANCELADO"
    ).group_by(Pedido.forma_pagamento)
    
    result = {}
    total = 0
    for row in query.all():
        result[row.forma_pagamento] = {
            "quantidade": row.quantidade,
            "valor": float(row.valor or 0)
        }
        total += float(row.valor or 0)
    
    return {
        "periodo": {"inicio": data_inicio, "fim": data_fim},
        "formas": result,
        "total": total
    }


@router.get("/produtos-vendidos")
async def relatorio_produtos_vendidos(
    data_inicio: str = None,
    data_fim: str = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Best selling products report"""
    if not data_inicio:
        data_inicio = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not data_fim:
        data_fim = datetime.now().strftime("%Y-%m-%d")
    
    query = db.query(
        Produto.id,
        Produto.nome,
        Categoria.nome.label("categoria"),
        func.sum(ItemPedido.quantidade).label("quantidade_vendida"),
        func.sum(ItemPedido.subtotal).label("valor_total")
    ).join(ItemPedido, Produto.id == ItemPedido.produto_id)\
     .join(Pedido, ItemPedido.pedido_id == Pedido.id)\
     .join(Categoria, Produto.categoria_id == Categoria.id)\
     .filter(
        func.date(Pedido.criado_em) >= data_inicio,
        func.date(Pedido.criado_em) <= data_fim,
        Pedido.status != "CANCELADO"
    ).group_by(Produto.id, Produto.nome, Categoria.nome)\
     .order_by(func.sum(ItemPedido.quantidade).desc())\
     .limit(limit)
    
    result = []
    for row in query.all():
        result.append({
            "produto_id": row.id,
            "nome": row.nome,
            "categoria": row.categoria,
            "quantidade_vendida": row.quantidade_vendida,
            "valor_total": float(row.valor_total or 0)
        })
    
    return {
        "periodo": {"inicio": data_inicio, "fim": data_fim},
        "produtos": result
    }


@router.get("/funcionarios-consumo")
async def relatorio_consumo_funcionarios(
    competencia_id: int = None,
    setor: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Employee consumption report"""
    from models import Competencia, ConsumoMensal
    
    if competencia_id:
        competencia = db.query(Competencia).filter(Competencia.id == competencia_id).first()
    else:
        competencia = db.query(Competencia).filter(Competencia.status == "ABERTA").first()
    
    if not competencia:
        raise HTTPException(status_code=404, detail="Competência não encontrada")
    
    query = db.query(ConsumoMensal).filter(
        ConsumoMensal.competencia_id == competencia.id,
        ConsumoMensal.valor_total > 0
    ).join(Funcionario)
    
    if setor:
        query = query.filter(Funcionario.setor.ilike(f"%{setor}%"))
    
    consumos = query.order_by(Funcionario.nome).all()
    
    result = []
    total_geral = 0
    for c in consumos:
        valor = float(c.valor_total)
        result.append({
            "matricula": c.funcionario.matricula,
            "nome": c.funcionario.nome,
            "setor": c.funcionario.setor,
            "centro_custo": c.funcionario.centro_custo,
            "limite_mensal": float(c.funcionario.limite_mensal),
            "valor_consumido": valor,
            "saldo": float(c.funcionario.limite_mensal) - valor
        })
        total_geral += valor
    
    return {
        "competencia": competencia.to_dict(),
        "funcionarios": result,
        "total_funcionarios": len(result),
        "total_geral": total_geral
    }


@router.get("/dashboard")
async def dashboard(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Dashboard summary for today"""
    today = datetime.now().date()
    
    # Today's orders
    pedidos_hoje = db.query(Pedido).filter(
        func.date(Pedido.criado_em) == today
    ).all()
    
    pendentes = sum(1 for p in pedidos_hoje if p.status == "PENDENTE")
    preparando = sum(1 for p in pedidos_hoje if p.status == "PREPARANDO")
    entregues = sum(1 for p in pedidos_hoje if p.status == "ENTREGUE")
    
    valor_funcionarios = sum(float(p.valor_total) for p in pedidos_hoje if p.tipo_cliente == "FUNCIONARIO" and p.status != "CANCELADO")
    valor_pacientes = sum(float(p.valor_total) for p in pedidos_hoje if p.tipo_cliente == "PACIENTE" and p.status != "CANCELADO")
    
    return {
        "data": str(today),
        "pedidos": {
            "total": len(pedidos_hoje),
            "pendentes": pendentes,
            "preparando": preparando,
            "entregues": entregues
        },
        "faturamento": {
            "funcionarios": valor_funcionarios,
            "pacientes": valor_pacientes,
            "total": valor_funcionarios + valor_pacientes
        }
    }


@router.get("/audit-log")
async def listar_audit_log(
    tabela: str = None,
    data_inicio: str = None,
    data_fim: str = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """List audit log entries"""
    query = db.query(AuditLog)
    
    if tabela:
        query = query.filter(AuditLog.tabela == tabela)
    if data_inicio:
        query = query.filter(AuditLog.criado_em >= data_inicio)
    if data_fim:
        query = query.filter(AuditLog.criado_em <= data_fim)
    
    logs = query.order_by(AuditLog.criado_em.desc()).limit(limit).all()
    
    return [log.to_dict() for log in logs]


@router.get("/dashboard/charts")
async def get_dashboard_charts(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Get chart data for dashboard visualizations"""
    
    # Sales for last 7 days
    today = datetime.now().date()
    sales_data = []
    sales_labels = []
    
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        daily_total = db.query(func.sum(Pedido.valor_total)).filter(
            func.date(Pedido.criado_em) == date,
            Pedido.status != 'CANCELADO'
        ).scalar() or 0
        
        sales_data.append(float(daily_total))
        sales_labels.append(date.strftime('%d/%m'))
    
    # Top 5 products
    top_products = db.query(
        Produto.nome,
        func.sum(ItemPedido.quantidade).label('total')
    ).join(
        ItemPedido, Produto.id == ItemPedido.produto_id
    ).join(
        Pedido, ItemPedido.pedido_id == Pedido.id
    ).filter(
        Pedido.status != 'CANCELADO',
        Pedido.criado_em >= today - timedelta(days=30)
    ).group_by(
        Produto.id, Produto.nome
    ).order_by(
        func.sum(ItemPedido.quantidade).desc()
    ).limit(5).all()
    
    products_labels = [p[0] for p in top_products]
    products_values = [int(p[1]) for p in top_products]
    
    # Payment methods distribution
    payment_methods = db.query(
        Pedido.forma_pagamento,
        func.count(Pedido.id).label('count')
    ).filter(
        Pedido.status != 'CANCELADO',
        Pedido.criado_em >= today - timedelta(days=30)
    ).group_by(
        Pedido.forma_pagamento
    ).all()
    
    payment_labels = [p[0] for p in payment_methods]
    payment_values = [int(p[1]) for p in payment_methods]
    
    return {
        "sales": {
            "labels": sales_labels,
            "values": sales_data
        },
        "products": {
            "labels": products_labels,
            "values": products_values
        },
        "payments": {
            "labels": payment_labels,
            "values": payment_values
        }
    }
