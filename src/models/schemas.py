"""
Pydantic schemas for API request/response models
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class DataSourceType(str, Enum):
    """Data source types"""
    DATABASE = "database"
    API = "api"
    FILE = "file"
    CLOUD_STORAGE = "cloud_storage"
    STREAMING = "streaming"


class DataSourceCreate(BaseModel):
    """Create data source request"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    type: DataSourceType
    connection_config: Dict[str, Any] = Field(..., description="Connection configuration")
    tags: Optional[List[str]] = Field(default_factory=list)


class DataSourceUpdate(BaseModel):
    """Update data source request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    connection_config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class DataSourceResponse(BaseModel):
    """Data source response"""
    id: str
    name: str
    description: Optional[str]
    type: DataSourceType
    connection_config: Dict[str, Any]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    last_scan_at: Optional[datetime] = None
    status: str = "active"


class ConnectionTestRequest(BaseModel):
    """Connection test request"""
    connection_config: Dict[str, Any]


class ConnectionTestResponse(BaseModel):
    """Connection test response"""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class MetadataScanResponse(BaseModel):
    """Metadata scan response"""
    scan_id: str
    status: str
    tables_found: int
    columns_found: int
    started_at: datetime
    completed_at: Optional[datetime] = None


class OntologyEntityCreate(BaseModel):
    """Create ontology entity request"""
    name: str = Field(..., min_length=1, max_length=100)
    type: str = Field(..., description="Entity type (Class, Property, etc.)")
    description: Optional[str] = Field(None, max_length=500)
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict)
    namespace: Optional[str] = None


class OntologyEntityResponse(BaseModel):
    """Ontology entity response"""
    id: str
    name: str
    type: str
    description: Optional[str]
    properties: Dict[str, Any]
    namespace: Optional[str]
    created_at: datetime
    updated_at: datetime


class OntologyRelationshipCreate(BaseModel):
    """Create ontology relationship request"""
    subject_id: str
    predicate: str
    object_id: str
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict)


class OntologyRelationshipResponse(BaseModel):
    """Ontology relationship response"""
    id: str
    subject_id: str
    predicate: str
    object_id: str
    properties: Dict[str, Any]
    created_at: datetime


class SystemStatusResponse(BaseModel):
    """System status response"""
    api_server: bool = True
    minio: bool = False
    unity_catalog: bool = False
    ollama: bool = False
    database: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SearchRequest(BaseModel):
    """Search request"""
    query: str = Field(..., min_length=1)
    source: str = Field(..., description="Search source (exa, duckduckgo, catalog)")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    limit: int = Field(10, ge=1, le=100)


class SearchResponse(BaseModel):
    """Search response"""
    query: str
    source: str
    results: List[Dict[str, Any]]
    total_count: int
    execution_time_ms: float


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow) 