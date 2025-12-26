# LANCH - Guia de Deploy em Produção

Guia completo para fazer deploy do sistema LANCH em ambiente de produção.

## 📋 Checklist Pré-Deploy

Antes de fazer deploy, certifique-se de:

- [ ] Arquivo `.env` configurado com SECRET_KEY forte
- [ ] DEBUG=False no arquivo .env
- [ ] ALLOWED_ORIGINS configurado com domínios corretos (sem localhost)
- [ ] Servidor Linux configurado (Ubuntu 20.04+ ou Debian 11+ recomendado)
- [ ] Acesso root ou sudo no servidor
- [ ] Domínio configurado e apontando para servidor
- [ ] SSL/TLS configurado (Let's Encrypt recomendado)

## 🖥️ Configuração do Servidor

### 1. Atualizar Sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Instalar Dependências

```bash
# Python 3.10+
sudo apt install python3.10 python3.10-venv python3-pip -y

# Nginx (reverse proxy)
sudo apt install nginx -y

# Certbot (SSL gratuito)
sudo apt install certbot python3-certbot-nginx -y

# Git
sudo apt install git -y
```

### 3. Criar Usuário do Sistema

```bash
sudo useradd -r -m -s /bin/bash lanch
sudo usermod -aG www-data lanch
```

## 📂 Deploy da Aplicação

### 1. Clonar Repositório

```bash
cd /opt
sudo git clone <seu-repositorio> lanch
sudo chown -R lanch:lanch /opt/lanch
```

### 2. Configurar Ambiente Virtual

```bash
cd /opt/lanch/backend
sudo -u lanch python3 -m venv /opt/lanch/.venv
sudo -u lanch /opt/lanch/.venv/bin/pip install -r requirements.txt
```

### 3. Configurar .env

```bash
sudo -u lanch cp /opt/lanch/.env.example /opt/lanch/.env
sudo -u lanch nano /opt/lanch/.env
```

**Configurações críticas**:

```ini
SECRET_KEY=<gerar com: python -c "import secrets; print(secrets.token_urlsafe(32))">
DEBUG=False
ALLOWED_ORIGINS=https://seu-dominio.com.br
DATABASE_URL=sqlite:///../database/lanch.db
LOG_LEVEL=INFO
```

### 4. Validar Configuração

```bash
cd /opt/lanch
sudo -u lanch /opt/lanch/.venv/bin/python scripts/validate_env.py
```

### 5. Inicializar Banco de Dados

```bash
cd /opt/lanch/backend
sudo -u lanch /opt/lanch/.venv/bin/python -c "from database import init_db; init_db()"
```

## 🔧 Configurar Systemd Service

### 1. Criar Arquivo de Serviço

```bash
sudo nano /etc/systemd/system/lanch.service
```

```ini
[Unit]
Description=LANCH - Sistema de Lanchonete Hospitalar
After=network.target

[Service]
Type=simple
User=lanch
Group=lanch
WorkingDirectory=/opt/lanch/backend
Environment="PATH=/opt/lanch/.venv/bin"
EnvironmentFile=/opt/lanch/.env
ExecStart=/opt/lanch/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Ativar e Iniciar Serviço

```bash
sudo systemctl daemon-reload
sudo systemctl enable lanch
sudo systemctl start lanch
sudo systemctl status lanch
```

## 🌐 Configurar Nginx

### 1. Criar Configuração

```bash
sudo nano /etc/nginx/sites-available/lanch
```

```nginx
server {
    listen 80;
    server_name seu-dominio.com.br;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com.br;
    
    # SSL Configuration (will be added by Certbot)
    ssl_certificate /etc/letsencrypt/live/seu-dominio.com.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com.br/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Frontend (static files)
    location / {
        root /opt/lanch/frontend;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript;
    
    # Client max body size
    client_max_body_size 10M;
}
```

### 2. Ativar Site

```bash
sudo ln -s /etc/nginx/sites-available/lanch /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔒 Configurar SSL (Let's Encrypt)

```bash
sudo certbot --nginx -d seu-dominio.com.br
```

Siga as instruções do Certbot. Escolha opção para redirecionar HTTP para HTTPS.

### Renovação Automática

```bash
# Testar renovação
sudo certbot renew --dry-run

# Certbot adiciona cron automaticamente em /etc/cron.d/certbot
```

## 🔥 Configurar Firewall

```bash
# Permitir SSH, HTTP e HTTPS
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

## 💾 Configurar Backups Automáticos

### 1. Criar Script de Backup Diário

```bash
sudo nano /etc/cron.daily/lanch-backup
```

```bash
#!/bin/bash
cd /opt/lanch
/opt/lanch/.venv/bin/python scripts/backup_now.py >> /var/log/lanch-backup.log 2>&1
```

```bash
sudo chmod +x /etc/cron.daily/lanch-backup
```

### 2. Configurar Backup Remoto (Opcional)

```bash
# Instalar rclone para backup remoto (Google Drive, S3, etc)
sudo apt install rclone -y
rclone config  # Configurar storage remoto
```

## 📊 Monitoramento

### Logs da Aplicação

```bash
# Ver logs do serviço
sudo journalctl -u lanch -f

# Logs da aplicação
tail -f /opt/lanch/logs/*.log

# Logs do Nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Health Check

```bash
# Executar health check
cd /opt/lanch
/opt/lanch/.venv/bin/python scripts/health_check.py
```

## 🔄 Atualizações

### Atualizar Aplicação

```bash
cd /opt/lanch
sudo -u lanch git pull
sudo -u lanch /opt/lanch/.venv/bin/pip install -r backend/requirements.txt
sudo systemctl restart lanch
```

### Rollback

```bash
cd /opt/lanch
sudo -u lanch git log --oneline -n 5  # Ver commits
sudo -u lanch git checkout <commit-hash>
sudo systemctl restart lanch
```

## 🆘 Troubleshooting

Ver [TROUBLESHOOTING.md](TROUBLESHOOTING.md) para problemas comuns.

## 📈 Performance

### Usar Gunicorn ao invés de Uvicorn

Para melhor performance em produção:

```bash
pip install gunicorn
```

Alterar ExecStart no systemd service:

```ini
ExecStart=/opt/lanch/.venv/bin/gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
```

### Tuning do Nginx

```nginx
# Adicionar em http block em /etc/nginx/nginx.conf
worker_processes auto;
worker_connections 1024;
keepalive_timeout 65;
```

## 🔐 Segurança Adicional

### Fail2ban (Proteção contra força bruta)

```bash
sudo apt install fail2ban -y
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local
# Configurar bantime, findtime, maxretry
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Atualizações Automáticas de Segurança

```bash
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

## ✅ Checklist Pós-Deploy

- [ ] Aplicação acessível via HTTPS
- [ ] Certificado SSL válido
- [ ] Login funcionando corretamente
- [ ] Backup automático configurado
- [ ] Logs sendo gerados corretamente
- [ ] Firewall configurado
- [ ] Monitoramento ativo
- [ ] Senha padrão do admin alterada
- [ ] Documentação atualizada com dados do servidor
