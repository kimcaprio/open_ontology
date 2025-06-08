"""
Schema Context Service
Collects and structures schema information from Trino for LLM processing
"""

from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel
import logging

from src.services.trino_service import trino_service
from src.config.logging_config import get_service_logger

logger = get_service_logger("schema_context_service")

class TableInfo(BaseModel):
    """Enhanced table information for LLM processing"""
    catalog: str
    schema: str
    name: str
    full_name: str
    description: Optional[str] = None
    columns: List[Dict[str, Any]] = []
    potential_relationships: List[str] = []  # Potential FK relationships
    business_context: Optional[str] = None  # Inferred business purpose

class SchemaContext(BaseModel):
    """Comprehensive schema context for LLM processing"""
    tables: List[TableInfo] = []
    relationships: List[Dict[str, Any]] = []
    business_domains: List[str] = []
    summary: str = ""
    total_tables: int = 0
    total_columns: int = 0
    token_count: int = 0

class SchemaContextService:
    """Service for building comprehensive schema context from Trino for LLM processing"""
    
    def __init__(self):
        self.logger = logger
    
    async def get_comprehensive_schema_context(self, max_tables: int = 50) -> SchemaContext:
        """
        Get comprehensive schema context from actual Trino catalogs
        """
        try:
            self.logger.info("Building schema context from Trino catalogs")
            
            tables = []
            business_domains = set()
            total_columns = 0
            
            # Get available catalogs from Trino
            try:
                trino_catalogs = await trino_service.get_catalogs()
                self.logger.info(f"Retrieved {len(trino_catalogs)} catalogs from Trino")
            except Exception as e:
                self.logger.warning(f"Failed to get catalogs from Trino: {e}, using fallback")
                return self._get_fallback_context()
            
            if not trino_catalogs:
                self.logger.warning("No catalogs found, using fallback")
                return self._get_fallback_context()
            
            for catalog_info in trino_catalogs:
                catalog_name = catalog_info.name
                
                # Skip system catalog for now, focus on memory and data catalogs
                if catalog_name in ['system']:
                    continue
                
                try:
                    # Get schemas in this catalog
                    schemas = await trino_service.get_schemas(catalog_name)
                    
                    for schema_info in schemas:
                        schema_name = schema_info.name
                        
                        # Skip information_schema
                        if schema_name == 'information_schema':
                            continue
                        
                        try:
                            # Get tables in this schema
                            table_list = await trino_service.get_tables(catalog_name, schema_name)
                            
                            if not table_list:
                                continue
                                
                            for table_basic in table_list[:max_tables]:
                                try:
                                    # Get detailed table info
                                    table_info = await trino_service.get_table_info(catalog_name, schema_name, table_basic.name)
                                    
                                    if table_info and table_info.columns:
                                        # Build column information
                                        columns = []
                                        for col in table_info.columns:
                                            columns.append({
                                                "name": col.name,
                                                "type": col.type,
                                                "nullable": getattr(col, 'nullable', True),
                                                "description": getattr(col, 'comment', f"Column {col.name} of type {col.type}")
                                            })
                                        
                                        total_columns += len(columns)
                                        
                                        # Infer potential relationships
                                        potential_relationships = self._infer_relationships(table_basic.name, columns)
                                        
                                        # Infer business context
                                        business_context = self._infer_business_context(table_basic.name, columns)
                                        if business_context:
                                            business_domains.add(business_context)
                                        
                                        # Create table info
                                        enhanced_table = TableInfo(
                                            catalog=catalog_name,
                                            schema=schema_name,
                                            name=table_basic.name,
                                            full_name=f"{catalog_name}.{schema_name}.{table_basic.name}",
                                            description=getattr(table_info, 'comment', f"Table {table_basic.name} from {catalog_name}.{schema_name}"),
                                            columns=columns,
                                            potential_relationships=potential_relationships,
                                            business_context=business_context
                                        )
                                        
                                        tables.append(enhanced_table)
                                        
                                except Exception as e:
                                    self.logger.warning(f"Failed to get detailed info for table {catalog_name}.{schema_name}.{table_basic.name}: {e}")
                                    
                        except Exception as e:
                            self.logger.warning(f"Failed to get tables for schema {catalog_name}.{schema_name}: {e}")
                            
                except Exception as e:
                    self.logger.warning(f"Failed to get schemas for catalog {catalog_name}: {e}")
            
            # If no tables found from Trino, use fallback
            if not tables:
                self.logger.warning("No tables found from Trino, using fallback context")
                return self._get_fallback_context()
            
            # Build relationships based on inferred connections
            relationships = self._build_relationships(tables)
            
            # Generate summary
            summary = self._generate_summary(tables, list(business_domains))
            
            # Calculate token estimate
            token_count = self._estimate_tokens(tables, relationships, summary)
            
            schema_context = SchemaContext(
                tables=tables,
                relationships=relationships,
                business_domains=list(business_domains),
                summary=summary,
                total_tables=len(tables),
                total_columns=total_columns,
                token_count=token_count
            )
            
            self.logger.success(f"Built schema context: {len(tables)} tables, {total_columns} columns, {len(business_domains)} domains")
            return schema_context
            
        except Exception as e:
            self.logger.error(f"Error building schema context: {str(e)}")
            # Return fallback context
            return self._get_fallback_context()
    
    def _get_fallback_context(self) -> SchemaContext:
        """Return fallback context with known memory tables"""
        fallback_tables = [
            TableInfo(
                catalog="memory",
                schema="default",
                name="sample_customers",
                full_name="memory.default.sample_customers",
                description="Customer information table",
                columns=[
                    {"name": "customer_id", "type": "BIGINT", "nullable": False, "description": "Unique customer identifier"},
                    {"name": "customer_name", "type": "VARCHAR(100)", "nullable": True, "description": "Customer full name"},
                    {"name": "email", "type": "VARCHAR(100)", "nullable": True, "description": "Customer email address"},
                    {"name": "country", "type": "VARCHAR(50)", "nullable": True, "description": "Customer country"},
                    {"name": "registration_date", "type": "DATE", "nullable": True, "description": "Customer registration date"}
                ],
                potential_relationships=["customer_id → purchases.customer_id"],
                business_context="customer_management"
            ),
            TableInfo(
                catalog="memory",
                schema="default",
                name="albums",
                full_name="memory.default.albums",
                description="Album catalog table",
                columns=[
                    {"name": "album_id", "type": "BIGINT", "nullable": False, "description": "Unique album identifier"},
                    {"name": "title", "type": "VARCHAR(200)", "nullable": True, "description": "Album title"},
                    {"name": "artist", "type": "VARCHAR(100)", "nullable": True, "description": "Artist name"},
                    {"name": "genre", "type": "VARCHAR(50)", "nullable": True, "description": "Music genre"},
                    {"name": "release_date", "type": "DATE", "nullable": True, "description": "Album release date"},
                    {"name": "price", "type": "DECIMAL(10,2)", "nullable": True, "description": "Album price"}
                ],
                potential_relationships=["album_id → purchases.album_id"],
                business_context="product_catalog"
            ),
            TableInfo(
                catalog="memory",
                schema="default",
                name="purchases",
                full_name="memory.default.purchases",
                description="Purchase transaction table",
                columns=[
                    {"name": "purchase_id", "type": "BIGINT", "nullable": False, "description": "Unique purchase identifier"},
                    {"name": "customer_id", "type": "BIGINT", "nullable": True, "description": "Customer who made the purchase"},
                    {"name": "album_id", "type": "BIGINT", "nullable": True, "description": "Album that was purchased"},
                    {"name": "purchase_date", "type": "DATE", "nullable": True, "description": "Date of purchase"},
                    {"name": "amount", "type": "DECIMAL(10,2)", "nullable": True, "description": "Purchase amount"},
                    {"name": "payment_method", "type": "VARCHAR(50)", "nullable": True, "description": "Payment method used"}
                ],
                potential_relationships=["customer_id → sample_customers.customer_id", "album_id → albums.album_id"],
                business_context="sales"
            )
        ]
        
        relationships = [
            {
                "from_table": "memory.default.sample_customers",
                "to_table": "memory.default.purchases",
                "type": "one_to_many",
                "condition": "customer_id = customer_id"
            },
            {
                "from_table": "memory.default.albums",
                "to_table": "memory.default.purchases",
                "type": "one_to_many",
                "condition": "album_id = album_id"
            }
        ]
        
        return SchemaContext(
            tables=fallback_tables,
            relationships=relationships,
            business_domains=["customer_management", "product_catalog", "sales"],
            summary="Sample music store database with customers, albums, and purchase transactions. Supports customer analysis, album catalog management, and sales analytics.",
            total_tables=3,
            total_columns=16,
            token_count=1500
        )
    
    def _infer_relationships(self, table_name: str, columns: List[Dict[str, Any]]) -> List[str]:
        """Infer potential foreign key relationships based on column names"""
        relationships = []
        
        for col in columns:
            col_name = col["name"].lower()
            
            # Common FK patterns
            if col_name.endswith("id") and col_name != "id":
                # Extract table name from column (e.g., customer_id -> customer)
                ref_table = col_name[:-2]  # Remove "id"
                if ref_table != table_name.lower():
                    relationships.append(f"→ {ref_table}")
            
            # Alternative FK patterns
            elif col_name.endswith("_id"):
                ref_table = col_name[:-3]  # Remove "_id"
                if ref_table != table_name.lower():
                    relationships.append(f"→ {ref_table}")
        
        return relationships
    
    def _infer_business_context(self, table_name: str, columns: List[Dict[str, Any]]) -> Optional[str]:
        """Infer business context/domain from table and column names"""
        table_lower = table_name.lower()
        column_names = [col["name"].lower() for col in columns]
        
        # Customer management domain
        if any(keyword in table_lower for keyword in ["customer", "client", "user"]) or \
           any(keyword in " ".join(column_names) for keyword in ["customer", "client", "email", "phone"]):
            return "customer_management"
        
        # Sales domain
        elif any(keyword in table_lower for keyword in ["invoice", "order", "sale", "payment", "purchase"]) or \
             any(keyword in " ".join(column_names) for keyword in ["total", "price", "amount", "payment"]):
            return "sales"
        
        # Product/Inventory domain
        elif any(keyword in table_lower for keyword in ["product", "item", "inventory", "album", "track"]) or \
             any(keyword in " ".join(column_names) for keyword in ["title", "name", "description", "genre"]):
            return "product_catalog"
        
        # HR domain
        elif any(keyword in table_lower for keyword in ["employee", "staff", "hr"]) or \
             any(keyword in " ".join(column_names) for keyword in ["firstname", "lastname", "hiredate", "salary"]):
            return "human_resources"
        
        # Analytics/Reporting domain
        elif any(keyword in table_lower for keyword in ["log", "activity", "analytics", "report"]):
            return "analytics"
        
        return None
    
    def _build_relationships(self, tables: List[TableInfo]) -> List[Dict[str, Any]]:
        """Build explicit relationships between tables"""
        relationships = []
        
        # Create a mapping of table names
        table_map = {table.name.lower(): table for table in tables}
        
        for table in tables:
            for rel in table.potential_relationships:
                if rel.startswith("→ "):
                    target_table_name = rel[2:]  # Remove "→ "
                    if target_table_name in table_map:
                        target_table = table_map[target_table_name]
                        relationships.append({
                            "from_table": table.full_name,
                            "to_table": target_table.full_name,
                            "type": "foreign_key",
                            "confidence": 0.8
                        })
        
        return relationships
    
    def _generate_summary(self, tables: List[TableInfo], business_domains: List[str]) -> str:
        """Generate a concise summary of the schema"""
        if not tables:
            return "No tables available"
        
        catalogs = set(table.catalog for table in tables)
        schemas = set(f"{table.catalog}.{table.schema}" for table in tables)
        
        summary = f"Database contains {len(tables)} tables across {len(catalogs)} catalogs and {len(schemas)} schemas. "
        
        if business_domains:
            summary += f"Business domains include: {', '.join(business_domains)}. "
        
        # Most common table types
        table_types = {}
        for table in tables:
            if table.business_context:
                table_types[table.business_context] = table_types.get(table.business_context, 0) + 1
        
        if table_types:
            most_common = max(table_types.items(), key=lambda x: x[1])
            summary += f"Primary focus appears to be {most_common[0]} with {most_common[1]} related tables."
        
        return summary
    
    def format_for_llm(self, context: SchemaContext, max_tokens: int = 8000) -> str:
        """Format schema context for LLM consumption with token limit consideration"""
        
        # Start with summary
        formatted = f"=== DATABASE SCHEMA OVERVIEW ===\n{context.summary}\n\n"
        
        # Add business domains
        if context.business_domains:
            formatted += f"=== BUSINESS DOMAINS ===\n{', '.join(context.business_domains)}\n\n"
        
        # Add tables with prioritization
        formatted += "=== AVAILABLE TABLES ===\n"
        
        # Sort tables by relevance (tables with more relationships first)
        sorted_tables = sorted(context.tables, key=lambda t: len(t.potential_relationships), reverse=True)
        
        current_length = len(formatted)
        for table in sorted_tables:
            table_desc = self._format_table_for_llm(table)
            
            # Rough token estimation (4 chars per token)
            if current_length + len(table_desc) > max_tokens * 4:
                formatted += f"... and {len(sorted_tables) - sorted_tables.index(table)} more tables\n"
                break
            
            formatted += table_desc
            current_length += len(table_desc)
        
        # Add relationships if space allows
        if context.relationships and current_length < max_tokens * 3:
            formatted += "\n=== TABLE RELATIONSHIPS ===\n"
            for rel in context.relationships[:10]:  # Limit to top 10 relationships
                formatted += f"• {rel['from_table']} → {rel['to_table']} ({rel['type']})\n"
        
        return formatted
    
    def _format_table_for_llm(self, table: TableInfo) -> str:
        """Format a single table for LLM"""
        result = f"📋 {table.full_name}"
        
        if table.business_context:
            result += f" [{table.business_context}]"
        
        result += "\n"
        
        if table.description:
            result += f"   Description: {table.description}\n"
        
        # Key columns (limit to most important ones)
        key_columns = []
        for col in table.columns[:10]:  # Limit columns
            col_info = f"{col['name']} ({col['type']})"
            if col.get('description'):
                col_info += f" - {col['description']}"
            key_columns.append(col_info)
        
        if key_columns:
            result += f"   Columns: {', '.join(key_columns)}\n"
        
        if table.potential_relationships:
            result += f"   Relationships: {', '.join(table.potential_relationships)}\n"
        
        result += "\n"
        return result

    def _estimate_tokens(self, tables: List[TableInfo], relationships: List[Dict[str, Any]], summary: str) -> int:
        """Estimate token count for the schema context"""
        # Rough estimation: 4 characters per token
        total_chars = len(summary)
        
        for table in tables:
            total_chars += len(table.full_name) + len(table.description or "") + 50  # Base table info
            for col in table.columns:
                total_chars += len(col.get('name', '')) + len(col.get('type', '')) + len(col.get('description', '')) + 10
        
        for rel in relationships:
            total_chars += len(str(rel)) + 20
        
        return total_chars // 4

# Global instance
schema_context_service = SchemaContextService() 