"""LANCH - Routers package"""

from .auth import router as auth_router
from .pedidos import router as pedidos_router
from .produtos import router as produtos_router
from .funcionarios import router as funcionarios_router
from .competencias import router as competencias_router
from .relatorios import router as relatorios_router
from .admin import router as admin_router
from .audit import router as audit_router
from .estoque import router as estoque_router
from .caixa import router as caixa_router
from .setores import router as setores_router
from .print import router as print_router

__all__ = ['auth_router', 'pedidos_router', 'produtos_router', 'funcionarios_router',
           'competencias_router', 'relatorios_router', 'admin_router', 'audit_router',
           'estoque_router', 'caixa_router', 'setores_router', 'print_router']




