"""
LANCH - Pydantic Schemas for Reports
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class ConsumoFuncionarioReport(BaseModel):
    matricula: str
    nome: str
    setor: str
    centro_custo: str
    valor_total: float
    competencia: str


class VendaDiariaReport(BaseModel):
    data: date
    total_pedidos: int
    total_funcionarios: int
    total_pacientes: int
    valor_convenio: float
    valor_pix: float
    valor_cartao: float
    valor_dinheiro: float
    valor_total: float


class ProdutoVendidoReport(BaseModel):
    produto_id: int
    nome: str
    categoria: str
    quantidade_vendida: int
    valor_total: float


class CompetenciaFechamento(BaseModel):
    id: int
    ano: int
    mes: int
    referencia: str
    status: str
    total_funcionarios: int
    valor_total: float
    fechada_em: Optional[datetime] = None


class RelatorioMensal(BaseModel):
    competencia: str
    funcionarios: List[ConsumoFuncionarioReport]
    total_geral: float
    total_funcionarios: int
