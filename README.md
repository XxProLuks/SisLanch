# LANCH - Sistema de Lanchonete Hospitalar

Sistema web completo para gestão de lanchonete hospitalar com suporte a:

- **Funcionários**: Consumo via convênio com desconto em folha
- **Pacientes/Visitantes**: Pagamento imediato (Pix, Cartão, Dinheiro)

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.10+
- Node.js (opcional, apenas para servidor estático)

### Instalação

```bash
# 1. Clone o repositório
cd Lanch

# 2. Configure as variáveis de ambiente
cp .env.example .env

# 3. IMPORTANTE: Edite o arquivo .env e configure:
#    - SECRET_KEY: Gere uma nova chave com: python -c "import secrets; print(secrets.token_urlsafe(32))"
#    - ALLOWED_ORIGINS: Configure os domínios permitidos
#    - Outras configurações conforme necessário

# 4. Instalar dependências do backend
cd backend
pip install -r requirements.txt

# 5. Iniciar o servidor
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 🐳 Docker (Recomendado para Produção)

```bash
# 1. Configure o arquivo .env (veja passo 3 acima)

# 2. Build e executar com Docker Compose
docker-compose up -d

# 3. Verificar logs
docker-compose logs -f

# 4. Parar o serviço
docker-compose down
```

### Acessar o Sistema

1. **Backend API**: <http://localhost:8000>
2. **Documentação API**: <http://localhost:8000/docs>
3. **Frontend**: Abrir `frontend/index.html` no navegador

### 🔐 Segurança - IMPORTANTE

> [!CAUTION]
> **ATENÇÃO**: O sistema possui senha padrão para o administrador que **DEVE** ser alterada antes de usar em produção!

#### Credenciais Padrão (Apenas Desenvolvimento)

| Usuário | Senha | Perfil |
|---------|-------|--------|
| admin | admin123 | Administrador |

> [!WARNING]
> **O login com a senha padrão será BLOQUEADO automaticamente**. Você precisará alterar a senha diretamente no banco de dados ou criar um novo usuário administrador.

#### Primeira Configuração de Segurança

1. **Gere uma SECRET_KEY forte**:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Configure o arquivo .env**:

   ```bash
   SECRET_KEY=sua-chave-gerada-aqui
   DEBUG=False  # NUNCA True em produção!
   ALLOWED_ORIGINS=https://seu-dominio.com.br
   ```

3. **Altere a senha do admin**:
   - Faça login no sistema
   - Vá para configurações e altere sua senha
   - Escolha uma senha forte (mínimo 8 caracteres, com maiúscula, minúscula e número)

## 📋 Funcionalidades

### Perfil: Atendente

- Criar pedidos para funcionários (convênio)
- Criar pedidos para pacientes (pagamento imediato)
- Identificar funcionário por matrícula/CPF

### Perfil: Cozinha

- Visualizar pedidos em tempo real
- Atualizar status dos pedidos (Pendente → Preparando → Pronto → Entregue)

### Perfil: Administrador

- Gerenciar produtos e categorias
- Gerenciar funcionários
- Fechar competências mensais
- Exportar para Excel/CSV (TOTVS RM)
- Visualizar relatórios
- Consultar logs de auditoria
- Alterar senha de usuários

## 🔄 Fluxo de Pedido

### Funcionário

1. Identificação por matrícula ou CPF
2. Validação de status ativo e limite disponível
3. Registro do pedido com pagamento CONVÊNIO
4. Valor acumulado na competência atual

### Paciente

1. Seleção de tipo "Paciente/Visitante"
2. Adição de produtos ao pedido
3. Pagamento imediato (Pix, Cartão, Dinheiro)

## 📊 Fechamento Mensal

1. Admin acessa "Competências"
2. Clica em "Fechar Competência"
3. Sistema consolida todos os consumos
4. Gera arquivos Excel e CSV
5. Layout compatível com TOTVS RM

## 📁 Estrutura do Projeto

```
c:\Lanch\
├── backend/
│   ├── main.py              # Entrada da aplicação
│   ├── config.py            # Configurações
│   ├── database.py          # Conexão com banco
│   ├── models/              # Modelos SQLAlchemy
│   ├── schemas/             # Schemas Pydantic
│   ├── routers/             # Endpoints da API
│   ├── services/            # Lógica de negócio
│   ├── utils/               # Utilitários
│   ├── middleware/          # Middlewares (rate limiting, etc.)
│   └── requirements.txt     # Dependências
├── frontend/
│   ├── index.html           # Página principal
│   ├── css/styles.css       # Estilos
│   └── js/
│       ├── validators.js    # Validações frontend
│       ├── api.js           # Cliente da API
│       └── app.js           # Lógica do frontend
├── database/
│   ├── schema.sql           # Schema do banco
│   └── lanch.db             # Banco SQLite
└── exports/                 # Arquivos exportados
```

## 🔐 Segurança

- ✅ Autenticação JWT com chave configurável
- ✅ Controle de acesso por perfil (RBAC)
- ✅ Rate limiting em endpoints de autenticação (proteção contra força bruta)
- ✅ Log de auditoria para todas as alterações
- ✅ Validação de força de senha
- ✅ Detecção e bloqueio de senhas padrão
- ✅ CORS configurável por ambiente
- ✅ Logging estruturado com rotação
- ✅ Validação de limite de consumo
- ✅ Proteção contra alterações em competências fechadas
- ✅ Sanitização de inputs no frontend

## 📝 Variáveis de Ambiente

Todas as configurações sensíveis devem ser definidas no arquivo `.env`:

| Variável | Descrição | Obrigatório |
|----------|-----------|-------------|
| `SECRET_KEY` | Chave secreta para JWT | ✅ Sim |
| `DEBUG` | Modo debug (False em produção) | Não (padrão: False) |
| `ALLOWED_ORIGINS` | Origens CORS permitidas | Não (padrão: localhost) |
| `DATABASE_URL` | URL do banco de dados | Não (padrão: SQLite) |
| `LOGIN_RATE_LIMIT` | Limite de tentativas de login | Não (padrão: 5/min) |
| `LOG_LEVEL` | Nível de logging | Não (padrão: INFO) |

Veja `.env.example` para lista completa e documentação.

## 🧪 Testes

```bash
# Executar suite de testes
cd tests
python test_api.py

# Testes devem passar 100%
```

## 📞 Suporte

Sistema desenvolvido para ambiente hospitalar com foco em:

- Simplicidade operacional
- Confiabilidade para RH
- Auditabilidade completa
- Integração com TOTVS RM
- Segurança e proteção de dados

## 📄 Licença

Sistema proprietário - Todos os direitos reservados

---

**⚠️ Checklist de Deploy em Produção**

Antes de fazer deploy, certifique-se de:

- [ ] Arquivo `.env` configurado com SECRET_KEY forte
- [ ] DEBUG=False no arquivo .env
- [ ] ALLOWED_ORIGINS configurado com domínios corretos
- [ ] Senha do admin alterada
- [ ] Banco de dados com backup configurado
- [ ] Logs monitorados
- [ ] HTTPS configurado no servidor web
- [ ] Testes executados e passando
