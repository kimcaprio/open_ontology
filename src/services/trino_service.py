"""
Trino SQL Engine Service
MPP distributed SQL query engine integration with Unity Catalog
"""

import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4

import trino
from trino.dbapi import connect
from trino.auth import BasicAuthentication

from src.config import get_settings
from src.config.logging_config import get_service_logger
from src.models.analysis import (
    CatalogInfo, SchemaInfo, TableInfo, ColumnInfo,
    QueryRequest, QueryResult, SampleQuery, SampleQueryRequest, 
    SampleQueriesResponse, QueryType, QueryExecutionStats,
    CatalogBrowserResponse, AnalysisSession
)
from src.services.unity_catalog_service import unity_catalog_service


class TrinoService:
    """Trino SQL engine service for distributed query processing with Unity Catalog integration"""
    
    def __init__(self):
        # Initialize service logger
        self.logger = get_service_logger("trino")
        
        self.settings = get_settings()
        self._connection = None
        self._cursor = None
        
        # Demo catalogs for testing (when Unity Catalog is not available)
        self._demo_catalogs = self._create_demo_catalogs()
        
        # Unity Catalog integration
        # 개발 환경에서는 Unity Catalog를 비활성화하고 데모 데이터 사용
        self.use_unity_catalog = self.settings.is_production  # Only enable in production
        
        # Trino connection status cache
        self._trino_available = None  # None: unknown, True: available, False: unavailable
        self._last_connection_check = 0  # Timestamp of last connection check
        self._connection_check_interval = 300  # Check every 5 minutes (300 seconds)
        
        self.logger.info("Trino service initialized with Unity Catalog integration",
                        host=self.settings.trino_host,
                        port=self.settings.trino_port,
                        user=self.settings.trino_user,
                        catalog=self.settings.trino_catalog,
                        unity_catalog_endpoint=self.settings.uc_endpoint)
    
    def _create_demo_catalogs(self) -> List[CatalogInfo]:
        """Create demo catalog data for testing"""
        return [
            CatalogInfo(
                name="memory",
                comment="In-memory connector for testing",
                connector="memory",
                schemas=["default", "test"]
            ),
            CatalogInfo(
                name="oracle_catalog",
                comment="Oracle Database Catalog",
                connector="oracle",
                schemas=["hr", "sales", "finance"]
            ),
            CatalogInfo(
                name="mysql_catalog", 
                comment="MySQL Database Catalog",
                connector="mysql",
                schemas=["ecommerce", "analytics", "logs"]
            ),
            CatalogInfo(
                name="postgresql_catalog",
                comment="PostgreSQL Database Catalog", 
                connector="postgresql",
                schemas=["public", "warehouse", "staging"]
            )
        ]
    
    async def _check_trino_availability(self) -> bool:
        """Check if Trino is available (with caching)"""
        current_time = time.time()
        
        # Check cache first
        if (self._trino_available is not None and 
            current_time - self._last_connection_check < self._connection_check_interval):
            return self._trino_available
        
        # Perform actual connection check
        try:
            # Direct connection test without using get_connection to avoid recursion
            # Create authentication if credentials are provided
            auth = None
            if self.settings.trino_auth_username and self.settings.trino_auth_password:
                auth = BasicAuthentication(
                    self.settings.trino_auth_username,
                    self.settings.trino_auth_password
                )
            
            test_connection = connect(
                host=self.settings.trino_host,
                port=self.settings.trino_port,
                user=self.settings.trino_user,
                catalog=self.settings.trino_catalog,
                schema=self.settings.trino_schema,
                http_scheme=self.settings.trino_http_scheme,
                auth=auth
            )
            
            test_cursor = test_connection.cursor()
            test_cursor.execute("SELECT 1")
            result = test_cursor.fetchone()
            test_connection.close()
            
            self._trino_available = True
            self.logger.info("Trino connection check: AVAILABLE")
            
        except Exception as e:
            self._trino_available = False
            self.logger.warning(f"Trino connection check: UNAVAILABLE ({str(e)})")
        
        self._last_connection_check = current_time
        return self._trino_available
    
    async def get_connection(self):
        """Get or create Trino connection"""
        start_time = time.time()
        self.logger.log_function_start("get_connection")
        
        try:
            if self._connection is None:
                # Create authentication if credentials are provided
                auth = None
                if self.settings.trino_auth_username and self.settings.trino_auth_password:
                    auth = BasicAuthentication(
                        self.settings.trino_auth_username,
                        self.settings.trino_auth_password
                    )
                
                self._connection = connect(
                    host=self.settings.trino_host,
                    port=self.settings.trino_port,
                    user=self.settings.trino_user,
                    catalog=self.settings.trino_catalog,
                    schema=self.settings.trino_schema,
                    http_scheme=self.settings.trino_http_scheme,
                    auth=auth
                )
                
                self._cursor = self._connection.cursor()
                
                execution_time = (time.time() - start_time) * 1000
                self.logger.log_function_success(
                    "get_connection",
                    result="Connection established",
                    execution_time=execution_time,
                    host=self.settings.trino_host,
                    port=self.settings.trino_port
                )
            
            return self._connection, self._cursor
            
        except Exception as e:
            self.logger.log_function_error("get_connection", e)
            return None, None
    
    async def health_check(self) -> bool:
        """Check Trino service health"""
        start_time = time.time()
        self.logger.log_function_start("health_check")
        
        try:
            connection, cursor = await self.get_connection()
            if not connection or not cursor:
                return False
            
            # Test with a simple query
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "health_check",
                result="Health check passed",
                execution_time=execution_time,
                test_result=result[0] if result else None
            )
            return True
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_error("health_check", e, execution_time=execution_time)
            return False
    
    async def get_catalogs(self) -> List[CatalogInfo]:
        """Get available catalogs (Unity Catalog first, fallback to Trino, then demo)"""
        start_time = time.time()
        self.logger.log_function_start("get_catalogs")
        
        try:
            # Try Unity Catalog first
            if self.use_unity_catalog:
                uc_health = await unity_catalog_service.health_check()
                if uc_health:
                    catalogs = await unity_catalog_service.get_catalogs()
                    if catalogs:
                        execution_time = (time.time() - start_time) * 1000
                        self.logger.log_function_success(
                            "get_catalogs",
                            result=f"Retrieved {len(catalogs)} catalogs from Unity Catalog",
                            execution_time=execution_time,
                            catalog_count=len(catalogs),
                            source="unity_catalog"
                        )
                        return catalogs
                    else:
                        self.logger.log_function_warning(
                            "get_catalogs",
                            "No catalogs found in Unity Catalog"
                        )
                else:
                    self.logger.log_function_warning(
                        "get_catalogs",
                        "Unity Catalog health check failed, trying Trino directly"
                    )
            
            # Check Trino availability before attempting connection
            trino_available = await self._check_trino_availability()
            if not trino_available:
                # Skip Trino connection attempt and go directly to demo data
                execution_time = (time.time() - start_time) * 1000
                self.logger.log_function_warning(
                    "get_catalogs",
                    "Using demo catalogs (Trino not available)",
                    execution_time=execution_time,
                    catalog_count=len(self._demo_catalogs),
                    source="demo"
                )
                return self._demo_catalogs
            
            # Fallback to Trino direct connection (only if available)
            connection, cursor = await self.get_connection()
            if connection and cursor:
                # Query system catalogs
                cursor.execute("SHOW CATALOGS")
                rows = cursor.fetchall()
                
                catalogs = []
                for row in rows:
                    catalog_name = row[0]
                    # Get schemas for each catalog
                    try:
                        cursor.execute(f"SHOW SCHEMAS FROM {catalog_name}")
                        schema_rows = cursor.fetchall()
                        schemas = [schema_row[0] for schema_row in schema_rows]
                    except:
                        schemas = []
                    
                    catalogs.append(CatalogInfo(
                        name=catalog_name,
                        schemas=schemas
                    ))
                
                execution_time = (time.time() - start_time) * 1000
                self.logger.log_function_success(
                    "get_catalogs",
                    result=f"Retrieved {len(catalogs)} catalogs from Trino",
                    execution_time=execution_time,
                    catalog_count=len(catalogs),
                    source="trino"
                )
                
                return catalogs
            
            # Final fallback to demo data
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_warning(
                "get_catalogs",
                "Using demo catalogs (Unity Catalog and Trino not available)",
                execution_time=execution_time,
                catalog_count=len(self._demo_catalogs),
                source="demo"
            )
            return self._demo_catalogs
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_error("get_catalogs", e, execution_time=execution_time)
            # Return demo data on error
            return self._demo_catalogs
    
    async def get_schemas(self, catalog: str) -> List[SchemaInfo]:
        """Get schemas in a catalog (Unity Catalog first, fallback to Trino, then demo)"""
        start_time = time.time()
        self.logger.log_function_start("get_schemas", catalog=catalog)
        
        try:
            # Try Unity Catalog first
            if self.use_unity_catalog:
                uc_health = await unity_catalog_service.health_check()
                if uc_health:
                    schemas = await unity_catalog_service.get_schemas(catalog)
                    if schemas:
                        execution_time = (time.time() - start_time) * 1000
                        self.logger.log_function_success(
                            "get_schemas",
                            result=f"Retrieved {len(schemas)} schemas from Unity Catalog",
                            execution_time=execution_time,
                            catalog=catalog,
                            schema_count=len(schemas),
                            source="unity_catalog"
                        )
                        return schemas
                    else:
                        self.logger.log_function_warning(
                            "get_schemas",
                            f"No schemas found in Unity Catalog for catalog {catalog}"
                        )
                else:
                    self.logger.log_function_warning(
                        "get_schemas",
                        "Unity Catalog health check failed, trying Trino directly"
                    )
            
            # Check Trino availability before attempting connection
            trino_available = await self._check_trino_availability()
            if not trino_available:
                # Skip Trino connection attempt and go directly to demo data
                demo_catalog = next((c for c in self._demo_catalogs if c.name == catalog), None)
                if demo_catalog:
                    schemas = [SchemaInfo(catalog=catalog, name=schema) for schema in demo_catalog.schemas]
                    execution_time = (time.time() - start_time) * 1000
                    self.logger.log_function_warning(
                        "get_schemas",
                        "Using demo schemas (Trino not available)",
                        execution_time=execution_time,
                        catalog=catalog,
                        schema_count=len(schemas),
                        source="demo"
                    )
                    return schemas
                return []
            
            # Fallback to Trino direct connection (only if available)
            connection, cursor = await self.get_connection()
            if connection and cursor:
                cursor.execute(f"SHOW SCHEMAS FROM {catalog}")
                rows = cursor.fetchall()
                
                schemas = []
                for row in rows:
                    schema_name = row[0]
                    # Get tables for each schema
                    try:
                        cursor.execute(f"SHOW TABLES FROM {catalog}.{schema_name}")
                        table_rows = cursor.fetchall()
                        tables = [table_row[0] for table_row in table_rows]
                    except:
                        tables = []
                    
                    schemas.append(SchemaInfo(
                        catalog=catalog,
                        name=schema_name,
                        tables=tables
                    ))
                
                execution_time = (time.time() - start_time) * 1000
                self.logger.log_function_success(
                    "get_schemas",
                    result=f"Retrieved {len(schemas)} schemas from Trino",
                    execution_time=execution_time,
                    catalog=catalog,
                    schema_count=len(schemas),
                    source="trino"
                )
                
                return schemas
            
            # Final fallback to demo data
            demo_catalog = next((c for c in self._demo_catalogs if c.name == catalog), None)
            if demo_catalog:
                schemas = [SchemaInfo(catalog=catalog, name=schema) for schema in demo_catalog.schemas]
                execution_time = (time.time() - start_time) * 1000
                self.logger.log_function_warning(
                    "get_schemas",
                    "Using demo schemas (Unity Catalog and Trino not available)",
                    execution_time=execution_time,
                    catalog=catalog,
                    schema_count=len(schemas),
                    source="demo"
                )
                return schemas
            
            return []
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_error("get_schemas", e, catalog=catalog, execution_time=execution_time)
            
            # Return demo data on error
            demo_catalog = next((c for c in self._demo_catalogs if c.name == catalog), None)
            if demo_catalog:
                schemas = [SchemaInfo(catalog=catalog, name=schema) for schema in demo_catalog.schemas]
                self.logger.log_function_warning(
                    "get_schemas",
                    f"Using demo schemas due to error: {str(e)}",
                    execution_time=execution_time,
                    catalog=catalog,
                    schema_count=len(schemas),
                    source="demo"
                )
                return schemas
            
            return []
    
    async def get_tables(self, catalog: str, schema: str) -> List[TableInfo]:
        """Get tables in a schema (Unity Catalog first, fallback to Trino, then demo)"""
        start_time = time.time()
        self.logger.log_function_start("get_tables", catalog=catalog, schema=schema)
        
        try:
            # Try Unity Catalog first
            if self.use_unity_catalog:
                uc_health = await unity_catalog_service.health_check()
                if uc_health:
                    tables = await unity_catalog_service.get_tables(catalog, schema)
                    if tables:
                        execution_time = (time.time() - start_time) * 1000
                        self.logger.log_function_success(
                            "get_tables",
                            result=f"Retrieved {len(tables)} tables from Unity Catalog",
                            execution_time=execution_time,
                            catalog=catalog,
                            schema=schema,
                            table_count=len(tables),
                            source="unity_catalog"
                        )
                        return tables
                    else:
                        self.logger.log_function_warning(
                            "get_tables",
                            f"No tables found in Unity Catalog for {catalog}.{schema}"
                        )
                else:
                    self.logger.log_function_warning(
                        "get_tables",
                        "Unity Catalog health check failed, trying Trino directly"
                    )
            
            # Check Trino availability before attempting connection
            trino_available = await self._check_trino_availability()
            if not trino_available:
                # Skip Trino connection attempt and go directly to demo data
                demo_tables = self._get_demo_tables(catalog, schema)
                if demo_tables:
                    execution_time = (time.time() - start_time) * 1000
                    self.logger.log_function_warning(
                        "get_tables",
                        "Using demo tables (Trino not available)",
                        execution_time=execution_time,
                        catalog=catalog,
                        schema=schema,
                        table_count=len(demo_tables),
                        source="demo"
                    )
                    return demo_tables
                return []
            
            # Fallback to Trino direct connection (only if available)
            connection, cursor = await self.get_connection()
            if connection and cursor:
                cursor.execute(f"SHOW TABLES FROM {catalog}.{schema}")
                rows = cursor.fetchall()
                
                tables = []
                for row in rows:
                    table_name = row[0]
                    # Get column information
                    try:
                        cursor.execute(f"DESCRIBE {catalog}.{schema}.{table_name}")
                        column_rows = cursor.fetchall()
                        columns = []
                        for col_row in column_rows:
                            columns.append(ColumnInfo(
                                name=col_row[0],
                                type=col_row[1]
                            ))
                    except:
                        columns = []
                    
                    tables.append(TableInfo(
                        catalog=catalog,
                        schema=schema,
                        name=table_name,
                        columns=columns
                    ))
                
                execution_time = (time.time() - start_time) * 1000
                self.logger.log_function_success(
                    "get_tables",
                    result=f"Retrieved {len(tables)} tables from Trino",
                    execution_time=execution_time,
                    catalog=catalog,
                    schema=schema,
                    table_count=len(tables),
                    source="trino"
                )
                
                return tables
            
            # Final fallback to demo data
            demo_tables = self._get_demo_tables(catalog, schema)
            if demo_tables:
                execution_time = (time.time() - start_time) * 1000
                self.logger.log_function_warning(
                    "get_tables",
                    "Using demo tables (Unity Catalog and Trino not available)",
                    execution_time=execution_time,
                    catalog=catalog,
                    schema=schema,
                    table_count=len(demo_tables),
                    source="demo"
                )
                return demo_tables
            
            return []
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_error("get_tables", e, catalog=catalog, schema=schema, execution_time=execution_time)
            
            # Return demo data on error
            demo_tables = self._get_demo_tables(catalog, schema)
            if demo_tables:
                self.logger.log_function_warning(
                    "get_tables",
                    f"Using demo tables due to error: {str(e)}",
                    execution_time=execution_time,
                    catalog=catalog,
                    schema=schema,
                    table_count=len(demo_tables),
                    source="demo"
                )
                return demo_tables
            
            return []
    
    def _get_demo_tables(self, catalog: str, schema: str) -> List[TableInfo]:
        """Get demo table data"""
        demo_tables_data = {
            "memory.default": [
                ("users", [
                    ("id", "bigint"), ("name", "varchar"), ("email", "varchar"), 
                    ("created_at", "timestamp"), ("active", "boolean")
                ]),
                ("orders", [
                    ("order_id", "bigint"), ("user_id", "bigint"), ("product", "varchar"),
                    ("amount", "decimal(10,2)"), ("order_date", "date")
                ])
            ],
            "oracle_catalog.hr": [
                ("employees", [
                    ("employee_id", "number"), ("first_name", "varchar2"), ("last_name", "varchar2"),
                    ("email", "varchar2"), ("hire_date", "date"), ("salary", "number")
                ]),
                ("departments", [
                    ("department_id", "number"), ("department_name", "varchar2"), 
                    ("manager_id", "number"), ("location_id", "number")
                ])
            ],
            "mysql_catalog.ecommerce": [
                ("products", [
                    ("product_id", "int"), ("name", "varchar"), ("price", "decimal"), 
                    ("category", "varchar"), ("stock", "int")
                ]),
                ("customers", [
                    ("customer_id", "int"), ("name", "varchar"), ("email", "varchar"),
                    ("phone", "varchar"), ("address", "text")
                ])
            ]
        }
        
        key = f"{catalog}.{schema}"
        if key in demo_tables_data:
            tables = []
            for table_name, columns_data in demo_tables_data[key]:
                columns = [ColumnInfo(name=col[0], type=col[1]) for col in columns_data]
                tables.append(TableInfo(
                    catalog=catalog,
                    schema=schema,
                    name=table_name,
                    columns=columns
                ))
            return tables
        return []
    
    async def get_table_info(self, catalog: str, schema: str, table: str) -> Optional[TableInfo]:
        """Get detailed table information (Unity Catalog first, fallback to Trino, then demo)"""
        start_time = time.time()
        self.logger.log_function_start("get_table_info", catalog=catalog, schema=schema, table=table)
        
        try:
            # Try Unity Catalog first
            if self.use_unity_catalog:
                uc_health = await unity_catalog_service.health_check()
                if uc_health:
                    table_info = await unity_catalog_service.get_table_info(catalog, schema, table)
                    if table_info:
                        execution_time = (time.time() - start_time) * 1000
                        self.logger.log_function_success(
                            "get_table_info",
                            result=f"Retrieved table info from Unity Catalog: {catalog}.{schema}.{table}",
                            execution_time=execution_time,
                            catalog=catalog,
                            schema=schema,
                            table=table,
                            column_count=len(table_info.columns),
                            source="unity_catalog"
                        )
                        return table_info
                    else:
                        self.logger.log_function_warning(
                            "get_table_info",
                            f"Table {catalog}.{schema}.{table} not found in Unity Catalog"
                        )
                else:
                    self.logger.log_function_warning(
                        "get_table_info",
                        "Unity Catalog health check failed, trying Trino directly"
                    )
            
            # Fallback to Trino direct connection
            connection, cursor = await self.get_connection()
            if connection and cursor:
                # Get table description
                cursor.execute(f"DESCRIBE {catalog}.{schema}.{table}")
                column_rows = cursor.fetchall()
                
                columns = []
                for col_row in column_rows:
                    columns.append(ColumnInfo(
                        name=col_row[0],
                        type=col_row[1],
                        comment=col_row[2] if len(col_row) > 2 else ""
                    ))
                
                table_info = TableInfo(
                    catalog=catalog,
                    schema=schema,
                    name=table,
                    columns=columns
                )
                
                execution_time = (time.time() - start_time) * 1000
                self.logger.log_function_success(
                    "get_table_info",
                    result=f"Retrieved table info from Trino: {catalog}.{schema}.{table}",
                    execution_time=execution_time,
                    catalog=catalog,
                    schema=schema,
                    table=table,
                    column_count=len(columns),
                    source="trino"
                )
                
                return table_info
            
            # Final fallback to demo data
            demo_tables = self._get_demo_tables(catalog, schema)
            for demo_table in demo_tables:
                if demo_table.name == table:
                    self.logger.log_function_warning(
                        "get_table_info",
                        f"Using demo table info due to error: {catalog}.{schema}.{table}",
                        execution_time=execution_time,
                        catalog=catalog,
                        schema=schema,
                        table=table,
                        column_count=len(demo_table.columns),
                        source="demo"
                    )
                    return demo_table
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_warning(
                "get_table_info",
                f"Table {catalog}.{schema}.{table} not found in any source",
                execution_time=execution_time,
                catalog=catalog,
                schema=schema,
                table=table
            )
            return None
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_error("get_table_info", e, catalog=catalog, schema=schema, table=table, execution_time=execution_time)
            
            # Return demo data on error
            demo_tables = self._get_demo_tables(catalog, schema)
            for demo_table in demo_tables:
                if demo_table.name == table:
                    self.logger.log_function_warning(
                        "get_table_info",
                        f"Using demo table info due to error: {catalog}.{schema}.{table}",
                        execution_time=execution_time,
                        catalog=catalog,
                        schema=schema,
                        table=table,
                        column_count=len(demo_table.columns),
                        source="demo"
                    )
                    return demo_table
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_warning(
                "get_table_info",
                f"Table {catalog}.{schema}.{table} not found in any source",
                execution_time=execution_time,
                catalog=catalog,
                schema=schema,
                table=table
            )
            return None
    
    async def execute_query(self, request: QueryRequest) -> QueryResult:
        """Execute SQL query"""
        start_time = time.time()
        query_start_time = datetime.now()
        self.logger.log_function_start(
            "execute_query",
            query=request.query[:100] + "..." if len(request.query) > 100 else request.query,
            catalog=request.catalog,
            schema=request.schema,
            limit=request.limit
        )
        
        try:
            connection, cursor = await self.get_connection()
            if not connection or not cursor:
                execution_time = (time.time() - start_time) * 1000
                return QueryResult(
                    query=request.query,
                    execution_time_ms=execution_time,
                    error="Trino connection not available"
                )
            
            # Set session properties if catalog/schema specified
            if request.catalog:
                cursor.execute(f"USE {request.catalog}")
            if request.schema:
                cursor.execute(f"USE {request.catalog}.{request.schema}")
            
            # Add LIMIT to query if not present and it's a SELECT
            query = request.query.strip()
            if query.upper().startswith('SELECT') and 'LIMIT' not in query.upper():
                query = f"{query} LIMIT {request.limit}"
            
            # Execute query
            cursor.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # Fetch data
            rows = cursor.fetchall()
            
            # Convert to list format
            data = [list(row) for row in rows]
            
            # Get query stats
            stats = cursor.stats if hasattr(cursor, 'stats') else {}
            
            execution_time = (time.time() - start_time) * 1000
            result = QueryResult(
                query=request.query,
                columns=columns,
                data=data,
                row_count=len(data),
                execution_time_ms=execution_time,
                query_id=stats.get('queryId'),
                stats=stats
            )
            
            self.logger.log_function_success(
                "execute_query",
                result=f"Query executed successfully, {len(data)} rows returned",
                execution_time=execution_time,
                query_id=stats.get('queryId'),
                row_count=len(data),
                column_count=len(columns)
            )
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_error("execute_query", e, execution_time=execution_time)
            
            return QueryResult(
                query=request.query,
                execution_time_ms=execution_time,
                error=str(e)
            )
    
    async def generate_sample_queries(self, request: SampleQueryRequest) -> SampleQueriesResponse:
        """Generate sample queries for a table"""
        start_time = time.time()
        self.logger.log_function_start(
            "generate_sample_queries",
            catalog=request.catalog,
            schema=request.schema,
            table=request.table,
            query_types=[qt.value for qt in request.query_types]
        )
        
        try:
            # Get table information
            table_info = await self.get_table_info(request.catalog, request.schema, request.table)
            if not table_info:
                execution_time = (time.time() - start_time) * 1000
                self.logger.log_function_warning(
                    "generate_sample_queries",
                    "Table info not found",
                    execution_time=execution_time,
                    catalog=request.catalog,
                    schema=request.schema,
                    table=request.table
                )
                return SampleQueriesResponse(
                    catalog=request.catalog,
                    schema=request.schema,
                    table=request.table,
                    table_info=TableInfo(catalog=request.catalog, schema=request.schema, name=request.table),
                    queries=[]
                )
            
            queries = []
            full_table_name = f"{request.catalog}.{request.schema}.{request.table}"
            
            for query_type in request.query_types:
                if query_type == QueryType.SELECT:
                    # Basic SELECT query
                    column_list = ", ".join([col.name for col in table_info.columns[:5]])  # First 5 columns
                    query = f"SELECT {column_list}\nFROM {full_table_name}\nLIMIT 10;"
                    
                    queries.append(SampleQuery(
                        type=QueryType.SELECT,
                        query=query,
                        description="Basic SELECT query to retrieve data from the table"
                    ))
                    
                    # SELECT with WHERE clause
                    if table_info.columns:
                        first_col = table_info.columns[0]
                        where_query = f"SELECT *\nFROM {full_table_name}\nWHERE {first_col.name} IS NOT NULL\nLIMIT 10;"
                        queries.append(SampleQuery(
                            type=QueryType.SELECT,
                            query=where_query,
                            description="SELECT query with WHERE clause filtering"
                        ))
                
                elif query_type == QueryType.INSERT:
                    if table_info.columns:
                        columns = ", ".join([col.name for col in table_info.columns])
                        values = []
                        for col in table_info.columns:
                            if 'int' in col.type.lower() or 'number' in col.type.lower():
                                values.append("1")
                            elif 'varchar' in col.type.lower() or 'text' in col.type.lower():
                                values.append("'sample_value'")
                            elif 'date' in col.type.lower():
                                values.append("CURRENT_DATE")
                            elif 'timestamp' in col.type.lower():
                                values.append("CURRENT_TIMESTAMP")
                            elif 'boolean' in col.type.lower():
                                values.append("true")
                            else:
                                values.append("NULL")
                        
                        value_list = ", ".join(values)
                        query = f"INSERT INTO {full_table_name}\n({columns})\nVALUES ({value_list});"
                        
                        queries.append(SampleQuery(
                            type=QueryType.INSERT,
                            query=query,
                            description="Sample INSERT query to add new data"
                        ))
                
                elif query_type == QueryType.UPDATE:
                    if table_info.columns:
                        set_clauses = []
                        where_col = table_info.columns[0]
                        
                        for col in table_info.columns[1:3]:  # Update first 2 non-id columns
                            if 'varchar' in col.type.lower():
                                set_clauses.append(f"{col.name} = 'updated_value'")
                            elif 'int' in col.type.lower() or 'number' in col.type.lower():
                                set_clauses.append(f"{col.name} = {col.name} + 1")
                            elif 'date' in col.type.lower() or 'timestamp' in col.type.lower():
                                set_clauses.append(f"{col.name} = CURRENT_TIMESTAMP")
                        
                        if set_clauses:
                            set_clause = ", ".join(set_clauses)
                            query = f"UPDATE {full_table_name}\nSET {set_clause}\nWHERE {where_col.name} = <value>;"
                            
                            queries.append(SampleQuery(
                                type=QueryType.UPDATE,
                                query=query,
                                description="Sample UPDATE query to modify existing data"
                            ))
                
                elif query_type == QueryType.DELETE:
                    if table_info.columns:
                        where_col = table_info.columns[0]
                        query = f"DELETE FROM {full_table_name}\nWHERE {where_col.name} = <value>;"
                        
                        queries.append(SampleQuery(
                            type=QueryType.DELETE,
                            query=query,
                            description="Sample DELETE query to remove data (use with caution)"
                        ))
                        
                        # Conditional delete
                        query2 = f"DELETE FROM {full_table_name}\nWHERE {where_col.name} IS NULL;"
                        queries.append(SampleQuery(
                            type=QueryType.DELETE,
                            query=query2,
                            description="DELETE query to remove rows with NULL values"
                        ))
            
            response = SampleQueriesResponse(
                catalog=request.catalog,
                schema=request.schema,
                table=request.table,
                table_info=table_info,
                queries=queries
            )
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "generate_sample_queries",
                result=f"Generated {len(queries)} sample queries",
                execution_time=execution_time,
                catalog=request.catalog,
                schema=request.schema,
                table=request.table,
                query_count=len(queries)
            )
            
            return response
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_error("generate_sample_queries", e, execution_time=execution_time)
            
            return SampleQueriesResponse(
                catalog=request.catalog,
                schema=request.schema,
                table=request.table,
                table_info=TableInfo(catalog=request.catalog, schema=request.schema, name=request.table),
                queries=[]
            )
    
    async def get_catalog_browser_data(self) -> CatalogBrowserResponse:
        """Get data for catalog browser"""
        start_time = time.time()
        self.logger.log_function_start("get_catalog_browser_data")
        
        try:
            catalogs = await self.get_catalogs()
            total_schemas = 0
            total_tables = 0
            
            for catalog in catalogs:
                total_schemas += len(catalog.schemas)
                # Count tables in each schema
                for schema_name in catalog.schemas:
                    tables = await self.get_tables(catalog.name, schema_name)
                    total_tables += len(tables)
            
            response = CatalogBrowserResponse(
                catalogs=catalogs,
                total_catalogs=len(catalogs),
                total_schemas=total_schemas,
                total_tables=total_tables
            )
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "get_catalog_browser_data",
                result=f"Browser data: {len(catalogs)} catalogs, {total_schemas} schemas, {total_tables} tables",
                execution_time=execution_time,
                total_catalogs=len(catalogs),
                total_schemas=total_schemas,
                total_tables=total_tables
            )
            
            return response
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_error("get_catalog_browser_data", e, execution_time=execution_time)
            
            return CatalogBrowserResponse()
    
    async def close_connection(self):
        """Close Trino connection"""
        if self._connection:
            try:
                self._connection.close()
                self._connection = None
                self._cursor = None
                self.logger.info("Trino connection closed")
            except Exception as e:
                self.logger.error(f"Error closing connection: {e}")

    async def get_full_schema_context(self, max_catalogs: int = 5, max_schemas_per_catalog: int = 3, max_tables_per_schema: int = 10) -> Dict[str, Any]:
        """
        Get comprehensive schema context for LLM queries
        
        Args:
            max_catalogs: Maximum number of catalogs to include
            max_schemas_per_catalog: Maximum schemas per catalog
            max_tables_per_schema: Maximum tables per schema
            
        Returns:
            Dictionary with structured schema information
        """
        start_time = time.time()
        self.logger.log_function_start("get_full_schema_context")
        
        try:
            # Get all available catalogs
            catalogs = await self.get_catalogs()
            
            schema_context = {
                "total_catalogs": len(catalogs),
                "catalogs": []
            }
            
            # Process limited number of catalogs
            for catalog in catalogs[:max_catalogs]:
                catalog_info = {
                    "name": catalog.name,
                    "comment": catalog.comment,
                    "schemas": []
                }
                
                # Get schemas for this catalog
                try:
                    schemas = await self.get_schemas(catalog.name)
                    
                    # Process limited number of schemas
                    for schema in schemas[:max_schemas_per_catalog]:
                        schema_info = {
                            "name": schema.name,
                            "tables": []
                        }
                        
                        # Get tables for this schema
                        try:
                            tables = await self.get_tables(catalog.name, schema.name)
                            
                            # Process limited number of tables
                            for table in tables[:max_tables_per_schema]:
                                table_info = {
                                    "name": table.name,
                                    "full_name": f"{catalog.name}.{schema.name}.{table.name}",
                                    "columns": []
                                }
                                
                                # Add column information
                                for column in table.columns:
                                    table_info["columns"].append({
                                        "name": column.name,
                                        "type": column.type,
                                        "comment": getattr(column, 'comment', '')
                                    })
                                
                                schema_info["tables"].append(table_info)
                        
                        except Exception as table_error:
                            self.logger.log_function_warning(
                                "get_full_schema_context",
                                f"Failed to get tables for {catalog.name}.{schema.name}: {str(table_error)}"
                            )
                        
                        catalog_info["schemas"].append(schema_info)
                
                except Exception as schema_error:
                    self.logger.log_function_warning(
                        "get_full_schema_context", 
                        f"Failed to get schemas for {catalog.name}: {str(schema_error)}"
                    )
                
                schema_context["catalogs"].append(catalog_info)
            
            execution_time = (time.time() - start_time) * 1000
            
            # Calculate totals
            total_schemas = sum(len(cat["schemas"]) for cat in schema_context["catalogs"])
            total_tables = sum(len(schema["tables"]) for cat in schema_context["catalogs"] for schema in cat["schemas"])
            
            schema_context.update({
                "total_schemas": total_schemas,
                "total_tables": total_tables,
                "generation_time_ms": execution_time
            })
            
            self.logger.log_function_success(
                "get_full_schema_context",
                result=f"Generated schema context with {len(schema_context['catalogs'])} catalogs",
                execution_time=execution_time,
                total_catalogs=len(schema_context["catalogs"]),
                total_schemas=total_schemas,
                total_tables=total_tables
            )
            
            return schema_context
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_error("get_full_schema_context", e, execution_time=execution_time)
            
            # Return minimal context in case of error
            return {
                "total_catalogs": 0,
                "total_schemas": 0,
                "total_tables": 0,
                "catalogs": [],
                "error": str(e),
                "generation_time_ms": execution_time
            }

    def format_schema_context_for_llm(self, schema_context: Dict[str, Any]) -> str:
        """
        Format schema context into a readable string for LLM
        
        Args:
            schema_context: Schema context from get_full_schema_context()
            
        Returns:
            Formatted string for LLM consumption
        """
        if not schema_context or not schema_context.get("catalogs"):
            return "No schema information available."
        
        context_lines = [
            "=== AVAILABLE DATABASE SCHEMA ===",
            f"Total: {schema_context['total_catalogs']} catalogs, {schema_context['total_schemas']} schemas, {schema_context['total_tables']} tables",
            ""
        ]
        
        for catalog in schema_context["catalogs"]:
            context_lines.append(f"📁 CATALOG: {catalog['name']}")
            if catalog.get("comment"):
                context_lines.append(f"   Description: {catalog['comment']}")
            
            for schema in catalog["schemas"]:
                context_lines.append(f"  📂 SCHEMA: {catalog['name']}.{schema['name']}")
                
                for table in schema["tables"]:
                    context_lines.append(f"    📋 TABLE: {table['full_name']}")
                    
                    # Add column information
                    columns_info = []
                    for col in table["columns"]:
                        col_desc = f"{col['name']} ({col['type']})"
                        if col.get("comment"):
                            col_desc += f" - {col['comment']}"
                        columns_info.append(col_desc)
                    
                    if columns_info:
                        context_lines.append(f"       Columns: {', '.join(columns_info[:10])}")  # Limit to 10 columns
                        if len(table["columns"]) > 10:
                            context_lines.append(f"       ... and {len(table['columns']) - 10} more columns")
                    
                    context_lines.append("")  # Empty line between tables
        
        context_lines.extend([
            "=== QUERY GUIDELINES ===",
            "- Always use fully qualified table names (catalog.schema.table)",
            "- Add LIMIT clauses for large result sets (default: LIMIT 100)",
            "- Use proper JOIN syntax when combining tables",
            "- Available catalogs: " + ", ".join([cat["name"] for cat in schema_context["catalogs"]]),
            ""
        ])
        
        return "\n".join(context_lines)


# Global service instance
trino_service = TrinoService() 