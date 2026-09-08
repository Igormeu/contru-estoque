-- ==============================================================================
-- CONTRU ESTOQUE - DDL SCHEMA PARA SUPABASE (POSTGRESQL 15+)
-- Execute este script no SQL Editor do seu projeto Supabase se preferir 
-- criar as tabelas manualmente (ou deixe a aplicação criar automaticamente via SQLAlchemy)
-- ==============================================================================

-- 1. PERFIS E USUÁRIOS
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    permissions JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    role_id INTEGER REFERENCES roles(id) ON DELETE RESTRICT,
    avatar VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. CATEGORIAS, LOCALIZAÇÕES E UNIDADES
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description VARCHAR(255),
    icon VARCHAR(50) DEFAULT 'tag',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(50) DEFAULT 'Almoxarifado',
    description VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS units (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(50) NOT NULL
);

-- 3. PRODUTOS, ESTOQUE E PREÇOS
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(180) NOT NULL,
    description TEXT,
    category_id INTEGER REFERENCES categories(id) ON DELETE RESTRICT,
    subcategory VARCHAR(100),
    unit_id INTEGER REFERENCES units(id) ON DELETE RESTRICT,
    location_id INTEGER REFERENCES locations(id) ON DELETE SET NULL,
    min_stock NUMERIC(12,2) DEFAULT 10.0 NOT NULL,
    max_stock NUMERIC(12,2) DEFAULT 100.0 NOT NULL,
    image_url VARCHAR(500),
    pdv_code VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS stock (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    quantity NUMERIC(12,2) DEFAULT 0.0 NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prices (
    id SERIAL PRIMARY KEY,
    product_id INTEGER UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    cost_price NUMERIC(12,2) DEFAULT 0.0 NOT NULL,
    sale_price NUMERIC(12,2) DEFAULT 0.0 NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. MOVIMENTAÇÕES E AJUSTES DE ESTOQUE
CREATE TABLE IF NOT EXISTS stock_movements (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE RESTRICT,
    movement_type VARCHAR(30) NOT NULL, -- ENTRADA, SAIDA, AJUSTE, INVENTARIO, PDV_VENDA
    quantity NUMERIC(12,2) NOT NULL,
    previous_balance NUMERIC(12,2) NOT NULL,
    new_balance NUMERIC(12,2) NOT NULL,
    unit_price NUMERIC(12,2) DEFAULT 0.0,
    total_value NUMERIC(12,2) DEFAULT 0.0,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    user_name VARCHAR(120),
    origin_destination VARCHAR(150),
    document_ref VARCHAR(100),
    reason_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS stock_adjustments (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE RESTRICT,
    movement_id INTEGER REFERENCES stock_movements(id) ON DELETE CASCADE,
    previous_quantity NUMERIC(12,2) NOT NULL,
    new_quantity NUMERIC(12,2) NOT NULL,
    diff_quantity NUMERIC(12,2) NOT NULL,
    justification TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. HISTÓRICO DE PREÇOS
CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE RESTRICT,
    previous_cost_price NUMERIC(12,2) DEFAULT 0.0,
    new_cost_price NUMERIC(12,2) DEFAULT 0.0,
    previous_sale_price NUMERIC(12,2) DEFAULT 0.0,
    new_sale_price NUMERIC(12,2) DEFAULT 0.0,
    reason VARCHAR(255) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    user_name VARCHAR(120),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. INVENTÁRIOS
CREATE TABLE IF NOT EXISTS inventories (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(150) NOT NULL,
    type VARCHAR(50) DEFAULT 'COMPLETO',
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    location_id INTEGER REFERENCES locations(id) ON DELETE SET NULL,
    status VARCHAR(30) DEFAULT 'EM_ANDAMENTO',
    notes TEXT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    user_name VARCHAR(120),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS inventory_items (
    id SERIAL PRIMARY KEY,
    inventory_id INTEGER REFERENCES inventories(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE RESTRICT,
    system_quantity NUMERIC(12,2) DEFAULT 0.0 NOT NULL,
    counted_quantity NUMERIC(12,2) DEFAULT 0.0 NOT NULL,
    diff_quantity NUMERIC(12,2) DEFAULT 0.0 NOT NULL,
    diff_percent NUMERIC(12,2) DEFAULT 0.0 NOT NULL,
    cost_price NUMERIC(12,2) DEFAULT 0.0 NOT NULL,
    diff_value NUMERIC(12,2) DEFAULT 0.0 NOT NULL,
    notes VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. AUDITORIA
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    user_name VARCHAR(120),
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(50),
    description VARCHAR(255) NOT NULL,
    before_data JSONB,
    after_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. INTEGRAÇÃO COM PDV
CREATE TABLE IF NOT EXISTS pdv_integrations (
    id SERIAL PRIMARY KEY,
    pdv_system_name VARCHAR(100) DEFAULT 'PDV Frente de Caixa',
    status VARCHAR(50) DEFAULT 'AGUARDANDO_CONEXAO',
    last_sync_at TIMESTAMP WITH TIME ZONE,
    pending_items_count INTEGER DEFAULT 0,
    pending_movements_count INTEGER DEFAULT 0,
    api_endpoint VARCHAR(255) DEFAULT '/api/pdv/sync',
    webhook_url VARCHAR(255),
    config_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ÍNDICES DE PERFORMANCE
CREATE INDEX IF NOT EXISTS idx_products_code ON products(code);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_movements_created ON stock_movements(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_movements_type ON stock_movements(movement_type);
CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at DESC);
