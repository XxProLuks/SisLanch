#!/bin/bash
# ============================================================
# LANCH - Script para iniciar o servidor (Linux/Mac)
# ============================================================

echo "============================================================"
echo "   LANCH - Sistema de Lanchonete Hospitalar"
echo "============================================================"
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretório do script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERRO] Python3 não encontrado! Instale Python 3.10+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}[OK] Python $PYTHON_VERSION${NC}"

# Verificar .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[AVISO] Arquivo .env não encontrado!${NC}"
    echo "Copiando .env.example para .env..."
    cp .env.example .env
    echo ""
    echo -e "${YELLOW}[IMPORTANTE] Configure o arquivo .env antes de continuar!${NC}"
    echo "Edite SECRET_KEY e outras configurações necessárias."
    read -p "Pressione Enter para continuar..."
fi

# Criar ambiente virtual se não existir
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}[INFO] Criando ambiente virtual...${NC}"
    python3 -m venv .venv
fi

# Ativar ambiente virtual
echo -e "${BLUE}[INFO] Ativando ambiente virtual...${NC}"
source .venv/bin/activate

# Instalar dependências se necessário
if [ ! -f ".venv/lib/python*/site-packages/fastapi/__init__.py" ] 2>/dev/null; then
    echo -e "${BLUE}[INFO] Instalando dependências...${NC}"
    pip install -r backend/requirements.txt
fi

# Criar diretórios necessários
mkdir -p logs exports backups

# Validar ambiente
echo -e "${BLUE}[INFO] Validando ambiente...${NC}"
python3 scripts/validate_env.py
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERRO] Falha na validação do ambiente!${NC}"
    exit 1
fi

echo ""
echo "============================================================"
echo -e "   ${GREEN}Iniciando servidor em http://localhost:8000${NC}"
echo "   Frontend: Abrir frontend/index.html no navegador"
echo "   API Docs: http://localhost:8000/docs"
echo "   Pressione Ctrl+C para parar"
echo "============================================================"
echo ""

# Iniciar servidor
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
