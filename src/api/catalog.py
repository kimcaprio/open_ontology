"""
Data Catalog API Router
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime

from src.services.catalog_service import catalog_service
from src.config.logging_config import get_service_logger

router = APIRouter(prefix="/catalog", tags=["Data Catalog"])
logger = get_service_logger("catalog_api")

class CatalogStatsResponse(BaseModel):
    """Catalog statistics response model"""
    total_data_sources: int
    total_databases: int
    total_tables: int
    total_columns: int
    total_rows: int
    healthy_sources: int
    last_scan_time: Optional[datetime] = None

class CatalogColumnResponse(BaseModel):
    """Catalog column response model"""
    name: str
    data_type: str
    nullable: bool
    primary_key: bool
    foreign_key: bool
    default_value: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []

class CatalogTableResponse(BaseModel):
    """Catalog table response model"""
    name: str
    database_name: str
    data_source_id: str
    full_name: str
    columns: List[CatalogColumnResponse] = []
    description: Optional[str] = None
    row_count: Optional[int] = None
    column_count: int
    last_scanned_at: Optional[datetime] = None
    tags: List[str] = []

class CatalogDatabaseResponse(BaseModel):
    """Catalog database response model"""
    name: str
    data_source_id: str
    tables: List[CatalogTableResponse] = []
    description: Optional[str] = None
    table_count: int
    total_row_count: int
    total_column_count: int
    last_scanned_at: Optional[datetime] = None
    tags: List[str] = []

class CatalogDataSourceResponse(BaseModel):
    """Catalog data source response model"""
    id: str
    name: str
    type: str
    databases: List[CatalogDatabaseResponse] = []
    description: Optional[str] = None
    connection_status: str
    database_count: int
    table_count: int
    total_row_count: int
    last_scanned_at: Optional[datetime] = None
    tags: List[str] = []

class CatalogTreeResponse(BaseModel):
    """Catalog tree response model"""
    data_sources: List[CatalogDataSourceResponse] = []
    total_data_sources: int
    total_databases: int
    total_tables: int
    total_columns: int
    last_updated: Optional[datetime] = None

class CatalogSearchResultResponse(BaseModel):
    """Catalog search result response model"""
    item_type: str
    name: str
    full_name: str
    description: Optional[str] = None
    data_source_name: str = ""
    database_name: str = ""
    table_name: str = ""
    tags: List[str] = []
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = {}

@router.get("/stats", response_model=CatalogStatsResponse)
async def get_catalog_stats():
    """Get catalog statistics"""
    try:
        logger.info("Getting catalog statistics")
        
        stats = await catalog_service.get_catalog_stats()
        
        response = CatalogStatsResponse(
            total_data_sources=stats.total_data_sources,
            total_databases=stats.total_databases,
            total_tables=stats.total_tables,
            total_columns=stats.total_columns,
            total_rows=stats.total_rows,
            healthy_sources=stats.healthy_sources,
            last_scan_time=stats.last_scan_time
        )
        
        logger.success(f"Retrieved catalog stats: {stats.total_data_sources} sources, {stats.total_tables} tables")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get catalog stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get catalog statistics: {str(e)}")

@router.get("/tree", response_model=CatalogTreeResponse)
async def get_catalog_tree():
    """Get the complete catalog tree"""
    try:
        logger.info("Getting catalog tree")
        
        catalog_tree = await catalog_service.get_catalog_tree()
        
        # Convert to response format
        data_sources = []
        for ds in catalog_tree.data_sources:
            databases = []
            for db in ds.databases:
                tables = []
                for table in db.tables:
                    columns = []
                    for col in table.columns:
                        columns.append(CatalogColumnResponse(
                            name=col.name,
                            data_type=col.data_type,
                            nullable=col.nullable,
                            primary_key=col.primary_key,
                            foreign_key=col.foreign_key,
                            default_value=col.default_value,
                            description=col.description,
                            tags=col.tags
                        ))
                    
                    tables.append(CatalogTableResponse(
                        name=table.name,
                        database_name=table.database_name,
                        data_source_id=table.data_source_id,
                        full_name=table.full_name,
                        columns=columns,
                        description=table.description,
                        row_count=table.row_count,
                        column_count=table.column_count,
                        last_scanned_at=table.last_scanned_at,
                        tags=table.tags
                    ))
                
                databases.append(CatalogDatabaseResponse(
                    name=db.name,
                    data_source_id=db.data_source_id,
                    tables=tables,
                    description=db.description,
                    table_count=db.table_count,
                    total_row_count=db.total_row_count,
                    total_column_count=db.total_column_count,
                    last_scanned_at=db.last_scanned_at,
                    tags=db.tags
                ))
            
            data_sources.append(CatalogDataSourceResponse(
                id=ds.id,
                name=ds.name,
                type=ds.type,
                databases=databases,
                description=ds.description,
                connection_status=ds.connection_status,
                database_count=ds.database_count,
                table_count=ds.table_count,
                total_row_count=ds.total_row_count,
                last_scanned_at=ds.last_scanned_at,
                tags=ds.tags
            ))
        
        response = CatalogTreeResponse(
            data_sources=data_sources,
            total_data_sources=catalog_tree.total_data_sources,
            total_databases=catalog_tree.total_databases,
            total_tables=catalog_tree.total_tables,
            total_columns=catalog_tree.total_columns,
            last_updated=catalog_tree.last_updated
        )
        
        logger.success(f"Retrieved catalog tree with {len(data_sources)} data sources")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get catalog tree: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get catalog tree: {str(e)}")

@router.post("/refresh")
async def refresh_catalog():
    """Refresh the catalog from data sources"""
    try:
        logger.info("Refreshing catalog")
        
        catalog_tree = await catalog_service.refresh_catalog()
        
        logger.success(f"Catalog refreshed successfully: {catalog_tree.total_data_sources} sources")
        return {
            "message": "Catalog refreshed successfully",
            "stats": {
                "data_sources": catalog_tree.total_data_sources,
                "databases": catalog_tree.total_databases,
                "tables": catalog_tree.total_tables,
                "columns": catalog_tree.total_columns
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to refresh catalog: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh catalog: {str(e)}")

@router.get("/search", response_model=List[CatalogSearchResultResponse])
async def search_catalog(
    q: str = Query(..., description="Search query"),
    types: Optional[List[str]] = Query(None, description="Item types to search"),
    limit: int = Query(50, description="Maximum number of results")
):
    """Search the catalog"""
    try:
        logger.info(f"Searching catalog with query: {q}")
        
        results = await catalog_service.search_catalog(q, types)
        
        # Limit results
        results = results[:limit]
        
        # Convert to response format
        response = []
        for result in results:
            response.append(CatalogSearchResultResponse(
                item_type=result.item_type,
                name=result.name,
                full_name=result.full_name,
                description=result.description,
                data_source_name=result.data_source_name,
                database_name=result.database_name,
                table_name=result.table_name,
                tags=result.tags,
                relevance_score=result.relevance_score,
                metadata=result.metadata
            ))
        
        logger.success(f"Found {len(response)} search results for query: {q}")
        return response
        
    except Exception as e:
        logger.error(f"Catalog search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/tables/{data_source_id}/{database_name}/{table_name}", response_model=CatalogTableResponse)
async def get_table_details(data_source_id: str, database_name: str, table_name: str):
    """Get detailed information about a specific table"""
    try:
        logger.info(f"Getting table details: {data_source_id}.{database_name}.{table_name}")
        
        table = await catalog_service.get_table_details(data_source_id, database_name, table_name)
        
        if not table:
            raise HTTPException(status_code=404, detail="Table not found")
        
        # Convert columns
        columns = []
        for col in table.columns:
            columns.append(CatalogColumnResponse(
                name=col.name,
                data_type=col.data_type,
                nullable=col.nullable,
                primary_key=col.primary_key,
                foreign_key=col.foreign_key,
                default_value=col.default_value,
                description=col.description,
                tags=col.tags
            ))
        
        response = CatalogTableResponse(
            name=table.name,
            database_name=table.database_name,
            data_source_id=table.data_source_id,
            full_name=table.full_name,
            columns=columns,
            description=table.description,
            row_count=table.row_count,
            column_count=table.column_count,
            last_scanned_at=table.last_scanned_at,
            tags=table.tags
        )
        
        logger.success(f"Retrieved table details for {table.full_name}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get table details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get table details: {str(e)}")

@router.get("/databases/{data_source_id}/{database_name}/tables", response_model=List[CatalogTableResponse])
async def get_database_tables(data_source_id: str, database_name: str):
    """Get all tables in a specific database"""
    try:
        logger.info(f"Getting tables for database: {data_source_id}.{database_name}")
        
        tables = await catalog_service.get_database_tables(data_source_id, database_name)
        
        # Convert to response format
        response = []
        for table in tables:
            columns = []
            for col in table.columns:
                columns.append(CatalogColumnResponse(
                    name=col.name,
                    data_type=col.data_type,
                    nullable=col.nullable,
                    primary_key=col.primary_key,
                    foreign_key=col.foreign_key,
                    default_value=col.default_value,
                    description=col.description,
                    tags=col.tags
                ))
            
            response.append(CatalogTableResponse(
                name=table.name,
                database_name=table.database_name,
                data_source_id=table.data_source_id,
                full_name=table.full_name,
                columns=columns,
                description=table.description,
                row_count=table.row_count,
                column_count=table.column_count,
                last_scanned_at=table.last_scanned_at,
                tags=table.tags
            ))
        
        logger.success(f"Retrieved {len(response)} tables for database {database_name}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get database tables: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get database tables: {str(e)}") 