#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create sample tables for testing Text-to-SQL functionality
    
    CREATE TABLE IF NOT EXISTS customers (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        city VARCHAR(50),
        country VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        customer_id INTEGER REFERENCES customers(id),
        order_date DATE DEFAULT CURRENT_DATE,
        total_amount DECIMAL(10,2),
        status VARCHAR(20) DEFAULT 'pending'
    );

    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        price DECIMAL(10,2),
        category VARCHAR(50),
        stock_quantity INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS order_items (
        id SERIAL PRIMARY KEY,
        order_id INTEGER REFERENCES orders(id),
        product_id INTEGER REFERENCES products(id),
        quantity INTEGER NOT NULL,
        unit_price DECIMAL(10,2)
    );

    -- Insert sample data
    INSERT INTO customers (name, email, city, country) VALUES
        ('John Doe', 'john.doe@email.com', 'New York', 'USA'),
        ('Jane Smith', 'jane.smith@email.com', 'London', 'UK'),
        ('Bob Johnson', 'bob.johnson@email.com', 'Toronto', 'Canada'),
        ('Alice Brown', 'alice.brown@email.com', 'Sydney', 'Australia'),
        ('Charlie Wilson', 'charlie.wilson@email.com', 'New York', 'USA')
    ON CONFLICT (email) DO NOTHING;

    INSERT INTO products (name, description, price, category, stock_quantity) VALUES
        ('Laptop', 'High-performance laptop', 999.99, 'Electronics', 50),
        ('Mouse', 'Wireless optical mouse', 29.99, 'Electronics', 200),
        ('Keyboard', 'Mechanical keyboard', 89.99, 'Electronics', 100),
        ('Monitor', '24-inch LCD monitor', 299.99, 'Electronics', 75),
        ('Desk Chair', 'Ergonomic office chair', 199.99, 'Furniture', 30)
    ON CONFLICT DO NOTHING;

    INSERT INTO orders (customer_id, order_date, total_amount, status) VALUES
        (1, '2024-01-15', 1099.98, 'completed'),
        (2, '2024-01-16', 329.98, 'completed'),
        (3, '2024-01-17', 89.99, 'pending'),
        (4, '2024-01-18', 599.98, 'shipped'),
        (5, '2024-01-19', 29.99, 'completed')
    ON CONFLICT DO NOTHING;

    INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
        (1, 1, 1, 999.99),
        (1, 2, 1, 29.99),
        (1, 3, 1, 89.99),
        (2, 4, 1, 299.99),
        (2, 2, 1, 29.99),
        (3, 3, 1, 89.99),
        (4, 1, 1, 999.99),
        (4, 5, 1, 199.99),
        (5, 2, 1, 29.99)
    ON CONFLICT DO NOTHING;

    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_customers_city ON customers(city);
    CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
    CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
    CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
    CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
    CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);

    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

    \echo 'Sample database initialized successfully!'
EOSQL