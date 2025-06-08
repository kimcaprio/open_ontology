"""
SQL Analysis Models
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class QueryType(str, Enum):
    """SQL Query Types"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    CREATE_TABLE = "CREATE_TABLE"
    DROP_TABLE = "DROP_TABLE"
    DESCRIBE = "DESCRIBE"
    SHOW = "SHOW"


class ColumnInfo(BaseModel):
    """Database column information"""
    name: str
    type: str
    nullable: bool = True
    default: Optional[str] = None
    comment: Optional[str] = None


class TableInfo(BaseModel):
    """Database table information"""
    catalog: str
    schema: str
    name: str
    type: str = "TABLE"  # TABLE, VIEW, MATERIALIZED_VIEW
    columns: List[ColumnInfo] = []
    comment: Optional[str] = None
    owner: Optional[str] = None
    created_time: Optional[datetime] = None


class SchemaInfo(BaseModel):
    """Database schema information"""
    catalog: str
    name: str
    tables: List[str] = []
    comment: Optional[str] = None
    owner: Optional[str] = None


class CatalogInfo(BaseModel):
    """Database catalog information"""
    name: str
    comment: Optional[str] = None
    connector: Optional[str] = None
    schemas: List[str] = []


class QueryRequest(BaseModel):
    """SQL query execution request"""
    query: str = Field(..., description="SQL query to execute")
    catalog: Optional[str] = Field(None, description="Target catalog")
    schema: Optional[str] = Field(None, description="Target schema")
    limit: Optional[int] = Field(1000, description="Maximum number of rows to return", ge=1, le=10000)
    timeout: Optional[int] = Field(300, description="Query timeout in seconds", ge=1, le=3600)


class QueryResult(BaseModel):
    """SQL query execution result"""
    query: str
    columns: List[str] = []
    data: List[List[Any]] = []
    row_count: int = 0
    execution_time_ms: float = 0
    query_id: Optional[str] = None
    stats: Dict[str, Any] = {}
    error: Optional[str] = None


class SampleQueryRequest(BaseModel):
    """Request for generating sample queries"""
    catalog: str
    schema: str
    table: str
    query_types: List[QueryType] = Field(default=[QueryType.SELECT, QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE])


class SampleQuery(BaseModel):
    """Generated sample query"""
    type: QueryType
    query: str
    description: str
    parameters: Dict[str, Any] = {}


class SampleQueriesResponse(BaseModel):
    """Response containing sample queries"""
    catalog: str
    schema: str
    table: str
    table_info: TableInfo
    queries: List[SampleQuery] = []


class CatalogBrowserResponse(BaseModel):
    """Response for catalog browser"""
    catalogs: List[CatalogInfo] = []
    total_catalogs: int = 0
    total_schemas: int = 0
    total_tables: int = 0


class QueryExecutionStats(BaseModel):
    """Query execution statistics"""
    query_id: str
    state: str
    queued: bool = False
    scheduled: bool = False
    nodes: int = 0
    total_splits: int = 0
    queued_splits: int = 0
    running_splits: int = 0
    completed_splits: int = 0
    cpu_time_millis: int = 0
    wall_time_millis: int = 0
    queued_time_millis: int = 0
    elapsed_time_millis: int = 0
    processed_rows: int = 0
    processed_bytes: int = 0
    physical_input_bytes: int = 0
    peak_memory_bytes: int = 0
    spilled_bytes: int = 0
    progress_percentage: Optional[float] = None


class AnalysisSession(BaseModel):
    """Analysis session information"""
    session_id: str
    user_id: str = "anonymous"
    catalog: Optional[str] = None
    schema: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_query: Optional[str] = None
    last_activity: datetime = Field(default_factory=datetime.now)
    query_count: int = 0
    properties: Dict[str, Any] = {} 