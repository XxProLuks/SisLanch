# LANCH - Guia de Troubleshooting

Soluções para problemas comuns no sistema LANCH.

## 🚫 Erro ao Iniciar Servidor

### Sintoma

```
SECRET_KEY must be changed from the example value!
```

**Causa**: SECRET_KEY não foi configurada ou está usando valor de exemplo.

**Solução**:

```bash
# Gerar nova SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Editar .env
nano .env
# Adicionar: SECRET_KEY=<valor-gerado-acima>
```

### Sintoma

```
ValidationError: 2 validation errors
```

**Causa**: Variáveis obrigatórias faltando no .env

**Solução**:

```bash
# Validar configuração
python scripts/validate_env.py

# Copiar exemplo se necessário
cp .env.example .env
```

### Sintoma

```
ModuleNotFoundError: No module named 'fastapi'
```

**Causa**: Dependências não instaladas

**Solução**:

```bash
cd backend
pip install -r requirements.txt
```

## 🔐 Problemas de Autenticação

### Sintoma

Login retorna 401 "Credenciais inválidas"

**Possíveis Causas**:

1. Senha incorreta
2. SECRET_KEY mudou (invalidou tokens antigos)
3. Usuário inativo

**Soluções**:

```bash
# Resetar senha do admin via Python
python -c "
from database import SessionLocal
from models import Usuario
from utils.security import get_password_hash

db = SessionLocal()
admin = db.query(Usuario).filter(Usuario.username == 'admin').first()
if admin:
    admin.password_hash = get_password_hash('nova_senha_aqui')
    db.commit()
    print('Senha atualizada!')
else:
    print('Usuário admin não encontrado')
db.close()
"
```

### Sintoma

```
403 Forbidden - "Default password detected"
```

**Causa**: Usando senha padrão "admin123"

**Solução**: Alterar senha através das configurações do sistema ou resetar via script acima.

## 💾 Problemas com Banco de Dados

### Sintoma

```
OperationalError: database is locked
```

**Causa**: Múltiplos processos tentando acessar SQLite simultaneamente

**Solução**:

```bash
# Verificar processos em execução
ps aux | grep uvicorn

# Matar processos duplicados
kill -9 <PID>

# Reiniciar serviço corretamente
sudo systemctl restart lanch
```

### Sintoma

Dados não aparecem ou tabelas vazias

**Causa**: Banco não inicializado

**Solução**:

```bash
cd backend
python -c "from database import init_db; init_db()"
```

### Sintoma

```
IntegrityError: UNIQUE constraint failed
```

**Causa**: Tentando criar registro duplicado (matrícula, CPF, etc)

**Solução**: Verificar se registro já existe antes de criar novo.

## 🌐 Problemas de CORS

### Sintoma

Console do navegador mostra:

```
Access to fetch at 'http://localhost:8000/...' from origin 'null' has been blocked by CORS policy
```

**Causa**: Origem não permitida em ALLOWED_ORIGINS

**Solução**:

```bash
# Editar .env
nano .env

# Adicionar origem
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:5500,file://

# Em desenvolvimento, pode usar DEBUG=True para permitir todas origens
DEBUG=True  # NUNCA usar em produção!
```

## 🔄 Problemas com Service Worker

### Sintoma

Assets não carregam offline ou versão antiga do site aparece

**Causa**: Service worker com cache antigo

**Solução**:

```javascript
// No console do navegador:
navigator.serviceWorker.getRegistrations().then(function(registrations) {
    for(let registration of registrations) {
        registration.unregister();
    }
    location.reload();
});
```

## 📊 Gráficos Não Aparecem

### Sintoma

Dashboard mostra áreas vazias onde deveriam estar gráficos

**Possíveis Causas**:

1. Chart.js não carregou
2. Dados insuficientes
3.JavaScript error

**Soluções**:

```bash
# 1. Verificar console do navegador (F12)
# Procurar por erros JavaScript

# 2. Verificar se charts.js está incluído no HTML
grep "charts.js" frontend/index.html

# 3. Limpar cache do navegador (Ctrl+Shift+R)

# 4. Verificar se há dados
# Criar alguns pedidos de teste
```

## 🔥 Performance Lenta

### Sintoma

Sistema demora muito para responder

**Diagnóstico**:

```bash
# Verificar uso de CPU e memória
top
htop

# Verificar logs
tail -f logs/*.log

# Verificar tamanho do banco
ls -lh database/lanch.db
```

**Soluções**:

```bash
# 1. Limpar logs antigos
find logs/ -name "*.log" -type f -mtime +30 -delete

# 2. Se banco muito grande, fazer vacuum
sqlite3 database/lanch.db "VACUUM;"

# 3. Aumentar workers (se usando Gunicorn)
# Editar /etc/systemd/system/lanch.service
# --workers 4 (2 x CPU cores)

# 4. Adicionar cache no Nginx
```

## 💾 Backup Falha

### Sintoma

```
Backup failed: Database file not found
```

**Causa**: Caminho do banco incorreto

**Solução**:

```bash
# Verificar DATABASE_URL no .env
cat .env | grep DATABASE_URL

# Verificar se arquivo existe
ls -l database/lanch.db

# Executar backup manualmente
python scripts/backup_now.py
```

### Sintoma

```
Permission denied
```

**Causa**: Sem permissão para escrever em backups/

**Solução**:

```bash
# Criar diretório com permissões corretas
mkdir -p backups
chmod 755 backups
chown lanch:lanch backups
```

## 🔌 API Não Responde

### Sintoma

```
Failed to fetch
Connection refused
```

**Diagnóstico**:

```bash
# Verificar se serviço está rodando
sudo systemctl status lanch

# Verificar logs
sudo journalctl -u lanch -n 50

# Verificar se porta está aberta
netstat -tulpn | grep 8000
```

**Soluções**:

```bash
# Reiniciar serviço
sudo systemctl restart lanch

# Se não iniciar, ver logs para erro
sudo journalctl -u lanch -xe

# Testar manualmente
cd backend
/opt/lanch/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📝 Logs Gigantes

### Sintoma

Disco cheio devido a logs

**Solução**:

```bash
# Implementar rotação de logs
sudo nano /etc/logrotate.d/lanch
```

```
/opt/lanch/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 lanch lanch
}
```

## 🔍 Debug Mode em Produção

### Sintoma

Erros muito verbosos em produção

**Causa**: DEBUG=True no .env

**Solução**:

```bash
# NUNCA deixar DEBUG=True em produção!
nano .env
# Mudar para: DEBUG=False

# Reiniciar
sudo systemctl restart lanch
```

## 📱 Frontend Não Carrega

### Sintoma

Página em branco ou erro 404

**Diagnóstico**:

```bash
# Verificar Nginx
sudo nginx -t
sudo systemctl status nginx

# Ver logs
tail -f /var/log/nginx/error.log
```

**Soluções**:

```bash
# Verificar permissões
ls -la /opt/lanch/frontend/

# Aplicar permissões corretas
sudo chown -R lanch:www-data /opt/lanch/frontend
sudo chmod -R 755 /opt/lanch/frontend

# Recarregar Nginx
sudo systemctl reload nginx
```

## 🆘 Último Recurso

Se nada funcionar:

```bash
# 1. Fazer backup do banco
cp database/lanch.db database/lanch.db.backup

# 2. Ver todos os logs
sudo journalctl -u lanch --no-pager | tail -100
tail -50 logs/*.log

# 3. Executar health check
python scripts/health_check.py

# 4. Validar ambiente
python scripts/validate_env.py

# 5. Testar em modo development
DEBUG=True python backend/main.py
```

## 📞 Obter Ajuda

1. Verificar logs primeiro
2. Executar health_check.py
3. Consultar este guia
4. Procurar no README.md
5. Verificar issues no repositório
