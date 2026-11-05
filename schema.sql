CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,
    sku VARCHAR(40) NOT NULL,
    name VARCHAR(120) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'new',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_status
        CHECK (status IN ('new', 'in_progress', 'done'))
);

INSERT INTO products (sku, name, status) VALUES
('SKU-1001', 'Ноутбук Lenovo ThinkPad E15', 'new'),
('SKU-1002', 'Миша бездротова Logitech M185', 'in_progress'),
('SKU-1003', 'Монітор Dell 24"', 'done');
