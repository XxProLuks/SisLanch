"""
LANCH - Orders Router
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime

from database import get_db
from models import (
    Pedido, ItemPedido, Produto, Funcionario, 
    Competencia, ConsumoMensal, Usuario
)
from schemas import PedidoCreate, PedidoUpdate, PedidoResponse, PedidoCozinha
from routers.auth import get_current_user, require_atendente
from utils.audit import log_action

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


def generate_order_number(db: Session) -> str:
    """Generate unique order number"""
    today = datetime.now().strftime("%Y%m%d")
    
    # Count orders today
    count = db.query(Pedido).filter(
        Pedido.numero.like(f"{today}%")
    ).count()
    
    return f"{today}{count + 1:04d}"


@router.get("", response_model=List[PedidoResponse])
async def listar_pedidos(
    status: str = None,
    tipo_cliente: str = None,
    data_inicio: str = None,
    data_fim: str = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """List orders with filters"""
    query = db.query(Pedido)
    
    if status:
        query = query.filter(Pedido.status == status)
    if tipo_cliente:
        query = query.filter(Pedido.tipo_cliente == tipo_cliente)
    if data_inicio:
        query = query.filter(Pedido.criado_em >= data_inicio)
    if data_fim:
        query = query.filter(Pedido.criado_em <= data_fim)
    
    pedidos = query.order_by(Pedido.criado_em.desc()).limit(limit).all()
    return [p.to_dict() for p in pedidos]


@router.get("/cozinha", response_model=List[dict])
async def listar_pedidos_cozinha(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """List pending orders for kitchen display"""
    pedidos = db.query(Pedido).filter(
        Pedido.status.in_(["PENDENTE", "PREPARANDO", "PRONTO"])
    ).order_by(
        # Priority: PENDENTE first, then PREPARANDO, then PRONTO
        func.case(
            (Pedido.status == "PENDENTE", 1),
            (Pedido.status == "PREPARANDO", 2),
            else_=3
        ),
        Pedido.criado_em.asc()
    ).all()
    
    result = []
    now = datetime.now()
    
    for p in pedidos:
        # Calculate wait time
        tempo_espera = int((now - p.criado_em).total_seconds() / 60)
        
        # Build items string
        itens_str = ", ".join([
            f"{item.quantidade}x {item.produto.nome}" 
            for item in p.itens
        ])
        
        result.append({
            "id": p.id,
            "numero": p.numero,
            "tipo_cliente": p.tipo_cliente,
            "cliente": p.funcionario.nome if p.funcionario else "Paciente/Visitante",
            "status": p.status,
            "observacao": p.observacao,
            "criado_em": str(p.criado_em),
            "itens": itens_str,
            "tempo_espera": tempo_espera
        })
    
    return result


@router.get("/hoje")
async def listar_pedidos_hoje(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Get today's orders summary"""
    today = datetime.now().date()
    
    pedidos = db.query(Pedido).filter(
        func.date(Pedido.criado_em) == today
    ).all()
    
    # Calculate summary
    total_funcionarios = sum(1 for p in pedidos if p.tipo_cliente == "FUNCIONARIO")
    total_pacientes = sum(1 for p in pedidos if p.tipo_cliente == "PACIENTE")
    valor_total = sum(float(p.valor_total) for p in pedidos if p.status != "CANCELADO")
    
    return {
        "data": str(today),
        "total_pedidos": len(pedidos),
        "total_funcionarios": total_funcionarios,
        "total_pacientes": total_pacientes,
        "valor_total": valor_total,
        "pedidos": [p.to_dict() for p in pedidos]
    }


@router.get("/{pedido_id}", response_model=PedidoResponse)
async def obter_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Get a single order by ID"""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return pedido.to_dict()


@router.post("", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
async def criar_pedido(
    pedido: PedidoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_atendente)
):
    """Create a new order"""
    # Get current open competency
    competencia = db.query(Competencia).filter(Competencia.status == "ABERTA").first()
    if not competencia:
        raise HTTPException(status_code=400, detail="Não há competência aberta")
    
    funcionario = None
    
    # Validate employee order
    if pedido.tipo_cliente == "FUNCIONARIO":
        if pedido.funcionario_id:
            funcionario = db.query(Funcionario).filter(
                Funcionario.id == pedido.funcionario_id
            ).first()
        elif pedido.matricula:
            funcionario = db.query(Funcionario).filter(
                Funcionario.matricula == pedido.matricula
            ).first()
        else:
            raise HTTPException(
                status_code=400,
                detail="Para funcionário, informe ID ou matrícula"
            )
        
        if not funcionario:
            raise HTTPException(status_code=404, detail="Funcionário não encontrado")
        
        if not funcionario.ativo:
            raise HTTPException(
                status_code=403,
                detail="Funcionário inativo. Consumo bloqueado."
            )
        
        # Force CONVENIO payment
        forma_pagamento = "CONVENIO"
    else:
        # Patient/Visitor
        if pedido.forma_pagamento == "CONVENIO":
            raise HTTPException(
                status_code=400,
                detail="Pacientes não podem usar convênio"
            )
        forma_pagamento = pedido.forma_pagamento
    
    # Calculate order total
    valor_total = 0
    itens_list = []
    
    for item in pedido.itens:
        produto = db.query(Produto).filter(
            Produto.id == item.produto_id,
            Produto.ativo == True
        ).first()
        
        if not produto:
            raise HTTPException(
                status_code=400,
                detail=f"Produto {item.produto_id} não encontrado ou inativo"
            )
        
        subtotal = float(produto.preco) * item.quantidade
        valor_total += subtotal
        
        itens_list.append({
            "produto": produto,
            "quantidade": item.quantidade,
            "preco_unitario": float(produto.preco),
            "subtotal": subtotal
        })
        
        # Check stock
        if produto.controlar_estoque:
            if produto.estoque_atual < item.quantidade:
                raise HTTPException(
                    status_code=400,
                    detail=f"Estoque insuficiente para {produto.nome}. Disponível: {produto.estoque_atual}"
                )
            # Reserve stock (will be committed with order)
            produto.estoque_atual -= item.quantidade
    
    # Check employee limit
    if funcionario:
        consumo = db.query(ConsumoMensal).filter(
            ConsumoMensal.funcionario_id == funcionario.id,
            ConsumoMensal.competencia_id == competencia.id
        ).first()
        
        valor_atual = float(consumo.valor_total) if consumo else 0
        saldo = float(funcionario.limite_mensal) - valor_atual
        
        if valor_total > saldo:
            raise HTTPException(
                status_code=403,
                detail=f"Limite excedido. Saldo disponível: R$ {saldo:.2f}"
            )
    
    # Create order
    db_pedido = Pedido(
        numero=generate_order_number(db),
        tipo_cliente=pedido.tipo_cliente,
        funcionario_id=funcionario.id if funcionario else None,
        usuario_id=current_user.id,
        valor_total=valor_total,
        status="PENDENTE",
        forma_pagamento=forma_pagamento,
        competencia_id=competencia.id,
        observacao=pedido.observacao
    )
    db.add(db_pedido)
    db.flush()  # Get ID before adding items
    
    # Create order items
    for item_data in itens_list:
        db_item = ItemPedido(
            pedido_id=db_pedido.id,
            produto_id=item_data["produto"].id,
            quantidade=item_data["quantidade"],
            preco_unitario=item_data["preco_unitario"],
            subtotal=item_data["subtotal"]
        )
        db.add(db_item)
    
    # Update employee consumption
    if funcionario:
        consumo = db.query(ConsumoMensal).filter(
            ConsumoMensal.funcionario_id == funcionario.id,
            ConsumoMensal.competencia_id == competencia.id
        ).first()
        
        if consumo:
            consumo.valor_total = float(consumo.valor_total) + valor_total
        else:
            consumo = ConsumoMensal(
                funcionario_id=funcionario.id,
                competencia_id=competencia.id,
                valor_total=valor_total
            )
            db.add(consumo)
    
    db.commit()
    db.refresh(db_pedido)
    
    log_action(db, current_user.id, "CRIAR", "pedidos", db_pedido.id, None, db_pedido.to_dict())
    db.commit()
    
    return db_pedido.to_dict()


@router.put("/{pedido_id}/status")
async def atualizar_status_pedido(
    pedido_id: int,
    novo_status: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Update order status"""
    valid_statuses = ["PENDENTE", "PREPARANDO", "PRONTO", "ENTREGUE", "CANCELADO"]
    if novo_status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Status inválido")
    
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    # Check if competency is closed for cancellations
    if novo_status == "CANCELADO":
        competencia = db.query(Competencia).filter(
            Competencia.id == pedido.competencia_id
        ).first()
        
        if competencia and competencia.status == "FECHADA":
            raise HTTPException(
                status_code=403,
                detail="Não é possível cancelar pedido de competência fechada"
            )
        
        # Reverse employee consumption
        if pedido.tipo_cliente == "FUNCIONARIO" and pedido.funcionario_id:
            consumo = db.query(ConsumoMensal).filter(
                ConsumoMensal.funcionario_id == pedido.funcionario_id,
                ConsumoMensal.competencia_id == pedido.competencia_id
            ).first()
            
            if consumo:
                consumo.valor_total = max(0, float(consumo.valor_total) - float(pedido.valor_total))
        
        # Restore stock for cancelled orders
        for item in pedido.itens:
            produto = db.query(Produto).filter(Produto.id == item.produto_id).first()
            if produto and produto.controlar_estoque:
                produto.estoque_atual += item.quantidade
    
    dados_anteriores = {"status": pedido.status}
    pedido.status = novo_status
    db.commit()
    
    log_action(
        db, current_user.id, "ATUALIZAR_STATUS", "pedidos", 
        pedido.id, dados_anteriores, {"status": novo_status}
    )
    db.commit()
    
    return {"message": f"Status atualizado para {novo_status}"}


@router.delete("/{pedido_id}")
async def cancelar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_atendente)
):
    """Cancel an order"""
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    if pedido.status in ["ENTREGUE", "CANCELADO"]:
        raise HTTPException(
            status_code=400,
            detail="Não é possível cancelar pedido já entregue ou cancelado"
        )
    
    # Use status update logic
    return await atualizar_status_pedido(pedido_id, "CANCELADO", db, current_user)
