@echo off
REM ============================================================
REM LANCH - Script para iniciar servidor de desenvolvimento
REM Abre backend e frontend simultaneamente
REM ============================================================

echo ============================================================
echo    LANCH - Modo Desenvolvimento
echo ============================================================

REM Diretório do script
cd /d "%~dp0"

REM Verificar ambiente virtual
if not exist ".venv\Scripts\activate.bat" (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo Execute start.bat primeiro para configurar.
    pause
    exit /b 1
)

REM Ativar ambiente virtual
call .venv\Scripts\activate.bat

REM Criar diretórios
if not exist "logs" mkdir logs
if not exist "exports" mkdir exports
if not exist "backups" mkdir backups

echo.
echo [INFO] Iniciando backend...
echo [INFO] API: http://localhost:8000
echo [INFO] Docs: http://localhost:8000/docs
echo.

REM Abrir frontend no navegador padrão
start "" "frontend\index.html"

REM Iniciar backend
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
