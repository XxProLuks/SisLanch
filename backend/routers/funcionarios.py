"""
LANCH - Employees Router
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Funcionario, Competencia, ConsumoMensal, Usuario
from schemas import (
    FuncionarioCreate, FuncionarioUpdate, FuncionarioResponse, FuncionarioConsumo
)
from routers.auth import get_current_user, require_admin, require_atendente
from utils.audit import log_action

router = APIRouter(prefix="/funcionarios", tags=["Funcionários"])


@router.get("", response_model=List[FuncionarioResponse])
async def listar_funcionarios(
    ativo: bool = None,
    setor: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """List all employees with optional filters"""
    query = db.query(Funcionario)
    
    if ativo is not None:
        query = query.filter(Funcionario.ativo == ativo)
    if setor:
        query = query.filter(Funcionario.setor.ilike(f"%{setor}%"))
    
    return query.order_by(Funcionario.nome).all()


@router.get("/buscar")
async def buscar_funcionario(
    matricula: str = None,
    cpf: str = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_atendente)
):
    """Search employee by matricula or CPF for order creation"""
    if not matricula and not cpf:
        raise HTTPException(
            status_code=400,
            detail="Informe matrícula ou CPF"
        )
    
    query = db.query(Funcionario)
    
    if matricula:
        funcionario = query.filter(Funcionario.matricula == matricula).first()
    else:
        # Clean CPF
        cpf_clean = ''.join(filter(str.isdigit, cpf))
        funcionario = query.filter(Funcionario.cpf == cpf_clean).first()
    
    if not funcionario:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    
    if not funcionario.ativo:
        raise HTTPException(
            status_code=403,
            detail="Funcionário inativo. Consumo bloqueado."
        )
    
    # Get current consumption
    competencia = db.query(Competencia).filter(Competencia.status == "ABERTA").first()
    
    valor_consumido = 0.0
    if competencia:
        consumo = db.query(ConsumoMensal).filter(
            ConsumoMensal.funcionario_id == funcionario.id,
            ConsumoMensal.competencia_id == competencia.id
        ).first()
        if consumo:
            valor_consumido = float(consumo.valor_total)
    
    saldo = float(funcionario.limite_mensal) - valor_consumido
    
    return {
        **funcionario.to_dict(),
        "valor_consumido": valor_consumido,
        "saldo_disponivel": saldo,
        "competencia": competencia.to_dict() if competencia else None
    }


@router.get("/{funcionario_id}", response_model=FuncionarioResponse)
async def obter_funcionario(
    funcionario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Get a single employee by ID"""
    funcionario = db.query(Funcionario).filter(Funcionario.id == funcionario_id).first()
    if not funcionario:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    return funcionario


@router.post("", response_model=FuncionarioResponse, status_code=status.HTTP_201_CREATED)
async def criar_funcionario(
    funcionario: FuncionarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Create a new employee"""
    # Clean CPF
    cpf_clean = ''.join(filter(str.isdigit, funcionario.cpf))
    
    # Check duplicates
    existing = db.query(Funcionario).filter(
        (Funcionario.matricula == funcionario.matricula) |
        (Funcionario.cpf == cpf_clean)
    ).first()
    
    if existing:
        if existing.matricula == funcionario.matricula:
            raise HTTPException(status_code=400, detail="Matrícula já cadastrada")
        raise HTTPException(status_code=400, detail="CPF já cadastrado")
    
    func_data = funcionario.model_dump()
    func_data['cpf'] = cpf_clean
    
    db_funcionario = Funcionario(**func_data)
    db.add(db_funcionario)
    db.commit()
    db.refresh(db_funcionario)
    
    log_action(db, current_user.id, "CRIAR", "funcionarios", db_funcionario.id, None, db_funcionario.to_dict())
    db.commit()
    
    return db_funcionario


@router.put("/{funcionario_id}", response_model=FuncionarioResponse)
async def atualizar_funcionario(
    funcionario_id: int,
    funcionario: FuncionarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Update an existing employee"""
    db_func = db.query(Funcionario).filter(Funcionario.id == funcionario_id).first()
    if not db_func:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    
    dados_anteriores = db_func.to_dict()
    
    update_data = funcionario.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_func, key, value)
    
    db.commit()
    db.refresh(db_func)
    
    log_action(db, current_user.id, "ATUALIZAR", "funcionarios", db_func.id, dados_anteriores, db_func.to_dict())
    db.commit()
    
    return db_func


@router.delete("/{funcionario_id}")
async def desativar_funcionario(
    funcionario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    """Deactivate an employee (soft delete)"""
    funcionario = db.query(Funcionario).filter(Funcionario.id == funcionario_id).first()
    if not funcionario:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    
    dados_anteriores = funcionario.to_dict()
    funcionario.ativo = False
    db.commit()
    
    log_action(db, current_user.id, "DESATIVAR", "funcionarios", funcionario.id, dados_anteriores, funcionario.to_dict())
    db.commit()
    
    return {"message": "Funcionário desativado com sucesso"}


@router.get("/{funcionario_id}/consumo")
async def obter_consumo_funcionario(
    funcionario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Get employee consumption history"""
    funcionario = db.query(Funcionario).filter(Funcionario.id == funcionario_id).first()
    if not funcionario:
        raise HTTPException(status_code=404, detail="Funcionário não encontrado")
    
    consumos = db.query(ConsumoMensal).filter(
        ConsumoMensal.funcionario_id == funcionario_id
    ).join(Competencia).order_by(Competencia.ano.desc(), Competencia.mes.desc()).all()
    
    return {
        "funcionario": funcionario.to_dict(),
        "consumos": [c.to_dict() for c in consumos]
    }
