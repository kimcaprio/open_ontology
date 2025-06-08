"""
Activity Log Service
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4
from collections import defaultdict, Counter

from src.config.logging_config import get_service_logger

from src.models.activity_log import (
    ActivityLog, ActivityLogRequest, ActivityLogQueryRequest, ActivityLogResponse,
    ActivitySummary, ActivityType, ActivityStatus
)


class ActivityLogService:
    """Service for managing user activity logs"""
    
    def __init__(self):
        # Initialize service logger
        self.logger = get_service_logger("activity")
        
        # In-memory storage for demo purposes
        # In production, this would be replaced with a database
        self.logs: Dict[str, ActivityLog] = {}
        self.logs_by_timestamp: List[ActivityLog] = []
        
        self.logger.info("Activity log service initialized")
    
    def log_activity(
        self, 
        request: ActivityLogRequest, 
        user_id: str = "anonymous", 
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLog:
        """Log a user activity"""
        start_time = time.time()
        self.logger.log_function_start(
            "log_activity",
            user_id=user_id,
            activity_type=request.activity_type.value,
            resource_type=request.resource_type,
            resource_id=request.resource_id
        )
        
        try:
            activity_id = str(uuid4())
            
            # Determine status based on execution time and error presence
            status = ActivityStatus.SUCCESS
            if request.execution_time_ms is not None and request.execution_time_ms > 10000:
                # Mark as slow if over 10 seconds
                status = ActivityStatus.IN_PROGRESS
            
            activity = ActivityLog(
                id=activity_id,
                user_id=user_id,
                activity_type=request.activity_type,
                status=status,
                resource_type=request.resource_type,
                resource_id=request.resource_id,
                description=request.description,
                details=request.details,
                ip_address=ip_address,
                user_agent=user_agent,
                execution_time_ms=request.execution_time_ms
            )
            
            # Store activity
            self.logs[activity_id] = activity
            self.logs_by_timestamp.append(activity)
            self.logs_by_timestamp.sort(key=lambda x: x.timestamp, reverse=True)
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "log_activity",
                result=activity,
                execution_time=execution_time,
                activity_id=activity_id,
                user_id=user_id,
                activity_type=request.activity_type.value,
                total_logs=len(self.logs)
            )
            
            return activity
            
        except Exception as e:
            self.logger.log_function_error("log_activity", e, user_id=user_id)
            raise
    
    def log_page_view(self, page: str, user_id: str = "anonymous", ip_address: Optional[str] = None) -> ActivityLog:
        """Convenience method to log page views"""
        start_time = time.time()
        self.logger.log_function_start("log_page_view", user_id=user_id, page=page)
        
        try:
            request = ActivityLogRequest(
                activity_type=ActivityType.PAGE_VIEW,
                description=f"Viewed page: {page}",
                resource_type="page",
                resource_id=page,
                details={"page": page}
            )
            
            result = self.log_activity(request, user_id, ip_address)
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "log_page_view",
                result=f"Page view logged: {page}",
                execution_time=execution_time,
                user_id=user_id,
                page=page
            )
            
            return result
            
        except Exception as e:
            self.logger.log_function_error("log_page_view", e, user_id=user_id, page=page)
            raise
    
    def log_error(
        self, 
        activity_type: ActivityType, 
        error_message: str, 
        user_id: str = "anonymous",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> ActivityLog:
        """Convenience method to log errors"""
        start_time = time.time()
        self.logger.log_function_start(
            "log_error",
            user_id=user_id,
            activity_type=activity_type.value,
            error_message=error_message
        )
        
        try:
            activity_id = str(uuid4())
            
            activity = ActivityLog(
                id=activity_id,
                user_id=user_id,
                activity_type=activity_type,
                status=ActivityStatus.FAILED,
                resource_type=resource_type,
                resource_id=resource_id,
                description=f"Error in {activity_type.value}",
                details={"error": error_message},
                error_message=error_message
            )
            
            self.logs[activity_id] = activity
            self.logs_by_timestamp.append(activity)
            self.logs_by_timestamp.sort(key=lambda x: x.timestamp, reverse=True)
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "log_error",
                result=f"Error activity logged: {activity_type.value}",
                execution_time=execution_time,
                activity_id=activity_id,
                user_id=user_id,
                activity_type=activity_type.value,
                error_message=error_message,
                total_logs=len(self.logs)
            )
            
            return activity
            
        except Exception as e:
            self.logger.log_function_error("log_error", e, user_id=user_id, activity_type=activity_type.value)
            raise
    
    def query_logs(self, query: ActivityLogQueryRequest) -> ActivityLogResponse:
        """Query activity logs with filters"""
        start_time = time.time()
        self.logger.log_function_start(
            "query_logs",
            page=query.page,
            page_size=query.page_size,
            user_id=query.user_id,
            activity_type=query.activity_type.value if query.activity_type else None,
            status=query.status.value if query.status else None
        )
        
        try:
            filtered_logs = list(self.logs_by_timestamp)
            original_count = len(filtered_logs)
            
            # Apply filters
            if query.user_id:
                filtered_logs = [log for log in filtered_logs if log.user_id == query.user_id]
            
            if query.activity_type:
                filtered_logs = [log for log in filtered_logs if log.activity_type == query.activity_type]
            
            if query.status:
                filtered_logs = [log for log in filtered_logs if log.status == query.status]
            
            if query.resource_type:
                filtered_logs = [log for log in filtered_logs if log.resource_type == query.resource_type]
            
            if query.start_date:
                filtered_logs = [log for log in filtered_logs if log.timestamp >= query.start_date]
            
            if query.end_date:
                filtered_logs = [log for log in filtered_logs if log.timestamp <= query.end_date]
            
            # Pagination
            total = len(filtered_logs)
            start_idx = (query.page - 1) * query.page_size
            end_idx = start_idx + query.page_size
            paginated_logs = filtered_logs[start_idx:end_idx]
            
            response = ActivityLogResponse(
                logs=paginated_logs,
                total=total,
                page=query.page,
                page_size=query.page_size
            )
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "query_logs",
                result=response,
                execution_time=execution_time,
                original_count=original_count,
                filtered_count=total,
                returned_count=len(paginated_logs),
                filters_applied=sum([
                    bool(query.user_id),
                    bool(query.activity_type),
                    bool(query.status),
                    bool(query.resource_type),
                    bool(query.start_date),
                    bool(query.end_date)
                ])
            )
            
            return response
            
        except Exception as e:
            self.logger.log_function_error("query_logs", e)
            raise
    
    def get_recent_activities(self, limit: int = 10, user_id: Optional[str] = None) -> List[ActivityLog]:
        """Get recent activities"""
        logs = self.logs_by_timestamp
        
        if user_id:
            logs = [log for log in logs if log.user_id == user_id]
        
        return logs[:limit]
    
    def get_activity_summary(self, days: int = 7) -> ActivitySummary:
        """Get activity summary for the last N days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Filter logs within date range
        period_logs = [
            log for log in self.logs_by_timestamp 
            if start_date <= log.timestamp <= end_date
        ]
        
        # Calculate statistics
        total_activities = len(period_logs)
        
        activities_by_type = Counter(log.activity_type.value for log in period_logs)
        activities_by_status = Counter(log.status.value for log in period_logs)
        
        # Top resources (most accessed)
        resource_counter = defaultdict(int)
        for log in period_logs:
            if log.resource_type and log.resource_id:
                key = f"{log.resource_type}:{log.resource_id}"
                resource_counter[key] += 1
        
        top_resources = [
            {"resource": resource, "access_count": count}
            for resource, count in resource_counter.most_common(10)
        ]
        
        # Recent activities (last 5)
        recent_activities = period_logs[:5]
        
        return ActivitySummary(
            total_activities=total_activities,
            activities_by_type=dict(activities_by_type),
            activities_by_status=dict(activities_by_status),
            recent_activities=recent_activities,
            top_resources=top_resources,
            period_start=start_date,
            period_end=end_date
        )
    
    def get_user_activity_stats(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get activity statistics for a specific user"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        user_logs = [
            log for log in self.logs_by_timestamp 
            if log.user_id == user_id and start_date <= log.timestamp <= end_date
        ]
        
        if not user_logs:
            return {
                "user_id": user_id,
                "period_days": days,
                "total_activities": 0,
                "activities_by_type": {},
                "activities_by_day": {},
                "most_active_day": None,
                "last_activity": None
            }
        
        # Activities by type
        activities_by_type = Counter(log.activity_type.value for log in user_logs)
        
        # Activities by day
        activities_by_day = defaultdict(int)
        for log in user_logs:
            day_key = log.timestamp.strftime("%Y-%m-%d")
            activities_by_day[day_key] += 1
        
        # Most active day
        most_active_day = max(activities_by_day.items(), key=lambda x: x[1]) if activities_by_day else None
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_activities": len(user_logs),
            "activities_by_type": dict(activities_by_type),
            "activities_by_day": dict(activities_by_day),
            "most_active_day": most_active_day,
            "last_activity": user_logs[0].timestamp.isoformat() if user_logs else None
        }
    
    def cleanup_old_logs(self, days_to_keep: int = 90):
        """Clean up old log entries"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Count logs to be removed
        old_logs = [log for log in self.logs_by_timestamp if log.timestamp < cutoff_date]
        
        if old_logs:
            # Remove from storage
            for log in old_logs:
                if log.id in self.logs:
                    del self.logs[log.id]
            
            # Rebuild sorted list
            self.logs_by_timestamp = [
                log for log in self.logs_by_timestamp 
                if log.timestamp >= cutoff_date
            ]
            
            logger.info(f"Cleaned up {len(old_logs)} old log entries older than {days_to_keep} days")
        
        return len(old_logs)
    
    def export_logs(self, query: ActivityLogQueryRequest, format: str = "json") -> str:
        """Export activity logs in specified format"""
        response = self.query_logs(query)
        
        if format == "json":
            return ActivityLogResponse.model_validate(response).model_dump_json(indent=2)
        elif format == "csv":
            return self._export_csv(response.logs)
        else:
            return ""
    
    def _export_csv(self, logs: List[ActivityLog]) -> str:
        """Export logs as CSV"""
        if not logs:
            return "No logs to export"
        
        csv_lines = [
            "timestamp,user_id,activity_type,status,resource_type,resource_id,description,execution_time_ms"
        ]
        
        for log in logs:
            csv_lines.append(
                f"{log.timestamp.isoformat()},"
                f"{log.user_id},"
                f"{log.activity_type.value},"
                f"{log.status.value},"
                f"{log.resource_type or ''},"
                f"{log.resource_id or ''},"
                f"\"{log.description}\","
                f"{log.execution_time_ms or ''}"
            )
        
        return "\n".join(csv_lines)


# Global service instance
activity_log_service = ActivityLogService() 