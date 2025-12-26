# LANCH - Arquitetura do Sistema

Diagramas e documentação da arquitetura do sistema LANCH.

## 📐 Visão Geral da Arquitetura

```mermaid
graph TB
    subgraph "Frontend - SPA"
        UI[Interface HTML/CSS/JS]
        SW[Service Worker PWA]
        Charts[Chart.js Visualizations]
    end
    
    subgraph "Backend - FastAPI"
        API[FastAPI Application]
        Auth[Autenticação JWT]
        Routes[Routers]
        Services[Business Logic]
        Middleware[Middleware Layer]
    end
    
    subgraph "Camada de Dados"
        DB[(SQLite Database)]
        Backups[(Backup Files)]
        Exports[(Export Files)]
        Logs[(Log Files)]
    end
    
    subgraph "Utilitários"
        Scripts[Maintenance Scripts]
        Monitoring[Health Check / Alerts]
    end
    
    UI --> API
    SW -.-> UI
    Charts --> UI
    
    API --> Auth
    API --> Routes
    API --> Middleware
    Routes --> Services
    Services --> DB
    
    Services --> Backups
    Services --> Exports
    Services --> Logs
    
    Scripts --> DB
    Scripts --> Backups
    Monitoring --> API
    Monitoring -->|Email Alerts| Admin[Administradores]
```

## 🏗️ Arquitetura em Camadas

```mermaid
graph LR
    subgraph "Presentation Layer"
        A[HTML/CSS]
        B[JavaScript]
        C[PWA]
    end
    
    subgraph "API Layer"
        D[FastAPI]
        E[Routers]
        F[Middleware]
    end
    
    subgraph "Business Layer"
        G[Services]
        H[Validators]
        I[Utilities]
    end
    
    subgraph "Data Layer"
        J[SQLAlchemy ORM]
        K[Database]
        L[File System]
    end
    
    A & B & C --> D
    D --> E & F
    E --> G
    G --> H & I
    G --> J
    J --> K
    G --> L
```

## 📊 Fluxo de Autenticação

```mermaid
sequenceDiagram
    participant U as Usuário
    participant F as Frontend
    participant A as API /auth/login
    participant M as Middleware
    participant DB as Database
    
    U->>F: Digite credenciais
    F->>A: POST /auth/login
    A->>M: Rate Limit Check
    M-->>A: OK
    A->>DB: Buscar usuário
    DB-->>A: Dados do usuário
    A->>A: Validar senha (bcrypt)
    A->>A: Gerar JWT token
    A-->>F: {access_token, user_data}
    F->>F: Armazenar token
    F-->>U: Redirecionar para dashboard
    
    Note over F,A: Requests subsequentes incluem token no header
    
    F->>A: GET /pedidos (+ Bearer token)
    A->>M: Validar JWT
    M-->>A: Token válido + user data
    A->>DB: Buscar pedidos
    DB-->>A: Lista de pedidos
    A-->>F: Dados protegidos
```

## 🛒 Fluxo de Criação de Pedido

```mermaid
stateDiagram-v2
    [*] --> SelecionaTipo: Novo Pedido
    
    SelecionaTipo --> IdentificaFunc: Tipo: Funcionário
    SelecionaTipo --> SelecionaProdutos: Tipo: Paciente
    
    IdentificaFunc --> ValidaLimite: Busca por Matrícula/CPF
    ValidaLimite --> SelecionaProdutos: Limite OK
    ValidaLimite --> [*]: Limite Excedido
    
    SelecionaProdutos --> SelecionaPagamento: Itens Adicionados
    
    SelecionaPagamento --> FinalizaPedido: Paciente: PIX/Cartão/Dinheiro
    SelecionaPagamento --> FinalizaPedido: Funcionário: Convênio
    
    FinalizaPedido --> AtualizaConsumo: Pedido Criado
    AtualizaConsumo --> NotificaCozinha: Consumo Atualizado
    NotificaCozinha --> [*]: Pedido na Fila
```

## 🔄 Fluxo de Status do Pedido (Cozinha)

```mermaid
stateDiagram-v2
    [*] --> PENDENTE: Pedido Criado
    PENDENTE --> PREPARANDO: Cozinha Aceita
    PREPARANDO --> PRONTO: Preparo Completo
    PRONTO --> ENTREGUE: Cliente Retira
    
    PENDENTE --> CANCELADO: Admin Cancela
    PREPARANDO --> CANCELADO: Problema
    
    ENTREGUE --> [*]
    CANCELADO --> [*]
```

## 💾 Arquitetura de Backup

```mermaid
graph LR
    subgraph "Triggers"
        A[Manual via /admin/backup]
        B[Agendado Diário 3h]
        C[Antes de Updates]
    end
    
    subgraph "Backup Service"
        D[Create Backup]
        E[Compress Optional]
        F[Rotate Old 30d]
    end
    
    subgraph "Storage"
        G[(backups/ Directory)]
        H[Local Backups]
        I[Remote Sync Optional]
    end
    
    subgraph "Monitoring"
        J[Verify Integrity]
        K[Email Alerts on Failure]
    end
    
    A & B & C --> D
    D --> E
    E --> F
    F --> G
    G --> H
    H -.-> I
    
    D --> J
    J -->|Falha| K
```

## 🗄️ Modelo de Dados Simplificado

```mermaid
erDiagram
    usuarios ||--o{ pedidos : cria
    usuarios ||--o{ competencias : fecha
    funcionarios ||--o{ pedidos : consome
    funcionarios ||--o{ consumos_mensais : acumula
    categorias ||--o{ produtos : contem
    produtos ||--o{ itens_pedido : vendido_como
    pedidos ||--|{ itens_pedido : contem
    competencias ||--o{ consumos_mensais : periodo
    competencias ||--o{ pedidos : registrados_em
    
    usuarios {
        int id PK
        string username UK
        string password_hash
        string perfil
        boolean ativo
    }
    
    funcionarios {
        int id PK
        string matricula UK
        string cpf UK
        string nome
        decimal limite_mensal
    }
    
    pedidos {
        int id PK
        string numero UK
        string tipo_cliente
        int funcionario_id FK
        decimal valor_total
        string status
        string forma_pagamento
    }
    
    produtos {
        int id PK
        string nome
        int categoria_id FK
        decimal preco
    }
    
    competencias {
        int id PK
        int ano
        int mes
        string status
    }
```

## 🔐 Camadas de Segurança

```mermaid
graph TB
    subgraph "Frontend Security"
        A[Input Sanitization]
        B[Client Validation]
        C[HTTPS Only]
    end
    
    subgraph "Network Security"
        D[CORS Policy]
        E[Rate Limiting]
        F[Nginx Firewall]
    end
    
    subgraph "Application Security"
        G[JWT Authentication]
        H[RBAC Authorization]
        I[Password Hashing bcrypt]
    end
    
    subgraph "Data Security"
        J[SQL Injection Protection ORM]
        K[Audit Logging]
        L[Encrypted Backups Optional]
    end
    
    A & B & C --> D
    D & E & F --> G
    G & H & I --> J
    J & K & L --> M[Protected Data]
```

## 📈 Fluxo de Monitoramento

```mermaid
sequenceDiagram
    participant Cron as Cron Job
    participant HC as Health Check Script
    participant API as API Server
    participant DB as Database
    participant Email as Email Service
    participant Admin as Administrador
    
    Cron->>HC: Execute a cada 15min
    
    HC->>API: GET /health
    alt API Respondendo
        API-->>HC: 200 OK
    else API Não Responde
        HC->>Email: send_api_down_alert()
        Email->>Admin: 🚨 API Down!
    end
    
    HC->>DB: Check database
    alt Database OK
        DB-->>HC: OK
    else Database Error
        HC->>Email: send_database_error_alert()
        Email->>Admin: ⚠️ DB Error!
    end
    
    HC->>HC: Check disk space
    alt Espaço < 100MB
        HC->>Email: send_disk_space_alert()
        Email->>Admin: 💾 Low Disk!
    end
    
    HC->>HC: Check backups
    alt Backup > 7 dias
        HC->>Email: send_backup_warning()
        Email->>Admin: 📦 Old Backup!
    end
```

## 🌐 Deploy Architecture (Produção)

```mermaid
graph TB
    subgraph "Internet"
        Users[Usuários]
    end
    
    subgraph "Edge Layer"
        DNS[DNS]
        SSL[Let's Encrypt SSL]
    end
    
    subgraph "Server Ubuntu/Debian"
        subgraph "Nginx Reverse Proxy"
            RP[Nginx]
            Cache[Static Cache]
        end
        
        subgraph "Application"
            UV[Uvicorn/Gunicorn]
            App[FastAPI App]
        end
        
        subgraph "Data"
            SQLite[(SQLite DB)]
            Files[Static Files]
        end
        
        subgraph "Services"
            Systemd[Systemd Service]
            Cron[Cron Jobs]
        end
    end
    
    subgraph "Monitoring"
        Logs[Journald Logs]
        Alerts[Email Alerts]
    end
    
    Users --> DNS
    DNS --> SSL
    SSL --> RP
    RP --> Cache
    RP --> UV
    UV --> App
    App --> SQLite
    RP --> Files
    
    Systemd -.-> UV
    Cron -.-> App
    
    App --> Logs
    Cron --> Alerts
```

## 🔄 CI/CD Flow (Recomendado)

```mermaid
graph LR
    A[Git Push] --> B[Run Tests]
    B --> C{Tests Pass?}
    C -->|Yes| D[Build Docker]
    C -->|No| E[Notify Developer]
    D --> F[Tag Version]
    F --> G[Deploy to Staging]
    G --> H{Manual Approval}
    H -->|Approved| I[Deploy to Production]
    H -->|Rejected| E
    I --> J[Health Check]
    J --> K{Healthy?}
    K -->|Yes| L[Complete]
    K -->|No| M[Rollback]
    M --> E
```

## 📱 Progressive Web App (PWA)

```mermaid
graph TB
    subgraph "Service Worker"
        SW[Service Worker]
        Cache[Cache Storage]
    end
    
    subgraph "App Shell"
        HTML[index.html]
        CSS[Styles]
        JS[JavaScript]
    end
    
    subgraph "Dynamic Content"
        API[API Calls]
        Data[JSON Data]
    end
    
    SW --> Cache
    Cache --> HTML
    Cache --> CSS
    Cache --> JS
    
    SW -.->|Network First| API
    API -.->|Cache Then Network| Data
    
    SW -->|Offline Fallback| Cache
```

## 🎯 Componentes por Responsabilidade

### Frontend

- **UI Components**: HTML5, CSS3 (Vanilla, Dark Mode)
- **State Management**: JavaScript (sem framework)
- **Visualização**: Chart.js
- **PWA**: Service Worker, Manifest
- **Validação**: Client-side validators

### Backend

- **Framework**: FastAPI (Python)
- **ORM**: SQLAlchemy
- **Autenticação**: JWT (python-jose)
- **Validação**: Pydantic
- **Documentação**: OpenAPI/Swagger automático

### Infraestrutura

- **Web Server**: Nginx (reverse proxy)
- **App Server**: Uvicorn/Gunicorn
- **Database**: SQLite (ou PostgreSQL)
- **Process Manager**: Systemd
- **Scheduler**: Cron

### Observabilidade

- **Logs**: Python logging + Journald
- **Metrics**: Health check endpoint
- **Alerts**: Email service
- **Backup**: Automated daily
