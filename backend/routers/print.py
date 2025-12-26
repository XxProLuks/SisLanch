"""
LANCH - Print Router
API endpoints for printing receipts and reports
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, date

from database import get_db
from models import Usuario, Pedido, ItemPedido, Funcionario
from models.caixa import Caixa, TransacaoCaixa, TransactionType
from routers.auth import get_current_user, require_admin
from config import settings

router = APIRouter(prefix="/print", tags=["Impressão"])


def _format_currency(value: float) -> str:
    """Format value as Brazilian currency"""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _get_print_css() -> str:
    """CSS for thermal printer (80mm width)"""
    return """
    <style>
        @page {
            size: 80mm auto;
            margin: 0;
        }
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Courier New', Courier, monospace;
            font-size: 12px;
            width: 80mm;
            padding: 5mm;
            background: white;
            color: black;
        }
        .header {
            text-align: center;
            border-bottom: 1px dashed #000;
            padding-bottom: 8px;
            margin-bottom: 8px;
        }
        .header h1 {
            font-size: 16px;
            font-weight: bold;
        }
        .header p {
            font-size: 10px;
        }
        .info {
            margin-bottom: 8px;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 2px;
        }
        .divider {
            border-top: 1px dashed #000;
            margin: 8px 0;
        }
        .items {
            margin-bottom: 8px;
        }
        .item {
            margin-bottom: 4px;
        }
        .item-name {
            font-weight: bold;
        }
        .item-details {
            display: flex;
            justify-content: space-between;
            padding-left: 10px;
            font-size: 11px;
        }
        .total-section {
            border-top: 2px solid #000;
            padding-top: 8px;
            margin-top: 8px;
        }
        .total-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 4px;
        }
        .total-row.grand-total {
            font-size: 16px;
            font-weight: bold;
        }
        .footer {
            text-align: center;
            border-top: 1px dashed #000;
            padding-top: 8px;
            margin-top: 12px;
            font-size: 10px;
        }
        .print-btn {
            display: block;
            width: 100%;
            padding: 10px;
            margin-top: 20px;
            background: #007bff;
            color: white;
            border: none;
            cursor: pointer;
            font-size: 14px;
        }
        @media print {
            .print-btn { display: none; }
        }
    </style>
    """


@router.get("/pedido/{pedido_id}", response_class=HTMLResponse)
async def imprimir_comanda(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Generate printable order receipt (comanda)
    """
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido não encontrado"
        )
    
    # Get order items
    itens = db.query(ItemPedido).filter(ItemPedido.pedido_id == pedido_id).all()
    
    # Get customer info
    cliente_info = ""
    if pedido.tipo_cliente == "FUNCIONARIO" and pedido.funcionario_id:
        funcionario = db.query(Funcionario).filter(Funcionario.id == pedido.funcionario_id).first()
        if funcionario:
            cliente_info = f"<p><strong>Funcionário:</strong> {funcionario.nome}</p>"
            cliente_info += f"<p><strong>Matrícula:</strong> {funcionario.matricula}</p>"
    else:
        cliente_info = "<p><strong>Tipo:</strong> Avulso</p>"
    
    # Build items HTML
    itens_html = ""
    for item in itens:
        itens_html += f"""
        <div class="item">
            <div class="item-name">{item.produto.nome if item.produto else 'Produto'}</div>
            <div class="item-details">
                <span>{item.quantidade}x {_format_currency(float(item.preco_unitario))}</span>
                <span>{_format_currency(float(item.subtotal))}</span>
            </div>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Comanda #{pedido.numero}</title>
        {_get_print_css()}
    </head>
    <body>
        <div class="header">
            <h1>LANCH</h1>
            <p>Lanchonete Hospitalar</p>
        </div>
        
        <div class="info">
            <div class="info-row">
                <span><strong>Pedido:</strong></span>
                <span>#{pedido.numero}</span>
            </div>
            <div class="info-row">
                <span><strong>Data:</strong></span>
                <span>{pedido.criado_em.strftime('%d/%m/%Y %H:%M')}</span>
            </div>
            {cliente_info}
            <div class="info-row">
                <span><strong>Pagamento:</strong></span>
                <span>{pedido.forma_pagamento}</span>
            </div>
        </div>
        
        <div class="divider"></div>
        
        <div class="items">
            <p><strong>ITENS DO PEDIDO</strong></p>
            {itens_html}
        </div>
        
        <div class="total-section">
            <div class="total-row">
                <span>Subtotal:</span>
                <span>{_format_currency(float(pedido.valor_total))}</span>
            </div>
            <div class="total-row grand-total">
                <span>TOTAL:</span>
                <span>{_format_currency(float(pedido.valor_total))}</span>
            </div>
        </div>
        
        <div class="footer">
            <p>Obrigado pela preferência!</p>
            <p>Volte sempre</p>
        </div>
        
        <button class="print-btn" onclick="window.print()">🖨️ Imprimir Comanda</button>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)


@router.get("/caixa/{data}", response_class=HTMLResponse)
async def imprimir_fechamento(
    data: date,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Generate printable cash register closing report
    """
    caixa = db.query(Caixa).filter(Caixa.data == data).first()
    
    if not caixa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Caixa não encontrado para esta data"
        )
    
    # Get transactions
    transacoes = db.query(TransacaoCaixa).filter(
        TransacaoCaixa.caixa_id == caixa.id
    ).order_by(TransacaoCaixa.criado_em).all()
    
    # Calculate totals
    vendas = [t for t in transacoes if t.tipo == TransactionType.VENDA.value]
    sangrias = [t for t in transacoes if t.tipo == TransactionType.SANGRIA.value]
    suprimentos = [t for t in transacoes if t.tipo in [TransactionType.SUPRIMENTO.value, TransactionType.TROCO.value]]
    
    total_vendas = sum(float(t.valor) for t in vendas)
    total_sangrias = sum(float(t.valor) for t in sangrias)
    total_suprimentos = sum(float(t.valor) for t in suprimentos)
    
    # Sales by payment method
    vendas_dinheiro = sum(float(t.valor) for t in vendas if t.forma_pagamento == "DINHEIRO")
    vendas_cartao = sum(float(t.valor) for t in vendas if t.forma_pagamento == "CARTAO")
    vendas_pix = sum(float(t.valor) for t in vendas if t.forma_pagamento == "PIX")
    vendas_convenio = sum(float(t.valor) for t in vendas if t.forma_pagamento == "CONVENIO")
    
    # Expected cash = opening + supplies - withdrawals + cash sales
    valor_esperado = float(caixa.valor_abertura or 0) + total_suprimentos - total_sangrias + vendas_dinheiro
    
    # Build transactions HTML
    trans_html = ""
    for t in transacoes[:20]:  # Limit to last 20
        tipo_label = {
            "VENDA": "Venda",
            "SANGRIA": "Sangria",
            "SUPRIMENTO": "Suprimento",
            "TROCO": "Troco"
        }.get(t.tipo, t.tipo)
        
        sinal = "-" if t.tipo == "SANGRIA" else "+"
        trans_html += f"""
        <div class="item-details">
            <span>{t.criado_em.strftime('%H:%M')} - {tipo_label}</span>
            <span>{sinal}{_format_currency(float(t.valor))}</span>
        </div>
        """
    
    # Status
    status_label = "FECHADO ✓" if caixa.status == "FECHADO" else "ABERTO"
    diferenca_html = ""
    if caixa.diferenca is not None:
        diff = float(caixa.diferenca)
        diff_class = "color: green;" if diff >= 0 else "color: red;"
        diferenca_html = f'<div class="total-row"><span>Diferença:</span><span style="{diff_class}">{_format_currency(diff)}</span></div>'
    
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Fechamento de Caixa - {data.strftime('%d/%m/%Y')}</title>
        {_get_print_css()}
    </head>
    <body>
        <div class="header">
            <h1>LANCH</h1>
            <p>Fechamento de Caixa</p>
            <p><strong>{data.strftime('%d/%m/%Y')}</strong></p>
        </div>
        
        <div class="info">
            <div class="info-row">
                <span><strong>Status:</strong></span>
                <span>{status_label}</span>
            </div>
            <div class="info-row">
                <span><strong>Abertura:</strong></span>
                <span>{caixa.aberto_em.strftime('%H:%M') if caixa.aberto_em else '-'}</span>
            </div>
            <div class="info-row">
                <span><strong>Fechamento:</strong></span>
                <span>{caixa.fechado_em.strftime('%H:%M') if caixa.fechado_em else '-'}</span>
            </div>
        </div>
        
        <div class="divider"></div>
        
        <div class="items">
            <p><strong>RESUMO DE VENDAS</strong></p>
            <div class="item-details">
                <span>Dinheiro:</span>
                <span>{_format_currency(vendas_dinheiro)}</span>
            </div>
            <div class="item-details">
                <span>Cartão:</span>
                <span>{_format_currency(vendas_cartao)}</span>
            </div>
            <div class="item-details">
                <span>PIX:</span>
                <span>{_format_currency(vendas_pix)}</span>
            </div>
            <div class="item-details">
                <span>Convênio:</span>
                <span>{_format_currency(vendas_convenio)}</span>
            </div>
        </div>
        
        <div class="divider"></div>
        
        <div class="items">
            <p><strong>MOVIMENTAÇÕES</strong></p>
            <div class="item-details">
                <span>Abertura:</span>
                <span>{_format_currency(float(caixa.valor_abertura or 0))}</span>
            </div>
            <div class="item-details">
                <span>Suprimentos:</span>
                <span>+{_format_currency(total_suprimentos)}</span>
            </div>
            <div class="item-details">
                <span>Sangrias:</span>
                <span>-{_format_currency(total_sangrias)}</span>
            </div>
        </div>
        
        <div class="total-section">
            <div class="total-row">
                <span>Total Vendas:</span>
                <span>{_format_currency(total_vendas)}</span>
            </div>
            <div class="total-row">
                <span>Qtd. Vendas:</span>
                <span>{len(vendas)}</span>
            </div>
            <div class="divider"></div>
            <div class="total-row">
                <span>Valor Esperado:</span>
                <span>{_format_currency(valor_esperado)}</span>
            </div>
            <div class="total-row">
                <span>Valor Informado:</span>
                <span>{_format_currency(float(caixa.valor_fechamento)) if caixa.valor_fechamento else '-'}</span>
            </div>
            {diferenca_html}
        </div>
        
        <div class="footer">
            <p>Impresso em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            <p>LANCH - Sistema de Gestão</p>
        </div>
        
        <button class="print-btn" onclick="window.print()">🖨️ Imprimir Relatório</button>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)


@router.get("/relatorio/consumo-setor/{setor_id}", response_class=HTMLResponse)
async def imprimir_consumo_setor(
    setor_id: int,
    competencia_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """
    Generate printable sector consumption report
    """
    from models.setor import Setor
    from models import ConsumoMensal, Competencia
    
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
    
    competencia_str = f"{competencia.mes:02d}/{competencia.ano}" if competencia else "Atual"
    
    # Get employees
    funcionarios = db.query(Funcionario).filter(
        Funcionario.setor_id == setor_id,
        Funcionario.ativo == True
    ).order_by(Funcionario.nome).all()
    
    # Build employees HTML
    func_html = ""
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
        limite = float(func.limite_mensal) if func.limite_mensal else 0
        saldo = limite - consumo
        
        func_html += f"""
        <div class="item">
            <div class="item-name">{func.nome}</div>
            <div class="item-details">
                <span>Mat: {func.matricula}</span>
                <span>Limite: {_format_currency(limite)}</span>
            </div>
            <div class="item-details">
                <span>Consumo: {_format_currency(consumo)}</span>
                <span>Saldo: {_format_currency(saldo)}</span>
            </div>
        </div>
        """
    
    limite_setor = float(setor.limite_mensal) if setor.limite_mensal else None
    saldo_setor = limite_setor - total_consumo if limite_setor else None
    
    html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Consumo por Setor - {setor.nome}</title>
        {_get_print_css()}
    </head>
    <body>
        <div class="header">
            <h1>LANCH</h1>
            <p>Relatório de Consumo por Setor</p>
            <p><strong>Competência: {competencia_str}</strong></p>
        </div>
        
        <div class="info">
            <div class="info-row">
                <span><strong>Setor:</strong></span>
                <span>{setor.nome}</span>
            </div>
            <div class="info-row">
                <span><strong>Centro Custo:</strong></span>
                <span>{setor.centro_custo or '-'}</span>
            </div>
            <div class="info-row">
                <span><strong>Funcionários:</strong></span>
                <span>{len(funcionarios)}</span>
            </div>
        </div>
        
        <div class="divider"></div>
        
        <div class="items">
            <p><strong>FUNCIONÁRIOS</strong></p>
            {func_html}
        </div>
        
        <div class="total-section">
            <div class="total-row">
                <span>Total Funcionários:</span>
                <span>{len(funcionarios)}</span>
            </div>
            <div class="total-row grand-total">
                <span>Consumo Total:</span>
                <span>{_format_currency(total_consumo)}</span>
            </div>
            {"<div class='total-row'><span>Limite Setor:</span><span>" + _format_currency(limite_setor) + "</span></div>" if limite_setor else ""}
            {"<div class='total-row'><span>Saldo:</span><span>" + _format_currency(saldo_setor) + "</span></div>" if saldo_setor else ""}
        </div>
        
        <div class="footer">
            <p>Impresso em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
        
        <button class="print-btn" onclick="window.print()">🖨️ Imprimir Relatório</button>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)
