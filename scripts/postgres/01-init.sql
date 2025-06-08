-- PostgreSQL Database Initialization Script
-- This script runs when the PostgreSQL container starts for the first time

-- Create additional databases
CREATE DATABASE ontology_test;
CREATE DATABASE ontology_analytics;

-- Grant privileges to ontology_user for all databases
GRANT ALL PRIVILEGES ON DATABASE ontology_dev TO ontology_user;
GRANT ALL PRIVILEGES ON DATABASE ontology_test TO ontology_user;
GRANT ALL PRIVILEGES ON DATABASE ontology_analytics TO ontology_user;

-- Connect to main development database
\c ontology_dev;

-- Create UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types
CREATE TYPE ontology_status AS ENUM ('draft', 'published', 'archived');
CREATE TYPE node_type AS ENUM ('class', 'property', 'instance', 'relationship');
CREATE TYPE edge_type AS ENUM ('relationship', 'property', 'inheritance', 'composition', 'aggregation');
CREATE TYPE relationship_type AS ENUM ('one-to-one', 'one-to-many', 'many-to-one', 'many-to-many');
CREATE TYPE suggestion_type AS ENUM ('ontology_class', 'property', 'relationship', 'enhancement');
CREATE TYPE suggestion_status AS ENUM ('pending', 'applied', 'rejected');
CREATE TYPE change_type AS ENUM ('ADD_NODE', 'EDIT_NODE', 'DELETE_NODE', 'CREATE_CONNECTION', 'DELETE_CONNECTION', 'APPLY_SUGGESTION');
CREATE TYPE user_role AS ENUM ('admin', 'editor', 'viewer');

-- Create ontology-related tables
CREATE TABLE IF NOT EXISTS ontologies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(20) DEFAULT '1.0.0',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    status ontology_status DEFAULT 'draft'
);

-- Create indexes for ontologies
CREATE INDEX idx_ontologies_name ON ontologies(name);
CREATE INDEX idx_ontologies_status ON ontologies(status);
CREATE INDEX idx_ontologies_created_at ON ontologies(created_at);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_ontologies_updated_at BEFORE UPDATE ON ontologies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS ontology_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ontology_id UUID NOT NULL REFERENCES ontologies(id) ON DELETE CASCADE,
    node_id VARCHAR(255) NOT NULL,
    node_type node_type NOT NULL,
    label VARCHAR(255) NOT NULL,
    description TEXT,
    properties JSONB,
    position_x DECIMAL(10,2),
    position_y DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ontology_id, node_id)
);

-- Create indexes for ontology_nodes
CREATE INDEX idx_ontology_nodes_ontology_id ON ontology_nodes(ontology_id);
CREATE INDEX idx_ontology_nodes_node_type ON ontology_nodes(node_type);
CREATE INDEX idx_ontology_nodes_label ON ontology_nodes(label);
CREATE INDEX idx_ontology_nodes_properties ON ontology_nodes USING GIN(properties);

CREATE TRIGGER update_ontology_nodes_updated_at BEFORE UPDATE ON ontology_nodes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS ontology_edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ontology_id UUID NOT NULL REFERENCES ontologies(id) ON DELETE CASCADE,
    edge_id VARCHAR(255) NOT NULL,
    source_node_id VARCHAR(255) NOT NULL,
    target_node_id VARCHAR(255) NOT NULL,
    edge_type edge_type NOT NULL,
    label VARCHAR(255) NOT NULL,
    relationship_type relationship_type DEFAULT 'one-to-many',
    description TEXT,
    properties JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ontology_id, edge_id)
);

-- Create indexes for ontology_edges
CREATE INDEX idx_ontology_edges_ontology_id ON ontology_edges(ontology_id);
CREATE INDEX idx_ontology_edges_source_target ON ontology_edges(source_node_id, target_node_id);
CREATE INDEX idx_ontology_edges_edge_type ON ontology_edges(edge_type);
CREATE INDEX idx_ontology_edges_properties ON ontology_edges USING GIN(properties);

CREATE TRIGGER update_ontology_edges_updated_at BEFORE UPDATE ON ontology_edges
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TABLE IF NOT EXISTS ai_suggestions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ontology_id UUID NOT NULL REFERENCES ontologies(id) ON DELETE CASCADE,
    suggestion_type suggestion_type NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    implementation TEXT,
    status suggestion_status DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    applied_at TIMESTAMP WITH TIME ZONE NULL,
    applied_by VARCHAR(100)
);

-- Create indexes for ai_suggestions
CREATE INDEX idx_ai_suggestions_ontology_id ON ai_suggestions(ontology_id);
CREATE INDEX idx_ai_suggestions_status ON ai_suggestions(status);
CREATE INDEX idx_ai_suggestions_suggestion_type ON ai_suggestions(suggestion_type);

CREATE TABLE IF NOT EXISTS change_history (
    id BIGSERIAL PRIMARY KEY,
    ontology_id UUID NOT NULL REFERENCES ontologies(id) ON DELETE CASCADE,
    change_type change_type NOT NULL,
    change_data JSONB,
    before_state JSONB,
    after_state JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Create indexes for change_history
CREATE INDEX idx_change_history_ontology_id ON change_history(ontology_id);
CREATE INDEX idx_change_history_change_type ON change_history(change_type);
CREATE INDEX idx_change_history_created_at ON change_history(created_at);
CREATE INDEX idx_change_history_change_data ON change_history USING GIN(change_data);

-- Create user management tables
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role user_role DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE NULL
);

-- Create indexes for users
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample ontologies
INSERT INTO ontologies (id, name, description, created_by, status) VALUES
('customer-domain'::UUID, 'Customer Domain Ontology', 'Ontology representing customer-related entities and relationships', 'system', 'published'),
('product-catalog'::UUID, 'Product Catalog Ontology', 'Ontology for product catalog management', 'system', 'published');

-- Insert sample nodes for customer-domain
INSERT INTO ontology_nodes (ontology_id, node_id, node_type, label, description, properties, position_x, position_y) VALUES
('customer-domain'::UUID, 'customer', 'class', 'Customer', 'Represents a customer entity', '["id", "name", "email", "registration_date"]'::JSONB, 100.00, 100.00),
('customer-domain'::UUID, 'order', 'class', 'Order', 'Represents an order placed by a customer', '["order_id", "total_amount", "order_date", "status"]'::JSONB, 300.00, 100.00),
('customer-domain'::UUID, 'product', 'class', 'Product', 'Represents a product in the catalog', '["product_id", "name", "price", "category"]'::JSONB, 500.00, 100.00),
('customer-domain'::UUID, 'address', 'property', 'Address', 'Customer address information', '["street", "city", "country", "postal_code"]'::JSONB, 100.00, 250.00);

-- Insert sample edges for customer-domain
INSERT INTO ontology_edges (ontology_id, edge_id, source_node_id, target_node_id, edge_type, label, relationship_type, description) VALUES
('customer-domain'::UUID, 'customer-order', 'customer', 'order', 'relationship', 'places', 'one-to-many', 'Customer places orders'),
('customer-domain'::UUID, 'order-product', 'order', 'product', 'relationship', 'contains', 'many-to-many', 'Order contains products'),
('customer-domain'::UUID, 'customer-address', 'customer', 'address', 'property', 'has_address', 'one-to-one', 'Customer has address');

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, password_hash, full_name, role) VALUES
('admin', 'admin@ontology.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewldhZQLXAu1v7EG', 'System Administrator', 'admin');

-- Connect to analytics database
\c ontology_analytics;

-- Create UUID extension for analytics database
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant privileges on analytics database
GRANT ALL PRIVILEGES ON SCHEMA public TO ontology_user;

CREATE TABLE IF NOT EXISTS usage_stats (
    id BIGSERIAL PRIMARY KEY,
    ontology_id UUID,
    action_type VARCHAR(50) NOT NULL,
    user_id UUID,
    session_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Create indexes for usage_stats
CREATE INDEX idx_usage_stats_ontology_id ON usage_stats(ontology_id);
CREATE INDEX idx_usage_stats_action_type ON usage_stats(action_type);
CREATE INDEX idx_usage_stats_timestamp ON usage_stats(timestamp);
CREATE INDEX idx_usage_stats_user_id ON usage_stats(user_id);
CREATE INDEX idx_usage_stats_metadata ON usage_stats USING GIN(metadata);

CREATE TABLE IF NOT EXISTS performance_metrics (
    id BIGSERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    ontology_id UUID,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    tags JSONB
);

-- Create indexes for performance_metrics
CREATE INDEX idx_performance_metrics_metric_name ON performance_metrics(metric_name);
CREATE INDEX idx_performance_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX idx_performance_metrics_ontology_id ON performance_metrics(ontology_id);
CREATE INDEX idx_performance_metrics_tags ON performance_metrics USING GIN(tags);

-- Create materialized views for analytics
CREATE MATERIALIZED VIEW daily_usage_summary AS
SELECT 
    DATE(timestamp) as date,
    ontology_id,
    action_type,
    COUNT(*) as action_count,
    COUNT(DISTINCT user_id) as unique_users
FROM usage_stats 
GROUP BY DATE(timestamp), ontology_id, action_type;

CREATE INDEX idx_daily_usage_summary_date ON daily_usage_summary(date);

-- Create function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_analytics_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_usage_summary;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions to ontology_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ontology_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ontology_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO ontology_user; 