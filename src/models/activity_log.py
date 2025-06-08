"""
Activity Log Models
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field


class ActivityType(str, Enum):
    """Types of user activities"""
    PAGE_VIEW = "page_view"
    ONTOLOGY_CREATE = "ontology_create"
    ONTOLOGY_UPDATE = "ontology_update"
    ONTOLOGY_DELETE = "ontology_delete"
    ONTOLOGY_VIEW = "ontology_view"
    AI_SUGGESTION_GENERATE = "ai_suggestion_generate"
    AI_SUGGESTION_APPLY = "ai_suggestion_apply"
    DATA_SOURCE_CONNECT = "data_source_connect"
    DATA_SOURCE_TEST = "data_source_test"
    DATA_ACCESS = "data_access"
    CATALOG_SEARCH = "catalog_search"
    CATALOG_VIEW = "catalog_view"
    LINEAGE_QUERY = "lineage_query"
    LINEAGE_EXPORT = "lineage_export"
    SYSTEM_STATUS_CHECK = "system_status_check"
    SYSTEM_CONFIG = "system_config"
    CHAT_QUERY = "chat_query"


class ActivityStatus(str, Enum):
    """Activity execution status"""
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"


class ActivityLog(BaseModel):
    """Activity log entry"""
    id: str = Field(..., description="Activity ID")
    user_id: Optional[str] = Field(default="anonymous", description="User ID")
    activity_type: ActivityType = Field(..., description="Type of activity")
    status: ActivityStatus = Field(..., description="Activity status")
    resource_type: Optional[str] = Field(default=None, description="Resource type involved")
    resource_id: Optional[str] = Field(default=None, description="Resource ID involved")
    description: str = Field(..., description="Activity description")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional activity details")
    ip_address: Optional[str] = Field(default=None, description="User IP address")
    user_agent: Optional[str] = Field(default=None, description="User agent")
    execution_time_ms: Optional[float] = Field(default=None, description="Execution time in milliseconds")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Activity timestamp")


class ActivityLogRequest(BaseModel):
    """Request to log an activity"""
    activity_type: ActivityType = Field(..., description="Type of activity")
    description: str = Field(..., description="Activity description")
    resource_type: Optional[str] = Field(default=None, description="Resource type involved")
    resource_id: Optional[str] = Field(default=None, description="Resource ID involved")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional activity details")
    execution_time_ms: Optional[float] = Field(default=None, description="Execution time in milliseconds")


class ActivityLogQueryRequest(BaseModel):
    """Request to query activity logs"""
    user_id: Optional[str] = Field(default=None, description="Filter by user ID")
    activity_type: Optional[ActivityType] = Field(default=None, description="Filter by activity type")
    status: Optional[ActivityStatus] = Field(default=None, description="Filter by status")
    resource_type: Optional[str] = Field(default=None, description="Filter by resource type")
    start_date: Optional[datetime] = Field(default=None, description="Start date filter")
    end_date: Optional[datetime] = Field(default=None, description="End date filter")
    page: int = Field(default=1, description="Page number")
    page_size: int = Field(default=50, description="Page size")


class ActivityLogResponse(BaseModel):
    """Response containing activity logs"""
    logs: List[ActivityLog] = Field(..., description="Activity logs")
    total: int = Field(..., description="Total number of logs")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")


class ActivitySummary(BaseModel):
    """Activity summary statistics"""
    total_activities: int = Field(..., description="Total number of activities")
    activities_by_type: Dict[str, int] = Field(..., description="Activities grouped by type")
    activities_by_status: Dict[str, int] = Field(..., description="Activities grouped by status")
    recent_activities: List[ActivityLog] = Field(..., description="Recent activities")
    top_resources: List[Dict[str, Any]] = Field(..., description="Most accessed resources")
    period_start: datetime = Field(..., description="Summary period start")
    period_end: datetime = Field(..., description="Summary period end") 