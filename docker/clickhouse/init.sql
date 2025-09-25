-- ClickHouse initialization script
-- Creates sample tables with test data

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS testdb;

USE testdb;

-- Create users table
CREATE TABLE IF NOT EXISTS users
(
    user_id UInt32,
    username String,
    email String,
    first_name String,
    last_name String,
    created_at DateTime,
    is_active UInt8,
    account_type Enum8('free' = 1, 'premium' = 2, 'enterprise' = 3)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (user_id, created_at)
SETTINGS index_granularity = 8192;

-- Insert sample users
INSERT INTO users VALUES
    (1, 'john_doe', 'john@example.com', 'John', 'Doe', '2024-01-15 10:00:00', 1, 'premium'),
    (2, 'jane_smith', 'jane@example.com', 'Jane', 'Smith', '2024-01-20 11:30:00', 1, 'free'),
    (3, 'bob_wilson', 'bob@example.com', 'Bob', 'Wilson', '2024-02-01 09:15:00', 1, 'enterprise'),
    (4, 'alice_brown', 'alice@example.com', 'Alice', 'Brown', '2024-02-10 14:20:00', 1, 'premium'),
    (5, 'charlie_davis', 'charlie@example.com', 'Charlie', 'Davis', '2024-02-15 16:45:00', 0, 'free'),
    (6, 'eva_garcia', 'eva@example.com', 'Eva', 'Garcia', '2024-03-01 08:00:00', 1, 'premium'),
    (7, 'frank_miller', 'frank@example.com', 'Frank', 'Miller', '2024-03-05 10:30:00', 1, 'enterprise'),
    (8, 'grace_lee', 'grace@example.com', 'Grace', 'Lee', '2024-03-10 12:00:00', 1, 'free'),
    (9, 'henry_wang', 'henry@example.com', 'Henry', 'Wang', '2024-03-15 13:30:00', 1, 'premium'),
    (10, 'iris_chen', 'iris@example.com', 'Iris', 'Chen', '2024-03-20 15:00:00', 1, 'enterprise');

-- Create orders table
CREATE TABLE IF NOT EXISTS orders
(
    order_id UInt32,
    user_id UInt32,
    product_id UInt32,
    quantity UInt16,
    total_amount Decimal(10, 2),
    order_date DateTime,
    status Enum8('pending' = 1, 'processing' = 2, 'shipped' = 3, 'delivered' = 4, 'cancelled' = 5),
    shipping_address String
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(order_date)
ORDER BY (order_date, order_id)
SETTINGS index_granularity = 8192;

-- Insert sample orders
INSERT INTO orders VALUES
    (1001, 1, 101, 2, 59.98, '2024-03-01 10:00:00', 'delivered', '123 Main St, New York, NY'),
    (1002, 2, 102, 1, 149.99, '2024-03-02 11:30:00', 'shipped', '456 Oak Ave, Los Angeles, CA'),
    (1003, 3, 103, 3, 89.97, '2024-03-03 14:20:00', 'processing', '789 Pine Rd, Chicago, IL'),
    (1004, 1, 104, 1, 299.99, '2024-03-04 09:15:00', 'delivered', '123 Main St, New York, NY'),
    (1005, 4, 105, 2, 199.98, '2024-03-05 16:30:00', 'pending', '321 Elm St, Houston, TX'),
    (1006, 5, 101, 1, 29.99, '2024-03-06 10:00:00', 'cancelled', '654 Maple Dr, Phoenix, AZ'),
    (1007, 6, 102, 2, 299.98, '2024-03-07 11:45:00', 'delivered', '987 Cedar Ln, Philadelphia, PA'),
    (1008, 7, 103, 1, 29.99, '2024-03-08 13:00:00', 'shipped', '147 Birch Ave, San Antonio, TX'),
    (1009, 8, 104, 3, 899.97, '2024-03-09 14:30:00', 'processing', '258 Spruce St, San Diego, CA'),
    (1010, 9, 105, 1, 99.99, '2024-03-10 15:45:00', 'delivered', '369 Willow Rd, Dallas, TX');

-- Create products table
CREATE TABLE IF NOT EXISTS products
(
    product_id UInt32,
    product_name String,
    category String,
    price Decimal(10, 2),
    stock_quantity UInt32,
    manufacturer String,
    created_at DateTime,
    is_available UInt8
)
ENGINE = MergeTree()
ORDER BY product_id
SETTINGS index_granularity = 8192;

-- Insert sample products
INSERT INTO products VALUES
    (101, 'Wireless Mouse', 'Electronics', 29.99, 150, 'TechCorp', '2024-01-01 00:00:00', 1),
    (102, 'Mechanical Keyboard', 'Electronics', 149.99, 75, 'KeyMaster', '2024-01-05 00:00:00', 1),
    (103, 'USB-C Hub', 'Electronics', 29.99, 200, 'ConnectPro', '2024-01-10 00:00:00', 1),
    (104, '27-inch Monitor', 'Electronics', 299.99, 50, 'ViewTech', '2024-01-15 00:00:00', 1),
    (105, 'Webcam HD', 'Electronics', 99.99, 100, 'CamPro', '2024-01-20 00:00:00', 1),
    (106, 'Laptop Stand', 'Accessories', 49.99, 120, 'DeskPro', '2024-02-01 00:00:00', 1),
    (107, 'Bluetooth Speaker', 'Audio', 79.99, 80, 'SoundWave', '2024-02-05 00:00:00', 1),
    (108, 'Power Bank 20000mAh', 'Accessories', 39.99, 150, 'PowerMax', '2024-02-10 00:00:00', 1),
    (109, 'Smart Watch', 'Wearables', 199.99, 60, 'TimeTech', '2024-02-15 00:00:00', 1),
    (110, 'Wireless Earbuds', 'Audio', 129.99, 90, 'AudioPro', '2024-02-20 00:00:00', 1);

-- Create inventory table
CREATE TABLE IF NOT EXISTS inventory
(
    inventory_id UInt32,
    product_id UInt32,
    warehouse_id UInt16,
    quantity_available UInt32,
    quantity_reserved UInt32,
    last_restocked DateTime,
    reorder_level UInt32,
    reorder_quantity UInt32
)
ENGINE = MergeTree()
ORDER BY (warehouse_id, product_id)
SETTINGS index_granularity = 8192;

-- Insert sample inventory data
INSERT INTO inventory VALUES
    (1, 101, 1, 50, 5, '2024-03-01 08:00:00', 20, 100),
    (2, 102, 1, 30, 2, '2024-03-02 09:00:00', 15, 50),
    (3, 103, 1, 75, 10, '2024-03-03 10:00:00', 30, 100),
    (4, 104, 1, 20, 3, '2024-03-04 11:00:00', 10, 30),
    (5, 105, 1, 40, 5, '2024-03-05 12:00:00', 20, 60),
    (6, 101, 2, 45, 3, '2024-03-01 08:00:00', 20, 100),
    (7, 102, 2, 25, 1, '2024-03-02 09:00:00', 15, 50),
    (8, 103, 2, 60, 8, '2024-03-03 10:00:00', 30, 100),
    (9, 104, 2, 18, 2, '2024-03-04 11:00:00', 10, 30),
    (10, 105, 2, 35, 4, '2024-03-05 12:00:00', 20, 60);

-- Create analytics_events table
CREATE TABLE IF NOT EXISTS analytics_events
(
    event_id UUID,
    user_id UInt32,
    event_type String,
    event_timestamp DateTime,
    page_url String,
    session_id String,
    device_type Enum8('desktop' = 1, 'mobile' = 2, 'tablet' = 3),
    browser String,
    country String,
    properties String  -- JSON string for additional properties
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_timestamp)
ORDER BY (event_timestamp, user_id, event_id)
SETTINGS index_granularity = 8192;

-- Insert sample analytics events
INSERT INTO analytics_events VALUES
    (generateUUIDv4(), 1, 'page_view', '2024-03-20 10:00:00', '/home', 'session_001', 'desktop', 'Chrome', 'USA', '{"referrer": "google.com"}'),
    (generateUUIDv4(), 1, 'button_click', '2024-03-20 10:01:00', '/products', 'session_001', 'desktop', 'Chrome', 'USA', '{"button": "add_to_cart"}'),
    (generateUUIDv4(), 2, 'page_view', '2024-03-20 10:05:00', '/home', 'session_002', 'mobile', 'Safari', 'UK', '{"referrer": "direct"}'),
    (generateUUIDv4(), 3, 'form_submit', '2024-03-20 10:10:00', '/checkout', 'session_003', 'tablet', 'Firefox', 'Canada', '{"form": "payment"}'),
    (generateUUIDv4(), 4, 'page_view', '2024-03-20 10:15:00', '/about', 'session_004', 'desktop', 'Edge', 'Germany', '{"referrer": "facebook.com"}'),
    (generateUUIDv4(), 5, 'search', '2024-03-20 10:20:00', '/search', 'session_005', 'mobile', 'Chrome', 'France', '{"query": "wireless mouse"}'),
    (generateUUIDv4(), 6, 'page_view', '2024-03-20 10:25:00', '/contact', 'session_006', 'desktop', 'Chrome', 'Japan', '{"referrer": "twitter.com"}'),
    (generateUUIDv4(), 7, 'video_play', '2024-03-20 10:30:00', '/tutorial', 'session_007', 'mobile', 'Safari', 'Australia', '{"video_id": "tutorial_01"}'),
    (generateUUIDv4(), 8, 'page_view', '2024-03-20 10:35:00', '/blog', 'session_008', 'tablet', 'Chrome', 'Brazil', '{"referrer": "linkedin.com"}'),
    (generateUUIDv4(), 9, 'download', '2024-03-20 10:40:00', '/resources', 'session_009', 'desktop', 'Firefox', 'India', '{"file": "guide.pdf"}');

-- Create a view for order summary
CREATE VIEW IF NOT EXISTS order_summary AS
SELECT
    o.order_id,
    o.order_date,
    u.username,
    p.product_name,
    o.quantity,
    o.total_amount,
    o.status
FROM orders o
JOIN users u ON o.user_id = u.user_id
JOIN products p ON o.product_id = p.product_id;