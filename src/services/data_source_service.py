"""
Data Source Management Service
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import pymysql
import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from src.config.logging_config import get_service_logger
from src.models.data_source import DataSource

class DataSourceService:
    """Data source management service"""
    
    def __init__(self):
        self.logger = get_service_logger("data_source")
        self.data_sources = {}  # In-memory storage for demo, should use database
        
    async def create_data_source(self, data: Dict[str, Any]) -> DataSource:
        """Create a new data source"""
        try:
            data_source = DataSource(
                id=str(uuid.uuid4()),
                name=data["name"],
                description=data.get("description"),
                type=data["type"],
                connection_config=data["connection_config"],
                tags=data.get("tags", []),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                status="active"
            )
            
            # Store in memory (should be database in production)
            self.data_sources[data_source.id] = data_source
            
            self.logger.info(f"Created data source: {data_source.name}", 
                           data_source_id=data_source.id,
                           data_source_type=data_source.type)
            
            return data_source
            
        except Exception as e:
            self.logger.error(f"Failed to create data source: {str(e)}")
            raise
    
    async def get_data_sources(self) -> List[DataSource]:
        """Get all data sources"""
        try:
            return list(self.data_sources.values())
        except Exception as e:
            self.logger.error(f"Failed to get data sources: {str(e)}")
            raise
    
    async def get_data_source(self, data_source_id: str) -> Optional[DataSource]:
        """Get a specific data source by ID"""
        try:
            return self.data_sources.get(data_source_id)
        except Exception as e:
            self.logger.error(f"Failed to get data source {data_source_id}: {str(e)}")
            raise
    
    async def update_data_source(self, data_source_id: str, data: Dict[str, Any]) -> Optional[DataSource]:
        """Update a data source"""
        try:
            data_source = self.data_sources.get(data_source_id)
            if not data_source:
                return None
            
            # Update fields
            if "name" in data:
                data_source.name = data["name"]
            if "description" in data:
                data_source.description = data["description"]
            if "connection_config" in data:
                data_source.connection_config = data["connection_config"]
            if "tags" in data:
                data_source.tags = data["tags"]
            
            data_source.updated_at = datetime.utcnow()
            
            self.logger.info(f"Updated data source: {data_source.name}", 
                           data_source_id=data_source_id)
            
            return data_source
            
        except Exception as e:
            self.logger.error(f"Failed to update data source {data_source_id}: {str(e)}")
            raise
    
    async def delete_data_source(self, data_source_id: str) -> bool:
        """Delete a data source"""
        try:
            if data_source_id in self.data_sources:
                data_source = self.data_sources[data_source_id]
                del self.data_sources[data_source_id]
                
                self.logger.info(f"Deleted data source: {data_source.name}", 
                               data_source_id=data_source_id)
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to delete data source {data_source_id}: {str(e)}")
            raise
    
    async def test_connection(self, connection_config: Dict[str, Any], db_type: str = "database") -> Dict[str, Any]:
        """Test database connection"""
        try:
            if db_type == "database":
                return await self._test_mysql_connection(connection_config)
            else:
                return {
                    "success": False,
                    "message": f"Connection test not implemented for type: {db_type}"
                }
                
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}"
            }
    
    async def _test_mysql_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test MySQL connection"""
        try:
            # Extract connection parameters
            host = config.get("host", "localhost")
            port = int(config.get("port", 3306))
            username = config.get("username", "")
            password = config.get("password", "")
            database = config.get("database", "")
            
            if not all([host, username, password]):
                return {
                    "success": False,
                    "message": "Missing required connection parameters (host, username, password)"
                }
            
            self.logger.info(f"Testing MySQL connection to {host}:{port}/{database}")
            
            # Test connection using pymysql
            connection = None
            try:
                connection = pymysql.connect(
                    host=host,
                    port=port,
                    user=username,
                    password=password,
                    database=database if database else None,
                    charset='utf8mb4',
                    auth_plugin_map={
                        'caching_sha2_password': 'mysql_native_password'
                    },
                    autocommit=True
                )
                
                # Test basic query
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1 as test")
                    result = cursor.fetchone()
                    
                    # Get server info
                    cursor.execute("SELECT VERSION() as version")
                    version_result = cursor.fetchone()
                    server_version = version_result[0] if version_result else "Unknown"
                    
                    # Get database list if no specific database
                    databases = []
                    if not database:
                        cursor.execute("SHOW DATABASES")
                        databases = [row[0] for row in cursor.fetchall()]
                    
                self.logger.success(f"MySQL connection successful to {host}:{port}")
                
                return {
                    "success": True,
                    "message": "Connection successful",
                    "server_info": {
                        "version": server_version,
                        "host": host,
                        "port": port,
                        "database": database or "No specific database",
                        "available_databases": databases[:10] if databases else []  # Limit to 10
                    }
                }
                
            finally:
                if connection:
                    connection.close()
                    
        except pymysql.Error as e:
            error_message = f"MySQL Error ({e.args[0]}): {e.args[1]}" if len(e.args) > 1 else str(e)
            self.logger.error(f"MySQL connection failed: {error_message}")
            return {
                "success": False,
                "message": f"MySQL connection failed: {error_message}"
            }
        except Exception as e:
            self.logger.error(f"Connection test error: {str(e)}")
            return {
                "success": False,
                "message": f"Connection test error: {str(e)}"
            }
    
    async def scan_metadata(self, data_source_id: str) -> Dict[str, Any]:
        """Scan metadata from a data source"""
        try:
            data_source = self.data_sources.get(data_source_id)
            if not data_source:
                return {
                    "success": False,
                    "message": "Data source not found"
                }
            
            if data_source.type == "database":
                return await self._scan_mysql_metadata(data_source.connection_config)
            else:
                return {
                    "success": False,
                    "message": f"Metadata scanning not implemented for type: {data_source.type}"
                }
                
        except Exception as e:
            self.logger.error(f"Metadata scan failed for {data_source_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Metadata scan failed: {str(e)}"
            }
    
    async def _scan_mysql_metadata(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Scan MySQL database metadata"""
        try:
            host = config.get("host", "localhost")
            port = int(config.get("port", 3306))
            username = config.get("username", "")
            password = config.get("password", "")
            database = config.get("database", "")
            
            connection = None
            try:
                connection = pymysql.connect(
                    host=host,
                    port=port,
                    user=username,
                    password=password,
                    database=database if database else None,
                    charset='utf8mb4',
                    auth_plugin_map={
                        'caching_sha2_password': 'mysql_native_password'
                    },
                    autocommit=True
                )
                
                metadata = {
                    "databases": [],
                    "tables": [],
                    "total_tables": 0,
                    "total_columns": 0
                }
                
                with connection.cursor() as cursor:
                    # Get databases
                    if database:
                        metadata["databases"] = [database]
                        target_databases = [database]
                    else:
                        cursor.execute("SHOW DATABASES")
                        all_dbs = [row[0] for row in cursor.fetchall()]
                        # Filter out system databases
                        target_databases = [db for db in all_dbs if db not in ['information_schema', 'performance_schema', 'mysql', 'sys']]
                        metadata["databases"] = target_databases
                    
                    # Get tables for each database
                    for db in target_databases[:5]:  # Limit to 5 databases
                        cursor.execute(f"USE `{db}`")
                        cursor.execute("SHOW TABLES")
                        tables = [row[0] for row in cursor.fetchall()]
                        
                        metadata["total_tables"] += len(tables)
                        
                        # Get table details (limit to 20 tables per database)
                        for table in tables[:20]:
                            cursor.execute(f"DESCRIBE `{table}`")
                            columns = []
                            for col in cursor.fetchall():
                                columns.append({
                                    "name": col[0],
                                    "type": col[1],
                                    "null": col[2] == "YES",
                                    "key": col[3],
                                    "default": col[4],
                                    "extra": col[5]
                                })
                            
                            metadata["total_columns"] += len(columns)
                            
                            # Get row count
                            try:
                                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                                row_count = cursor.fetchone()[0]
                            except:
                                row_count = None
                            
                            metadata["tables"].append({
                                "database": db,
                                "name": table,
                                "columns": columns,
                                "row_count": row_count
                            })
                
                self.logger.info(f"Scanned metadata: {len(metadata['databases'])} databases, {metadata['total_tables']} tables")
                
                return {
                    "success": True,
                    "message": "Metadata scan completed",
                    "metadata": metadata
                }
                
            finally:
                if connection:
                    connection.close()
                    
        except Exception as e:
            self.logger.error(f"MySQL metadata scan failed: {str(e)}")
            return {
                "success": False,
                "message": f"MySQL metadata scan failed: {str(e)}"
            }

# Global instance
data_source_service = DataSourceService() 