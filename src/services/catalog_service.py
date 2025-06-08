"""
Data Catalog Service
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from src.config.logging_config import get_service_logger
from src.models.catalog import (
    CatalogColumn, CatalogTable, CatalogDatabase, CatalogDataSource,
    CatalogTree, CatalogStats, CatalogSearchResult, CatalogItemType
)
from src.services.data_source_service import data_source_service


class CatalogService:
    """Data catalog management service"""
    
    def __init__(self):
        self.logger = get_service_logger("catalog")
        self.catalog_tree = CatalogTree()
        
    async def refresh_catalog(self) -> CatalogTree:
        """Refresh the entire catalog from data sources"""
        try:
            self.logger.info("Starting catalog refresh")
            
            # Get all data sources
            data_sources = await data_source_service.get_data_sources()
            
            catalog_data_sources = []
            
            for data_source in data_sources:
                self.logger.info(f"Processing data source: {data_source.name}")
                
                # Scan metadata for this data source
                scan_result = await data_source_service.scan_metadata(data_source.id)
                
                if scan_result["success"]:
                    catalog_ds = await self._convert_to_catalog_data_source(
                        data_source, scan_result["metadata"]
                    )
                    catalog_data_sources.append(catalog_ds)
                else:
                    self.logger.warning(f"Failed to scan {data_source.name}: {scan_result['message']}")
                    # Create empty catalog data source
                    catalog_ds = CatalogDataSource(
                        id=data_source.id,
                        name=data_source.name,
                        type=data_source.type,
                        description=data_source.description,
                        connection_status="unhealthy",
                        last_scanned_at=datetime.utcnow(),
                        tags=data_source.tags
                    )
                    catalog_data_sources.append(catalog_ds)
            
            # Update catalog tree
            self.catalog_tree.data_sources = catalog_data_sources
            self.catalog_tree.update_statistics()
            
            self.logger.success(f"Catalog refresh completed. Found {len(catalog_data_sources)} data sources")
            return self.catalog_tree
            
        except Exception as e:
            self.logger.error(f"Catalog refresh failed: {str(e)}")
            raise
    
    async def _convert_to_catalog_data_source(self, data_source, metadata: Dict[str, Any]) -> CatalogDataSource:
        """Convert data source metadata to catalog data source"""
        try:
            databases = []
            
            # Group tables by database
            tables_by_db = {}
            for table_info in metadata.get("tables", []):
                db_name = table_info["database"]
                if db_name not in tables_by_db:
                    tables_by_db[db_name] = []
                tables_by_db[db_name].append(table_info)
            
            # Create catalog databases
            for db_name, tables in tables_by_db.items():
                catalog_tables = []
                
                for table_info in tables:
                    # Convert columns
                    catalog_columns = []
                    for col_info in table_info.get("columns", []):
                        catalog_col = CatalogColumn(
                            name=col_info["name"],
                            data_type=col_info["type"],
                            nullable=col_info["null"],
                            primary_key="PRI" in col_info.get("key", ""),
                            foreign_key="FK" in col_info.get("tags", []),
                            default_value=col_info.get("default"),
                            description=f"Column {col_info['name']} of type {col_info['type']}",
                            tags=self._extract_column_tags(col_info)
                        )
                        catalog_columns.append(catalog_col)
                    
                    # Create catalog table
                    catalog_table = CatalogTable(
                        name=table_info["name"],
                        database_name=db_name,
                        data_source_id=data_source.id,
                        columns=catalog_columns,
                        description=f"Table {table_info['name']} from {data_source.name}",
                        row_count=table_info.get("row_count"),
                        last_scanned_at=datetime.utcnow(),
                        tags=["mysql", "auto-generated"]
                    )
                    catalog_tables.append(catalog_table)
                
                # Create catalog database
                catalog_db = CatalogDatabase(
                    name=db_name,
                    data_source_id=data_source.id,
                    tables=catalog_tables,
                    description=f"Database {db_name} from {data_source.name}",
                    last_scanned_at=datetime.utcnow(),
                    tags=["mysql"]
                )
                databases.append(catalog_db)
            
            # Create catalog data source
            catalog_ds = CatalogDataSource(
                id=data_source.id,
                name=data_source.name,
                type=data_source.type,
                databases=databases,
                description=data_source.description,
                connection_status="healthy",
                last_scanned_at=datetime.utcnow(),
                tags=data_source.tags
            )
            
            return catalog_ds
            
        except Exception as e:
            self.logger.error(f"Failed to convert data source {data_source.name}: {str(e)}")
            raise
    
    def _extract_column_tags(self, col_info: Dict[str, Any]) -> List[str]:
        """Extract tags from column information"""
        tags = []
        
        # Add type-based tags
        data_type = col_info["type"].upper()
        if "INT" in data_type:
            tags.append("numeric")
        elif "VARCHAR" in data_type or "TEXT" in data_type:
            tags.append("text")
        elif "DATE" in data_type or "TIME" in data_type:
            tags.append("datetime")
        elif "DECIMAL" in data_type or "FLOAT" in data_type:
            tags.append("numeric")
        
        # Add key tags
        if "PRI" in col_info.get("key", ""):
            tags.append("primary-key")
        if "MUL" in col_info.get("key", ""):
            tags.append("foreign-key")
        
        # Add nullability tag
        if not col_info["null"]:
            tags.append("required")
        
        # Add name-based tags
        col_name = col_info["name"].lower()
        if "id" in col_name:
            tags.append("identifier")
        if "email" in col_name:
            tags.append("pii")
        if "name" in col_name:
            tags.append("pii")
        if "date" in col_name or "time" in col_name:
            tags.append("temporal")
        
        return tags
    
    async def get_catalog_tree(self) -> CatalogTree:
        """Get the current catalog tree"""
        if not self.catalog_tree.data_sources:
            await self.refresh_catalog()
        return self.catalog_tree
    
    async def get_catalog_stats(self) -> CatalogStats:
        """Get catalog statistics"""
        catalog_tree = await self.get_catalog_tree()
        
        stats = CatalogStats(
            total_data_sources=catalog_tree.total_data_sources,
            total_databases=catalog_tree.total_databases,
            total_tables=catalog_tree.total_tables,
            total_columns=catalog_tree.total_columns,
            total_rows=sum(ds.total_row_count for ds in catalog_tree.data_sources),
            healthy_sources=sum(1 for ds in catalog_tree.data_sources if ds.connection_status == "healthy"),
            last_scan_time=catalog_tree.last_updated
        )
        
        return stats
    
    async def search_catalog(self, query: str, item_types: Optional[List[str]] = None) -> List[CatalogSearchResult]:
        """Search the catalog"""
        try:
            if not query or len(query.strip()) < 2:
                return []
            
            catalog_tree = await self.get_catalog_tree()
            results = []
            query_lower = query.lower()
            
            for data_source in catalog_tree.data_sources:
                # Search data source
                if self._matches_query(data_source.name, query_lower):
                    results.append(CatalogSearchResult(
                        item_type=CatalogItemType.DATA_SOURCE,
                        name=data_source.name,
                        full_name=data_source.name,
                        description=data_source.description,
                        data_source_name=data_source.name,
                        tags=data_source.tags,
                        relevance_score=self._calculate_relevance(data_source.name, query_lower),
                        metadata={"type": data_source.type, "status": data_source.connection_status}
                    ))
                
                for database in data_source.databases:
                    # Search database
                    if self._matches_query(database.name, query_lower):
                        results.append(CatalogSearchResult(
                            item_type=CatalogItemType.DATABASE,
                            name=database.name,
                            full_name=f"{data_source.name}.{database.name}",
                            description=database.description,
                            data_source_name=data_source.name,
                            database_name=database.name,
                            tags=database.tags,
                            relevance_score=self._calculate_relevance(database.name, query_lower),
                            metadata={"table_count": database.table_count}
                        ))
                    
                    for table in database.tables:
                        # Search table
                        if self._matches_query(table.name, query_lower):
                            results.append(CatalogSearchResult(
                                item_type=CatalogItemType.TABLE,
                                name=table.name,
                                full_name=f"{data_source.name}.{database.name}.{table.name}",
                                description=table.description,
                                data_source_name=data_source.name,
                                database_name=database.name,
                                table_name=table.name,
                                tags=table.tags,
                                relevance_score=self._calculate_relevance(table.name, query_lower),
                                metadata={
                                    "column_count": table.column_count,
                                    "row_count": table.row_count
                                }
                            ))
                        
                        for column in table.columns:
                            # Search column
                            if self._matches_query(column.name, query_lower):
                                results.append(CatalogSearchResult(
                                    item_type=CatalogItemType.COLUMN,
                                    name=column.name,
                                    full_name=f"{data_source.name}.{database.name}.{table.name}.{column.name}",
                                    description=column.description,
                                    data_source_name=data_source.name,
                                    database_name=database.name,
                                    table_name=table.name,
                                    tags=column.tags,
                                    relevance_score=self._calculate_relevance(column.name, query_lower),
                                    metadata={
                                        "data_type": column.data_type,
                                        "nullable": column.nullable
                                    }
                                ))
            
            # Filter by item types if specified
            if item_types:
                results = [r for r in results if r.item_type in item_types]
            
            # Sort by relevance score (descending)
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Limit results
            return results[:50]
            
        except Exception as e:
            self.logger.error(f"Catalog search failed: {str(e)}")
            return []
    
    def _matches_query(self, text: str, query: str) -> bool:
        """Check if text matches search query"""
        if not text:
            return False
        return query in text.lower()
    
    def _calculate_relevance(self, text: str, query: str) -> float:
        """Calculate relevance score for search results"""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        
        # Exact match gets highest score
        if text_lower == query:
            return 1.0
        
        # Starts with query gets high score
        if text_lower.startswith(query):
            return 0.8
        
        # Contains query gets medium score
        if query in text_lower:
            return 0.6
        
        # Fuzzy matching (simple)
        words = query.split()
        matches = sum(1 for word in words if word in text_lower)
        return (matches / len(words)) * 0.4 if words else 0.0
    
    async def get_table_details(self, data_source_id: str, database_name: str, table_name: str) -> Optional[CatalogTable]:
        """Get detailed information about a specific table"""
        try:
            catalog_tree = await self.get_catalog_tree()
            
            for data_source in catalog_tree.data_sources:
                if data_source.id == data_source_id:
                    for database in data_source.databases:
                        if database.name == database_name:
                            for table in database.tables:
                                if table.name == table_name:
                                    return table
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get table details: {str(e)}")
            return None
    
    async def get_database_tables(self, data_source_id: str, database_name: str) -> List[CatalogTable]:
        """Get all tables in a database"""
        try:
            catalog_tree = await self.get_catalog_tree()
            
            for data_source in catalog_tree.data_sources:
                if data_source.id == data_source_id:
                    for database in data_source.databases:
                        if database.name == database_name:
                            return database.tables
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get database tables: {str(e)}")
            return []


# Global instance
catalog_service = CatalogService() 