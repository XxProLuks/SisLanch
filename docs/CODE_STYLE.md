# LANCH - Guia de Estilo de Código

Padrões e melhores práticas para o código do projeto LANCH.

## 📋 Índice

- [Python (Backend)](#python-backend)
- [JavaScript (Frontend)](#javascript-frontend)
- [CSS](#css)
- [Banco de Dados](#banco-de-dados)
- [Documentação](#documentação)

## 🐍 Python (Backend)

### Type Hints

**Sempre use type hints** em funções e métodos:

```python
from typing import Optional, List, Dict

def buscar_produto(produto_id: int) -> Optional[Produto]:
    """Busca produto por ID"""
    return db.query(Produto).filter(Produto.id == produto_id).first()

def listar_produtos(categoria_id: Optional[int] = None) -> List[Produto]:
    """Lista produtos, opcionalmente filtrados por categoria"""
    query = db.query(Produto)
    if categoria_id:
        query = query.filter(Produto.categoria_id == categoria_id)
    return query.all()
```

### Docstrings

Use **Google style docstrings**:

```python
def calcular_total_pedido(itens: List[ItemPedido]) -> Decimal:
    """
    Calcula o valor total de um pedido
    
    Args:
        itens: Lista de itens do pedido
        
    Returns:
        Valor total do pedido com 2 casas decimais
        
    Raises:
        ValueError: Se a lista de itens estiver vazia
        
    Examples:
        >>> itens = [ItemPedido(preco=10.50, quantidade=2)]
        >>> calcular_total_pedido(itens)
        Decimal('21.00')
    """
    if not itens:
        raise ValueError("Lista de itens não pode estar vazia")
    
    return sum(item.subtotal for item in itens)
```

### Tratamento de Erros

**Seja específico** com exceções:

```python
# ❌ Ruim
try:
    resultado = operacao()
except:
    pass

# ✅ Bom
try:
    resultado = operacao_perigosa()
except ValueError as e:
    logger.error(f"Valor inválido: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except DatabaseError as e:
    logger.error(f"Erro de banco: {e}")
    raise HTTPException(status_code=500, detail="Erro interno")
```

### Validação com Pydantic

Use **field validators** para validação customizada:

```python
from pydantic import BaseModel, Field, field_validator

class ProdutoCreate(BaseModel):
    nome: str = Field(..., min_length=1, max_length=200)
    preco: float = Field(..., gt=0)
    
    @field_validator('nome')
    @classmethod
    def nome_nao_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Nome não pode estar vazio')
        return v.strip()
    
    @field_validator('preco')
    @classmethod
    def preco_valido(cls, v: float) -> float:
        if v > 9999.99:
            raise ValueError('Preço muito alto')
        return round(v, 2)
```

### Logging

Use **structured logging**:

```python
import logging

logger = logging.getLogger(__name__)

# ❌ Ruim
logger.info("Usuario 123 fez login")

# ✅ Bom
logger.info(
    "User logged in",
    extra={
        "user_id": 123,
        "username": "admin",
        "ip": request.client.host
    }
)
```

---

## 📜 JavaScript (Frontend)

### JSDoc

**Documente todas as funções** com JSDoc:

```javascript
/**
 * Busca pedidos do servidor
 * @param {Object} filters - Filtros de busca
 * @param {string} [filters.status] - Status do pedido
 * @param {number} [filters.page=1] - Página atual
 * @returns {Promise<Array<Object>>} Lista de pedidos
 * @throws {Error} Se a requisição falhar
 * @example
 * const pedidos = await fetchPedidos({ status: 'PENDENTE' });
 */
async function fetchPedidos(filters = {}) {
    const params = new URLSearchParams(filters);
    const response = await fetch(`/api/pedidos?${params}`);
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response.json();
}
```

### Async/Await

**Prefira async/await** a Promises:

```javascript
// ❌ Ruim
function salvarProduto(data) {
    return fetch('/api/produtos', {
        method: 'POST',
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(produto => {
        showToast('Produto salvo!');
        return produto;
    })
    .catch(err => {
        showError(err.message);
    });
}

// ✅ Bom
async function salvarProduto(data) {
    try {
        const response = await fetch('/api/produtos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`Erro ${response.status}`);
        }
        
        const produto = await response.json();
        showToast('Produto salvo com sucesso!');
        return produto;
        
    } catch (error) {
        logger.error('Erro ao salvar produto:', error);
        showError('Não foi possível salvar o produto');
        throw error;
    }
}
```

### Validação

**Valide entradas** antes de usar:

```javascript
/**
 * Valida dados de produto
 * @param {Object} data - Dados do produto
 * @returns {boolean} True se válido
 * @throws {ValidationError} Se dados inválidos
 */
function validateProduto(data) {
    const errors = [];
    
    if (!data.nome || data.nome.trim() === '') {
        errors.push('Nome é obrigatório');
    }
    
    if (!data.preco || data.preco <= 0) {
        errors.push('Preço deve ser maior que zero');
    }
    
    if (errors.length > 0) {
        throw new ValidationError(errors.join(', '));
    }
    
    return true;
}
```

### Event Handlers

**Use event delegation** quando possível:

```javascript
// ❌ Ruim - adiciona listener em cada botão
document.querySelectorAll('.delete-btn').forEach(btn => {
    btn.addEventListener('click', handleDelete);
});

// ✅ Bom - um listener no container
document.getElementById('products-table').addEventListener('click', (e) => {
    if (e.target.matches('.delete-btn')) {
        handleDelete(e);
    }
});
```

---

## 🎨 CSS

### Namingção

Use **BEM (Block Element Modifier)**:

```css
/* Block */
.product-card { }

/* Element */
.product-card__title { }
.product-card__price { }

/* Modifier */
.product-card--featured { }
.product-card--out-of-stock { }
```

### Variáveis CSS

Defina **variáveis** para valores reutilizáveis:

```css
:root {
    /* Colors */
    --primary: #2563eb;
    --success: #10b981;
    --danger: #ef4444;
    
    /* Spacing */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    
    /* Typography */
    --font-base: 'Inter', sans-serif;
    --text-sm: 0.875rem;
    --text-base: 1rem;
    --text-lg: 1.125rem;
}
```

### Mobile First

Escreva CSS **mobile-first**:

```css
/* Base: mobile */
.container {
    padding: var(--spacing-sm);
}

/* Tablet e acima */
@media (min-width: 768px) {
    .container {
        padding: var(--spacing-md);
    }
}

/* Desktop e acima */
@media (min-width: 1024px) {
    .container {
        padding: var(--spacing-lg);
    }
}
```

---

## 🗄️ Banco de Dados

### Nomenclatura

- **Tabelas**: plural, snake_case (`produtos`, `itens_pedido`)
- **Colunas**: singular, snake_case (`nome`, `preco_unitario`)
- **Foreign Keys**: `{tabela}_id` (`categoria_id`, `pedido_id`)

### Índices

Crie índices para **colunas frequentemente consultadas**:

```sql
-- Índice simples
CREATE INDEX idx_produtos_categoria ON produtos(categoria_id);

-- Índice composto
CREATE INDEX idx_pedidos_data_status ON pedidos(criado_em, status);

-- Índice parcial
CREATE INDEX idx_pedidos_ativos ON pedidos(status) 
WHERE status IN ('PENDENTE', 'PREPARANDO');
```

---

## 📚 Documentação

### README

Inclua no README:
- ✅ Descrição do projeto
- ✅ Pré-requisitos
- ✅ Instalação passo a passo
- ✅ Configuração (.env)
- ✅ Como executar
- ✅ Como testar
- ✅ Troubleshooting

### Comentários de Código

```python
# ❌ Ruim - óbvio
x = x + 1  # incrementa x

# ✅ Bom - explica "por quê"
# Adiciona margem extra para compensar bug do IE11
margin_left = base_margin + 10

# ✅ Bom - avisa sobre comportamento não-óbvio
# IMPORTANTE: Este método modifica o objeto original
def processar_pedido(pedido):
    pedido.status = 'PROCESSADO'  # Modifica in-place
```

### TODOs

Use **formato padrão** para TODOs:

```python
# TODO(nome): Adicionar validação de CPF
# FIXME: Corrigir bug de arredondamento
# HACK: Workaround temporário para issue #123
# NOTE: Este código será removido na v2.0
```

---

## ✅ Checklist de Code Review

Antes de fazer commit:

**Python**:
- [ ] Type hints em todas funções
- [ ] Docstrings em funções públicas
- [ ] Tratamento de erros específico
- [ ] Testes passando
- [ ] Sem warnings do linter

**JavaScript**:
- [ ] JSDoc em funções exportadas
- [ ] Async/await ao invés de Promises
- [ ] Validação de inputs
- [ ] Sem console.log em produção

**Geral**:
- [ ] Código auto-explicativo
- [ ] Funções pequenas (< 50 linhas)
- [ ] DRY (Don't Repeat Yourself)
- [ ] SOLID principles
- [ ] Sem código comentado
