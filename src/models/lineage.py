"""
Data Lineage Models
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class LineageEventType(str, Enum):
    """Types of lineage events"""
    START = "START"
    COMPLETE = "COMPLETE" 
    FAIL = "FAIL"
    ABORT = "ABORT"
    OTHER = "OTHER"


class DatasetType(str, Enum):
    """Types of datasets"""
    TABLE = "table"
    FILE = "file"
    STREAM = "stream"
    VIEW = "view"
    API = "api"


class JobType(str, Enum):
    """Types of jobs/processes"""
    ETL = "etl"
    QUERY = "query"
    TRANSFORM = "transform"
    COPY = "copy"
    SYNC = "sync"
    PIPELINE = "pipeline"


class LineageNamespace(BaseModel):
    """Namespace for organizing lineage entities"""
    name: str = Field(..., description="Namespace name")
    
    
class LineageDataset(BaseModel):
    """Dataset in lineage graph"""
    namespace: str = Field(..., description="Dataset namespace")
    name: str = Field(..., description="Dataset name")
    type: DatasetType = Field(default=DatasetType.TABLE, description="Dataset type")
    schema_fields: Optional[List[Dict[str, Any]]] = Field(default=None, description="Schema information")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional properties")
    
    @property
    def qualified_name(self) -> str:
        """Get fully qualified dataset name"""
        return f"{self.namespace}.{self.name}"


class LineageJob(BaseModel):
    """Job/Process in lineage graph"""
    namespace: str = Field(..., description="Job namespace")
    name: str = Field(..., description="Job name") 
    type: JobType = Field(default=JobType.ETL, description="Job type")
    description: Optional[str] = Field(default=None, description="Job description")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional properties")
    
    @property
    def qualified_name(self) -> str:
        """Get fully qualified job name"""
        return f"{self.namespace}.{self.name}"


class LineageRun(BaseModel):
    """Job run instance"""
    run_id: UUID = Field(default_factory=uuid4, description="Unique run ID")
    job: LineageJob = Field(..., description="Associated job")
    status: LineageEventType = Field(..., description="Run status")
    started_at: datetime = Field(..., description="Run start time")
    ended_at: Optional[datetime] = Field(default=None, description="Run end time")
    input_datasets: List[LineageDataset] = Field(default_factory=list, description="Input datasets")
    output_datasets: List[LineageDataset] = Field(default_factory=list, description="Output datasets")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Run properties")


class LineageEvent(BaseModel):
    """OpenLineage event"""
    event_type: LineageEventType = Field(..., description="Event type")
    event_time: datetime = Field(default_factory=datetime.now, description="Event timestamp")
    run: LineageRun = Field(..., description="Run information")
    producer: str = Field(default="ontology-platform", description="Event producer")
    schema_url: str = Field(
        default="https://openlineage.io/spec/1-0-5/OpenLineage.json",
        description="OpenLineage schema URL"
    )


class LineageGraph(BaseModel):
    """Complete lineage graph representation"""
    datasets: Dict[str, LineageDataset] = Field(default_factory=dict, description="All datasets")
    jobs: Dict[str, LineageJob] = Field(default_factory=dict, description="All jobs")
    runs: List[LineageRun] = Field(default_factory=list, description="All runs")
    relationships: List[Dict[str, str]] = Field(default_factory=list, description="Dataset relationships")


class LineageQueryRequest(BaseModel):
    """Request for lineage query"""
    dataset_name: Optional[str] = Field(default=None, description="Dataset to trace")
    job_name: Optional[str] = Field(default=None, description="Job to trace")
    direction: str = Field(default="both", description="Direction: upstream, downstream, or both")
    depth: int = Field(default=3, description="Maximum depth to traverse")
    include_schema: bool = Field(default=True, description="Include schema information")


class LineageQueryResponse(BaseModel):
    """Response for lineage query"""
    query: LineageQueryRequest = Field(..., description="Original query")
    graph: LineageGraph = Field(..., description="Resulting lineage graph")
    total_datasets: int = Field(..., description="Total datasets found")
    total_jobs: int = Field(..., description="Total jobs found")
    execution_time_ms: float = Field(..., description="Query execution time")


class ColumnLineage(BaseModel):
    """Column-level lineage information"""
    source_dataset: str = Field(..., description="Source dataset")
    source_column: str = Field(..., description="Source column")
    target_dataset: str = Field(..., description="Target dataset")
    target_column: str = Field(..., description="Target column")
    transformation: Optional[str] = Field(default=None, description="Transformation applied")
    job_name: str = Field(..., description="Job that created this lineage")


class LineageMetrics(BaseModel):
    """Lineage metrics and statistics"""
    total_datasets: int = Field(..., description="Total number of datasets")
    total_jobs: int = Field(..., description="Total number of jobs") 
    total_runs: int = Field(..., description="Total number of runs")
    active_jobs: int = Field(..., description="Currently active jobs")
    failed_runs: int = Field(..., description="Failed runs in last 24h")
    avg_execution_time: float = Field(..., description="Average job execution time")
    last_updated: datetime = Field(..., description="Last metrics update")


# Demo Data Templates
DEMO_DATASETS = [
    LineageDataset(
        namespace="production",
        name="customers",
        type=DatasetType.TABLE,
        schema_fields=[
            {"name": "customer_id", "type": "INTEGER"},
            {"name": "email", "type": "VARCHAR(255)"},
            {"name": "first_name", "type": "VARCHAR(100)"},
            {"name": "last_name", "type": "VARCHAR(100)"}
        ],
        properties={"source": "postgresql", "location": "customers_table"}
    ),
    LineageDataset(
        namespace="production", 
        name="orders",
        type=DatasetType.TABLE,
        schema_fields=[
            {"name": "order_id", "type": "INTEGER"},
            {"name": "customer_id", "type": "INTEGER"},
            {"name": "order_total", "type": "DECIMAL(10,2)"},
            {"name": "order_date", "type": "DATE"}
        ],
        properties={"source": "postgresql", "location": "orders_table"}
    ),
    LineageDataset(
        namespace="analytics",
        name="customer_analytics",
        type=DatasetType.TABLE,
        schema_fields=[
            {"name": "customer_id", "type": "INTEGER"},
            {"name": "total_orders", "type": "INTEGER"},
            {"name": "total_spent", "type": "DECIMAL(12,2)"},
            {"name": "last_order_date", "type": "DATE"}
        ],
        properties={"source": "data_warehouse", "location": "customer_analytics_view"}
    )
]

DEMO_JOBS = [
    LineageJob(
        namespace="etl",
        name="customer_data_sync",
        type=JobType.ETL,
        description="Sync customer data from operational database",
        properties={"schedule": "hourly", "owner": "data-team"}
    ),
    LineageJob(
        namespace="analytics",
        name="customer_analytics_pipeline", 
        type=JobType.TRANSFORM,
        description="Generate customer analytics from raw data",
        properties={"schedule": "daily", "owner": "analytics-team"}
    )
] 