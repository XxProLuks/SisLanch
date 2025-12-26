@echo off
REM ============================================================
REM LANCH - Script para iniciar o servidor (Windows)
REM ============================================================

echo ============================================================
echo    LANCH - Sistema de Lanchonete Hospitalar
echo ============================================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado! Instale Python 3.10+
    pause
    exit /b 1
)

REM Diretório do script
cd /d "%~dp0"

REM Verificar se .env existe
if not exist ".env" (
    echo [AVISO] Arquivo .env nao encontrado!
    echo Copiando .env.example para .env...
    copy .env.example .env
    echo.
    echo [IMPORTANTE] Configure o arquivo .env antes de continuar!
    echo Edite SECRET_KEY e outras configuracoes necessarias.
    pause
)

REM Verificar e criar ambiente virtual se não existir
if not exist ".venv" (
    echo [INFO] Criando ambiente virtual...
    python -m venv .venv
)

REM Ativar ambiente virtual
echo [INFO] Ativando ambiente virtual...
call .venv\Scripts\activate.bat

REM Instalar dependências se necessário
if not exist ".venv\Lib\site-packages\fastapi" (
    echo [INFO] Instalando dependencias...
    pip install -r backend\requirements.txt
)

REM Criar diretórios necessários
if not exist "logs" mkdir logs
if not exist "exports" mkdir exports
if not exist "backups" mkdir backups

REM Validar ambiente
echo [INFO] Validando ambiente...
python scripts\validate_env.py
if errorlevel 1 (
    echo [ERRO] Falha na validacao do ambiente!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo    Iniciando servidor em http://localhost:8000
echo    Frontend: http://localhost:8000 (abrir frontend/index.html)
echo    API Docs: http://localhost:8000/docs
echo    Pressione Ctrl+C para parar
echo ============================================================
echo.

REM Iniciar servidor
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
