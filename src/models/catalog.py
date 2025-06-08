"""
Data Catalog Models
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class CatalogItemType(str, Enum):
    """Catalog item types"""
    DATA_SOURCE = "data_source"
    DATABASE = "database"
    SCHEMA = "schema"
    TABLE = "table"
    COLUMN = "column"


@dataclass
class CatalogColumn:
    """Catalog column model"""
    name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key: bool = False
    default_value: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class CatalogTable:
    """Catalog table model"""
    name: str
    database_name: str
    data_source_id: str
    columns: List[CatalogColumn] = field(default_factory=list)
    description: Optional[str] = None
    row_count: Optional[int] = None
    size_bytes: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_scanned_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def full_name(self) -> str:
        """Get fully qualified table name"""
        return f"{self.database_name}.{self.name}"
    
    @property
    def column_count(self) -> int:
        """Get number of columns"""
        return len(self.columns)


@dataclass
class CatalogDatabase:
    """Catalog database model"""
    name: str
    data_source_id: str
    tables: List[CatalogTable] = field(default_factory=list)
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    last_scanned_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def table_count(self) -> int:
        """Get number of tables"""
        return len(self.tables)
    
    @property
    def total_row_count(self) -> int:
        """Get total row count across all tables"""
        return sum(table.row_count or 0 for table in self.tables)
    
    @property
    def total_column_count(self) -> int:
        """Get total column count across all tables"""
        return sum(table.column_count for table in self.tables)


@dataclass
class CatalogDataSource:
    """Catalog data source model"""
    id: str
    name: str
    type: str
    databases: List[CatalogDatabase] = field(default_factory=list)
    description: Optional[str] = None
    connection_status: str = "unknown"  # healthy, unhealthy, unknown
    last_scanned_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def database_count(self) -> int:
        """Get number of databases"""
        return len(self.databases)
    
    @property
    def table_count(self) -> int:
        """Get total number of tables"""
        return sum(db.table_count for db in self.databases)
    
    @property
    def total_row_count(self) -> int:
        """Get total row count across all tables"""
        return sum(db.total_row_count for db in self.databases)


@dataclass
class CatalogSearchResult:
    """Catalog search result model"""
    item_type: CatalogItemType
    name: str
    full_name: str
    description: Optional[str] = None
    data_source_name: str = ""
    database_name: str = ""
    table_name: str = ""
    tags: List[str] = field(default_factory=list)
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CatalogTree:
    """Catalog tree structure for UI"""
    data_sources: List[CatalogDataSource] = field(default_factory=list)
    total_data_sources: int = 0
    total_databases: int = 0
    total_tables: int = 0
    total_columns: int = 0
    last_updated: Optional[datetime] = None
    
    def update_statistics(self):
        """Update tree statistics"""
        self.total_data_sources = len(self.data_sources)
        self.total_databases = sum(ds.database_count for ds in self.data_sources)
        self.total_tables = sum(ds.table_count for ds in self.data_sources)
        self.total_columns = sum(db.total_column_count for ds in self.data_sources for db in ds.databases)
        self.last_updated = datetime.utcnow()


@dataclass
class CatalogStats:
    """Catalog statistics"""
    total_data_sources: int = 0
    total_databases: int = 0
    total_tables: int = 0
    total_columns: int = 0
    total_rows: int = 0
    healthy_sources: int = 0
    last_scan_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_data_sources": self.total_data_sources,
            "total_databases": self.total_databases,
            "total_tables": self.total_tables,
            "total_columns": self.total_columns,
            "total_rows": self.total_rows,
            "healthy_sources": self.healthy_sources,
            "last_scan_time": self.last_scan_time.isoformat() if self.last_scan_time else None
        } 