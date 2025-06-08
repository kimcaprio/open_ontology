"""
Unity Catalog Service
REST API integration for Unity Catalog metadata management
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

from src.config import get_settings
from src.config.logging_config import get_service_logger
from src.models.analysis import CatalogInfo, SchemaInfo, TableInfo, ColumnInfo


class UnityCatalogService:
    """Unity Catalog REST API service"""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_service_logger("unity_catalog")
        
        # Unity Catalog API base URL
        self.base_url = self.settings.uc_endpoint
        
        # API session
        self._session = None
        
        self.logger.info("Unity Catalog service initialized",
                        endpoint=self.base_url,
                        catalog=self.settings.uc_catalog_name)
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session
    
    async def health_check(self) -> bool:
        """Check Unity Catalog service health"""
        try:
            session = await self._get_session()
            
            # Try to list catalogs as a health check
            url = urljoin(self.base_url, "catalogs")
            async with session.get(url) as response:
                if response.status == 200:
                    self.logger.info("Unity Catalog health check passed")
                    return True
                else:
                    self.logger.warning(f"Unity Catalog health check failed with status: {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Unity Catalog health check failed: {e}")
            return False
    
    async def get_catalogs(self) -> List[CatalogInfo]:
        """Get all catalogs from Unity Catalog"""
        try:
            session = await self._get_session()
            
            url = urljoin(self.base_url, "catalogs")
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    catalogs = []
                    
                    for catalog_data in data.get("catalogs", []):
                        catalog_name = catalog_data.get("name")
                        
                        # Get schemas for this catalog
                        schemas = await self._get_catalog_schemas(catalog_name)
                        schema_names = [schema.name for schema in schemas]
                        
                        catalogs.append(CatalogInfo(
                            name=catalog_name,
                            comment=catalog_data.get("comment", ""),
                            schemas=schema_names
                        ))
                    
                    self.logger.info(f"Retrieved {len(catalogs)} catalogs from Unity Catalog")
                    return catalogs
                    
                else:
                    self.logger.warning(f"Failed to get catalogs, status: {response.status}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error getting catalogs from Unity Catalog: {e}")
            return []
    
    async def _get_catalog_schemas(self, catalog_name: str) -> List[SchemaInfo]:
        """Get schemas for a specific catalog"""
        try:
            session = await self._get_session()
            
            url = urljoin(self.base_url, f"schemas?catalog_name={catalog_name}")
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    schemas = []
                    
                    for schema_data in data.get("schemas", []):
                        schema_name = schema_data.get("name")
                        
                        # Get tables for this schema
                        tables = await self._get_schema_tables(catalog_name, schema_name)
                        table_names = [table.name for table in tables]
                        
                        schemas.append(SchemaInfo(
                            catalog=catalog_name,
                            name=schema_name,
                            comment=schema_data.get("comment", ""),
                            tables=table_names
                        ))
                    
                    return schemas
                    
                else:
                    self.logger.warning(f"Failed to get schemas for catalog {catalog_name}, status: {response.status}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error getting schemas for catalog {catalog_name}: {e}")
            return []
    
    async def get_schemas(self, catalog_name: str) -> List[SchemaInfo]:
        """Get schemas for a catalog"""
        return await self._get_catalog_schemas(catalog_name)
    
    async def _get_schema_tables(self, catalog_name: str, schema_name: str) -> List[TableInfo]:
        """Get tables for a specific schema"""
        try:
            session = await self._get_session()
            
            url = urljoin(self.base_url, f"tables?catalog_name={catalog_name}&schema_name={schema_name}")
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    tables = []
                    
                    for table_data in data.get("tables", []):
                        table_name = table_data.get("name")
                        
                        # Get column information
                        columns = await self._get_table_columns(catalog_name, schema_name, table_name)
                        
                        tables.append(TableInfo(
                            catalog=catalog_name,
                            schema=schema_name,
                            name=table_name,
                            comment=table_data.get("comment", ""),
                            table_type=table_data.get("table_type", "MANAGED"),
                            columns=columns
                        ))
                    
                    return tables
                    
                else:
                    self.logger.warning(f"Failed to get tables for {catalog_name}.{schema_name}, status: {response.status}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error getting tables for {catalog_name}.{schema_name}: {e}")
            return []
    
    async def get_tables(self, catalog_name: str, schema_name: str) -> List[TableInfo]:
        """Get tables for a schema"""
        return await self._get_schema_tables(catalog_name, schema_name)
    
    async def _get_table_columns(self, catalog_name: str, schema_name: str, table_name: str) -> List[ColumnInfo]:
        """Get column information for a table"""
        try:
            session = await self._get_session()
            
            url = urljoin(self.base_url, f"tables/{catalog_name}.{schema_name}.{table_name}")
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    columns = []
                    
                    for column_data in data.get("columns", []):
                        columns.append(ColumnInfo(
                            name=column_data.get("name"),
                            type=column_data.get("type_name", "string"),
                            comment=column_data.get("comment", ""),
                            nullable=column_data.get("nullable", True)
                        ))
                    
                    return columns
                    
                else:
                    self.logger.warning(f"Failed to get columns for {catalog_name}.{schema_name}.{table_name}, status: {response.status}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error getting columns for {catalog_name}.{schema_name}.{table_name}: {e}")
            return []
    
    async def get_table_info(self, catalog_name: str, schema_name: str, table_name: str) -> Optional[TableInfo]:
        """Get detailed table information"""
        try:
            session = await self._get_session()
            
            url = urljoin(self.base_url, f"tables/{catalog_name}.{schema_name}.{table_name}")
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Get column information
                    columns = await self._get_table_columns(catalog_name, schema_name, table_name)
                    
                    return TableInfo(
                        catalog=catalog_name,
                        schema=schema_name,
                        name=table_name,
                        comment=data.get("comment", ""),
                        table_type=data.get("table_type", "MANAGED"),
                        columns=columns,
                        properties=data.get("properties", {}),
                        storage_location=data.get("storage_location", "")
                    )
                    
                else:
                    self.logger.warning(f"Table {catalog_name}.{schema_name}.{table_name} not found, status: {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error getting table info for {catalog_name}.{schema_name}.{table_name}: {e}")
            return None
    
    async def close(self):
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self.logger.info("Unity Catalog service session closed")


# Global Unity Catalog service instance
unity_catalog_service = UnityCatalogService() 