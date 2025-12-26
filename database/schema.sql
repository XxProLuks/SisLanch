-- ============================================================================
-- LANCH - Sistema de Lanchonete Hospitalar
-- Database Schema - SQLite
-- Created: 2024-12-22
-- ============================================================================

-- ============================================================================
-- TABELAS PRINCIPAIS
-- ============================================================================

-- Usuários do sistema (Admin, Atendente, Cozinha)
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    nome TEXT NOT NULL,
    perfil TEXT NOT NULL CHECK (perfil IN ('ADMIN', 'ATENDENTE', 'COZINHA')),
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Categorias de produtos
CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Produtos da lanchonete
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    categoria_id INTEGER NOT NULL,
    preco DECIMAL(10,2) NOT NULL CHECK (preco >= 0),
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
);

-- Funcionários do hospital (consumo via convênio)
CREATE TABLE IF NOT EXISTS funcionarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula TEXT NOT NULL UNIQUE,
    cpf TEXT NOT NULL UNIQUE,
    nome TEXT NOT NULL,
    setor TEXT NOT NULL,
    centro_custo TEXT NOT NULL,
    limite_mensal DECIMAL(10,2) NOT NULL DEFAULT 500.00 CHECK (limite_mensal >= 0),
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Competências mensais para fechamento
CREATE TABLE IF NOT EXISTS competencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ano INTEGER NOT NULL,
    mes INTEGER NOT NULL CHECK (mes >= 1 AND mes <= 12),
    status TEXT NOT NULL DEFAULT 'ABERTA' CHECK (status IN ('ABERTA', 'FECHADA')),
    fechada_em DATETIME,
    fechada_por INTEGER,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ano, mes),
    FOREIGN KEY (fechada_por) REFERENCES usuarios(id)
);

-- Consumo mensal acumulado por funcionário
CREATE TABLE IF NOT EXISTS consumos_mensais (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    funcionario_id INTEGER NOT NULL,
    competencia_id INTEGER NOT NULL,
    valor_total DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(funcionario_id, competencia_id),
    FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id),
    FOREIGN KEY (competencia_id) REFERENCES competencias(id)
);

-- Pedidos (funcionários e pacientes)
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT NOT NULL UNIQUE,
    tipo_cliente TEXT NOT NULL CHECK (tipo_cliente IN ('FUNCIONARIO', 'PACIENTE')),
    funcionario_id INTEGER,
    usuario_id INTEGER NOT NULL,
    valor_total DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    status TEXT NOT NULL DEFAULT 'PENDENTE' CHECK (status IN ('PENDENTE', 'PREPARANDO', 'PRONTO', 'ENTREGUE', 'CANCELADO')),
    forma_pagamento TEXT NOT NULL CHECK (forma_pagamento IN ('CONVENIO', 'PIX', 'CARTAO', 'DINHEIRO')),
    competencia_id INTEGER,
    observacao TEXT,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (funcionario_id) REFERENCES funcionarios(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (competencia_id) REFERENCES competencias(id)
);

-- Itens do pedido
CREATE TABLE IF NOT EXISTS itens_pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL,
    produto_id INTEGER NOT NULL,
    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
    preco_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);

-- Log de auditoria
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    acao TEXT NOT NULL,
    tabela TEXT NOT NULL,
    registro_id INTEGER,
    dados_anteriores TEXT,
    dados_novos TEXT,
    ip TEXT,
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- ============================================================================
-- ÍNDICES PARA PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON produtos(categoria_id);
CREATE INDEX IF NOT EXISTS idx_produtos_ativo ON produtos(ativo);
CREATE INDEX IF NOT EXISTS idx_funcionarios_matricula ON funcionarios(matricula);
CREATE INDEX IF NOT EXISTS idx_funcionarios_cpf ON funcionarios(cpf);
CREATE INDEX IF NOT EXISTS idx_funcionarios_ativo ON funcionarios(ativo);
CREATE INDEX IF NOT EXISTS idx_competencias_ano_mes ON competencias(ano, mes);
CREATE INDEX IF NOT EXISTS idx_competencias_status ON competencias(status);
CREATE INDEX IF NOT EXISTS idx_consumos_funcionario ON consumos_mensais(funcionario_id);
CREATE INDEX IF NOT EXISTS idx_consumos_competencia ON consumos_mensais(competencia_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_tipo ON pedidos(tipo_cliente);
CREATE INDEX IF NOT EXISTS idx_pedidos_funcionario ON pedidos(funcionario_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_status ON pedidos(status);
CREATE INDEX IF NOT EXISTS idx_pedidos_competencia ON pedidos(competencia_id);
CREATE INDEX IF NOT EXISTS idx_pedidos_criado ON pedidos(criado_em);
CREATE INDEX IF NOT EXISTS idx_itens_pedido ON itens_pedido(pedido_id);
CREATE INDEX IF NOT EXISTS idx_audit_tabela ON audit_log(tabela);
CREATE INDEX IF NOT EXISTS idx_audit_criado ON audit_log(criado_em);

-- ============================================================================
-- TRIGGERS PARA AUDITORIA AUTOMÁTICA
-- ============================================================================

-- Trigger para atualizar timestamp em usuarios
CREATE TRIGGER IF NOT EXISTS trg_usuarios_update
AFTER UPDATE ON usuarios
BEGIN
    UPDATE usuarios SET atualizado_em = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger para atualizar timestamp em produtos
CREATE TRIGGER IF NOT EXISTS trg_produtos_update
AFTER UPDATE ON produtos
BEGIN
    UPDATE produtos SET atualizado_em = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger para atualizar timestamp em funcionarios
CREATE TRIGGER IF NOT EXISTS trg_funcionarios_update
AFTER UPDATE ON funcionarios
BEGIN
    UPDATE funcionarios SET atualizado_em = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger para atualizar timestamp em pedidos
CREATE TRIGGER IF NOT EXISTS trg_pedidos_update
AFTER UPDATE ON pedidos
BEGIN
    UPDATE pedidos SET atualizado_em = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Trigger para atualizar timestamp em consumos_mensais
CREATE TRIGGER IF NOT EXISTS trg_consumos_update
AFTER UPDATE ON consumos_mensais
BEGIN
    UPDATE consumos_mensais SET atualizado_em = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- ============================================================================
-- DADOS INICIAIS
-- ============================================================================

-- Usuário administrador padrão (senha: admin123)
INSERT OR IGNORE INTO usuarios (username, password_hash, nome, perfil, ativo)
VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.N0w8.y9.q3mV8i', 'Administrador', 'ADMIN', 1);

-- Categorias padrão
INSERT OR IGNORE INTO categorias (nome) VALUES ('Lanches');
INSERT OR IGNORE INTO categorias (nome) VALUES ('Bebidas');
INSERT OR IGNORE INTO categorias (nome) VALUES ('Salgados');
INSERT OR IGNORE INTO categorias (nome) VALUES ('Doces');
INSERT OR IGNORE INTO categorias (nome) VALUES ('Refeições');

-- Competência atual (Dezembro 2024)
INSERT OR IGNORE INTO competencias (ano, mes, status)
VALUES (2024, 12, 'ABERTA');

-- ============================================================================
-- VIEWS ÚTEIS
-- ============================================================================

-- View de consumo consolidado por funcionário na competência atual
CREATE VIEW IF NOT EXISTS vw_consumo_atual AS
SELECT 
    f.id AS funcionario_id,
    f.matricula,
    f.nome,
    f.setor,
    f.centro_custo,
    f.limite_mensal,
    COALESCE(cm.valor_total, 0) AS valor_consumido,
    f.limite_mensal - COALESCE(cm.valor_total, 0) AS saldo_disponivel,
    c.ano,
    c.mes
FROM funcionarios f
LEFT JOIN competencias c ON c.status = 'ABERTA'
LEFT JOIN consumos_mensais cm ON cm.funcionario_id = f.id AND cm.competencia_id = c.id
WHERE f.ativo = 1;

-- View de pedidos do dia
CREATE VIEW IF NOT EXISTS vw_pedidos_hoje AS
SELECT 
    p.id,
    p.numero,
    p.tipo_cliente,
    f.nome AS funcionario_nome,
    p.valor_total,
    p.status,
    p.forma_pagamento,
    p.criado_em,
    u.nome AS atendente
FROM pedidos p
LEFT JOIN funcionarios f ON f.id = p.funcionario_id
LEFT JOIN usuarios u ON u.id = p.usuario_id
WHERE DATE(p.criado_em) = DATE('now', 'localtime')
ORDER BY p.criado_em DESC;

-- View para tela da cozinha
CREATE VIEW IF NOT EXISTS vw_pedidos_cozinha AS
SELECT 
    p.id,
    p.numero,
    p.tipo_cliente,
    CASE 
        WHEN p.tipo_cliente = 'FUNCIONARIO' THEN f.nome
        ELSE 'Paciente/Visitante'
    END AS cliente,
    p.status,
    p.observacao,
    p.criado_em,
    GROUP_CONCAT(pr.nome || ' x' || ip.quantidade, ', ') AS itens
FROM pedidos p
LEFT JOIN funcionarios f ON f.id = p.funcionario_id
JOIN itens_pedido ip ON ip.pedido_id = p.id
JOIN produtos pr ON pr.id = ip.produto_id
WHERE p.status IN ('PENDENTE', 'PREPARANDO', 'PRONTO')
GROUP BY p.id
ORDER BY 
    CASE p.status 
        WHEN 'PENDENTE' THEN 1 
        WHEN 'PREPARANDO' THEN 2 
        WHEN 'PRONTO' THEN 3 
    END,
    p.criado_em ASC;

-- View de relatório mensal por funcionário
CREATE VIEW IF NOT EXISTS vw_relatorio_mensal AS
SELECT 
    c.ano,
    c.mes,
    f.matricula,
    f.nome,
    f.setor,
    f.centro_custo,
    COALESCE(cm.valor_total, 0) AS valor_total,
    c.status AS status_competencia
FROM competencias c
CROSS JOIN funcionarios f
LEFT JOIN consumos_mensais cm ON cm.competencia_id = c.id AND cm.funcionario_id = f.id
WHERE f.ativo = 1 OR cm.valor_total > 0
ORDER BY c.ano DESC, c.mes DESC, f.nome;
