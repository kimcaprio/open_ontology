# Database Setup Guide

## Overview

This project includes a comprehensive Docker-based database setup with MySQL, PostgreSQL, and Redis for different purposes:

- **MySQL**: Main development database for ontology data
- **PostgreSQL**: Alternative development database + Unity Catalog
- **Redis**: Caching layer
- **Management Tools**: phpMyAdmin & pgAdmin for database administration

## Quick Start

### 1. Start All Services

```bash
# Start all database services
docker-compose up -d mysql postgres redis pgadmin phpmyadmin

# Or start everything including the application
docker-compose up -d
```

### 2. Verify Services

```bash
# Check service status
docker-compose ps

# Check logs if needed
docker-compose logs mysql
docker-compose logs postgres
```

## Service Details

### MySQL Database

- **Host**: localhost
- **Port**: 3306
- **Database**: ontology_dev
- **User**: ontology_user
- **Password**: ontology_password
- **Root Password**: rootpassword

#### Connection String:
```
mysql://ontology_user:ontology_password@localhost:3306/ontology_dev
```

#### Additional Databases:
- `ontology_test` - For testing
- `ontology_analytics` - For analytics data

### PostgreSQL Database

- **Host**: localhost
- **Port**: 5433 (to avoid conflict with Unity Catalog)
- **Database**: ontology_dev
- **User**: ontology_user
- **Password**: ontology_password

#### Connection String:
```
postgresql://ontology_user:ontology_password@localhost:5433/ontology_dev
```

#### Additional Databases:
- `ontology_test` - For testing
- `ontology_analytics` - For analytics data

### Unity Catalog PostgreSQL

- **Host**: localhost
- **Port**: 5432
- **Database**: unity_catalog
- **User**: unity
- **Password**: catalog123

### Redis Cache

- **Host**: localhost
- **Port**: 6379
- **No Authentication**

#### Connection String:
```
redis://localhost:6379/0
```

## Database Management Tools

### phpMyAdmin (MySQL)

- **URL**: http://localhost:8080
- **Username**: root
- **Password**: rootpassword

### pgAdmin (PostgreSQL)

- **URL**: http://localhost:5050
- **Email**: admin@ontology.com
- **Password**: admin123

#### Adding PostgreSQL Servers in pgAdmin:

1. **Development PostgreSQL**:
   - Host: postgres
   - Port: 5432
   - Database: ontology_dev
   - Username: ontology_user
   - Password: ontology_password

2. **Unity Catalog PostgreSQL**:
   - Host: unity-catalog
   - Port: 5432
   - Database: unity_catalog
   - Username: unity
   - Password: catalog123

## Database Schema

### Core Tables

#### `ontologies`
- Stores ontology metadata and versions
- Supports draft/published/archived status

#### `ontology_nodes`
- Stores individual nodes (classes, properties, instances)
- JSON/JSONB properties for flexible data

#### `ontology_edges`
- Stores relationships between nodes
- Support for various relationship types

#### `ai_suggestions`
- Stores AI-generated suggestions for ontology improvements
- Tracks application status

#### `change_history`
- Complete audit trail of all changes
- JSON storage for before/after states

#### `users`
- User management with roles (admin/editor/viewer)
- BCrypt password hashing

### Analytics Tables (in separate database)

#### `usage_stats`
- User activity tracking
- Session and interaction logging

#### `performance_metrics`
- Application performance data
- Custom metrics with tags

## Sample Data

Both databases are initialized with sample data:

- Two sample ontologies: "Customer Domain" and "Product Catalog"
- Sample nodes and relationships
- Default admin user (username: admin, password: admin123)

## Connection from Application

### Python/FastAPI

```python
# MySQL
mysql_url = "mysql://ontology_user:ontology_password@mysql:3306/ontology_dev"

# PostgreSQL
postgres_url = "postgresql://ontology_user:ontology_password@postgres:5432/ontology_dev"

# Redis
redis_url = "redis://redis:6379/0"
```

### Environment Variables (for Docker containers)

```bash
MYSQL_URL=mysql://ontology_user:ontology_password@mysql:3306/ontology_dev
POSTGRES_URL=postgresql://ontology_user:ontology_password@postgres:5432/ontology_dev
REDIS_URL=redis://redis:6379/0
```

## Development Commands

### Connect to Databases

```bash
# MySQL
docker exec -it ontology-mysql mysql -u ontology_user -p ontology_dev

# PostgreSQL
docker exec -it ontology-postgres psql -U ontology_user -d ontology_dev

# Redis
docker exec -it ontology-redis redis-cli
```

### Backup Databases

```bash
# MySQL backup
docker exec ontology-mysql mysqldump -u root -p ontology_dev > backup_mysql.sql

# PostgreSQL backup
docker exec ontology-postgres pg_dump -U ontology_user ontology_dev > backup_postgres.sql
```

### Reset Databases

```bash
# Stop and remove containers with data
docker-compose down -v

# Restart (will recreate with fresh data)
docker-compose up -d mysql postgres redis
```

## Performance Optimization

### MySQL

- Configured with UTF8MB4 for full Unicode support
- InnoDB engine for ACID compliance
- Optimized indexes for common queries

### PostgreSQL

- UUID primary keys with proper indexing
- JSONB for flexible schema
- GIN indexes for JSON queries
- Materialized views for analytics

### Redis

- Persistent storage with AOF
- Optimized for caching frequently accessed data

## Monitoring

### Health Checks

All services include health checks:

```bash
# Check health status
docker-compose ps
```

### Logs

```bash
# View real-time logs
docker-compose logs -f mysql
docker-compose logs -f postgres
docker-compose logs -f redis
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**: Ensure ports 3306, 5432, 5433, 6379 are available
2. **Permission Issues**: Check Docker permissions if containers fail to start
3. **Data Persistence**: Use `docker-compose down -v` to reset all data

### Reset Individual Services

```bash
# Reset MySQL only
docker-compose stop mysql
docker volume rm ontology_kwkim_mysql_data
docker-compose up -d mysql

# Reset PostgreSQL only
docker-compose stop postgres
docker volume rm ontology_kwkim_postgres_data
docker-compose up -d postgres
```

## Security Notes

⚠️ **Important**: This setup is for development only. For production:

1. Change all default passwords
2. Use secure password policies
3. Configure proper network security
4. Enable SSL/TLS connections
5. Implement proper backup strategies
6. Use secrets management for credentials 