-- MySQL Database Initialization Script
-- This script runs when the MySQL container starts for the first time

-- Create additional databases
CREATE DATABASE IF NOT EXISTS ontology_test;
CREATE DATABASE IF NOT EXISTS ontology_analytics;

-- Grant privileges to ontology_user
GRANT ALL PRIVILEGES ON ontology_dev.* TO 'ontology_user'@'%';
GRANT ALL PRIVILEGES ON ontology_test.* TO 'ontology_user'@'%';
GRANT ALL PRIVILEGES ON ontology_analytics.* TO 'ontology_user'@'%';
FLUSH PRIVILEGES;

-- Use the main development database
USE ontology_dev;

-- Create ontology-related tables
CREATE TABLE IF NOT EXISTS ontologies (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(20) DEFAULT '1.0.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    status ENUM('draft', 'published', 'archived') DEFAULT 'draft',
    INDEX idx_name (name),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ontology_nodes (
    id VARCHAR(36) PRIMARY KEY,
    ontology_id VARCHAR(36) NOT NULL,
    node_id VARCHAR(255) NOT NULL,
    node_type ENUM('class', 'property', 'instance', 'relationship') NOT NULL,
    label VARCHAR(255) NOT NULL,
    description TEXT,
    properties JSON,
    position_x DECIMAL(10,2),
    position_y DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (ontology_id) REFERENCES ontologies(id) ON DELETE CASCADE,
    UNIQUE KEY unique_node_per_ontology (ontology_id, node_id),
    INDEX idx_ontology_id (ontology_id),
    INDEX idx_node_type (node_type),
    INDEX idx_label (label)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ontology_edges (
    id VARCHAR(36) PRIMARY KEY,
    ontology_id VARCHAR(36) NOT NULL,
    edge_id VARCHAR(255) NOT NULL,
    source_node_id VARCHAR(255) NOT NULL,
    target_node_id VARCHAR(255) NOT NULL,
    edge_type ENUM('relationship', 'property', 'inheritance', 'composition', 'aggregation') NOT NULL,
    label VARCHAR(255) NOT NULL,
    relationship_type ENUM('one-to-one', 'one-to-many', 'many-to-one', 'many-to-many') DEFAULT 'one-to-many',
    description TEXT,
    properties JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (ontology_id) REFERENCES ontologies(id) ON DELETE CASCADE,
    UNIQUE KEY unique_edge_per_ontology (ontology_id, edge_id),
    INDEX idx_ontology_id (ontology_id),
    INDEX idx_source_target (source_node_id, target_node_id),
    INDEX idx_edge_type (edge_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ai_suggestions (
    id VARCHAR(36) PRIMARY KEY,
    ontology_id VARCHAR(36) NOT NULL,
    suggestion_type ENUM('ontology_class', 'property', 'relationship', 'enhancement') NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    implementation TEXT,
    status ENUM('pending', 'applied', 'rejected') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_at TIMESTAMP NULL,
    applied_by VARCHAR(100),
    FOREIGN KEY (ontology_id) REFERENCES ontologies(id) ON DELETE CASCADE,
    INDEX idx_ontology_id (ontology_id),
    INDEX idx_status (status),
    INDEX idx_suggestion_type (suggestion_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS change_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ontology_id VARCHAR(36) NOT NULL,
    change_type ENUM('ADD_NODE', 'EDIT_NODE', 'DELETE_NODE', 'CREATE_CONNECTION', 'DELETE_CONNECTION', 'APPLY_SUGGESTION') NOT NULL,
    change_data JSON,
    before_state JSON,
    after_state JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    FOREIGN KEY (ontology_id) REFERENCES ontologies(id) ON DELETE CASCADE,
    INDEX idx_ontology_id (ontology_id),
    INDEX idx_change_type (change_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert sample ontologies
INSERT INTO ontologies (id, name, description, created_by, status) VALUES
('customer-domain', 'Customer Domain Ontology', 'Ontology representing customer-related entities and relationships', 'system', 'published'),
('product-catalog', 'Product Catalog Ontology', 'Ontology for product catalog management', 'system', 'published');

-- Insert sample nodes for customer-domain
INSERT INTO ontology_nodes (id, ontology_id, node_id, node_type, label, description, properties, position_x, position_y) VALUES
(UUID(), 'customer-domain', 'customer', 'class', 'Customer', 'Represents a customer entity', '["id", "name", "email", "registration_date"]', 100.00, 100.00),
(UUID(), 'customer-domain', 'order', 'class', 'Order', 'Represents an order placed by a customer', '["order_id", "total_amount", "order_date", "status"]', 300.00, 100.00),
(UUID(), 'customer-domain', 'product', 'class', 'Product', 'Represents a product in the catalog', '["product_id", "name", "price", "category"]', 500.00, 100.00),
(UUID(), 'customer-domain', 'address', 'property', 'Address', 'Customer address information', '["street", "city", "country", "postal_code"]', 100.00, 250.00);

-- Insert sample edges for customer-domain
INSERT INTO ontology_edges (id, ontology_id, edge_id, source_node_id, target_node_id, edge_type, label, relationship_type, description) VALUES
(UUID(), 'customer-domain', 'customer-order', 'customer', 'order', 'relationship', 'places', 'one-to-many', 'Customer places orders'),
(UUID(), 'customer-domain', 'order-product', 'order', 'product', 'relationship', 'contains', 'many-to-many', 'Order contains products'),
(UUID(), 'customer-domain', 'customer-address', 'customer', 'address', 'property', 'has_address', 'one-to-one', 'Customer has address');

-- Create user management tables
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role ENUM('admin', 'editor', 'viewer') DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default admin user (password: admin123)
INSERT INTO users (id, username, email, password_hash, full_name, role) VALUES
(UUID(), 'admin', 'admin@ontology.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewldhZQLXAu1v7EG', 'System Administrator', 'admin');

-- Create analytics tables
USE ontology_analytics;

CREATE TABLE IF NOT EXISTS usage_stats (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ontology_id VARCHAR(36),
    action_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(36),
    session_id VARCHAR(100),
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    INDEX idx_ontology_id (ontology_id),
    INDEX idx_action_type (action_type),
    INDEX idx_timestamp (timestamp),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS performance_metrics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    ontology_id VARCHAR(36),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags JSON,
    INDEX idx_metric_name (metric_name),
    INDEX idx_timestamp (timestamp),
    INDEX idx_ontology_id (ontology_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci; 