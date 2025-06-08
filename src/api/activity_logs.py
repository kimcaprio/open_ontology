"""
Activity Log API endpoints
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import Response

from loguru import logger

from src.models.activity_log import (
    ActivityLog, ActivityLogQueryRequest, ActivityLogResponse,
    ActivitySummary, ActivityType, ActivityStatus
)
from src.services.activity_log_service import activity_log_service

router = APIRouter(tags=["activity-logs"])


def get_user_info(request: Request) -> tuple:
    """Extract user info from request"""
    user_id = "anonymous"  # Default for demo
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return user_id, ip_address, user_agent


@router.get("/activity-logs", response_model=ActivityLogResponse)
async def query_activity_logs(
    http_request: Request,
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    page: int = Query(1, description="Page number"),
    page_size: int = Query(50, description="Page size")
):
    """Query activity logs with filters"""
    try:
        logger.info(f"Querying activity logs with filters: user_id={user_id}, activity_type={activity_type}")
        
        # Validate activity type if provided
        activity_type_enum = None
        if activity_type:
            try:
                activity_type_enum = ActivityType(activity_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid activity type: {activity_type}")
        
        # Validate status if provided
        status_enum = None
        if status:
            try:
                status_enum = ActivityStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        query = ActivityLogQueryRequest(
            user_id=user_id,
            activity_type=activity_type_enum,
            status=status_enum,
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size
        )
        
        response = activity_log_service.query_logs(query)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying activity logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity-logs/recent")
async def get_recent_activities(
    http_request: Request,
    limit: int = Query(10, description="Number of recent activities to return"),
    user_id: Optional[str] = Query(None, description="Filter by user ID")
):
    """Get recent activities"""
    try:
        logger.info(f"Getting recent activities: limit={limit}, user_id={user_id}")
        
        activities = activity_log_service.get_recent_activities(limit, user_id)
        return {"recent_activities": activities, "total": len(activities)}
        
    except Exception as e:
        logger.error(f"Error getting recent activities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity-logs/summary", response_model=ActivitySummary)
async def get_activity_summary(
    http_request: Request,
    days: int = Query(7, description="Number of days for summary")
):
    """Get activity summary for the last N days"""
    try:
        logger.info(f"Getting activity summary for last {days} days")
        
        summary = activity_log_service.get_activity_summary(days)
        return summary
        
    except Exception as e:
        logger.error(f"Error getting activity summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity-logs/user/{user_id}/stats")
async def get_user_activity_stats(
    user_id: str,
    http_request: Request,
    days: int = Query(30, description="Number of days for statistics")
):
    """Get activity statistics for a specific user"""
    try:
        logger.info(f"Getting activity stats for user {user_id} for last {days} days")
        
        stats = activity_log_service.get_user_activity_stats(user_id, days)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting user activity stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity-logs/types")
async def get_activity_types():
    """Get available activity types"""
    try:
        types = [
            {
                "value": activity_type.value,
                "label": activity_type.value.replace("_", " ").title(),
                "description": f"Activities related to {activity_type.value.replace('_', ' ')}"
            }
            for activity_type in ActivityType
        ]
        return {"activity_types": types}
        
    except Exception as e:
        logger.error(f"Error getting activity types: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity-logs/export")
async def export_activity_logs(
    http_request: Request,
    format: str = Query("json", description="Export format (json, csv)"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    page_size: int = Query(1000, description="Maximum records to export")
):
    """Export activity logs in specified format"""
    try:
        logger.info(f"Exporting activity logs in format: {format}")
        
        # Validate format
        if format not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
        
        # Validate activity type if provided
        activity_type_enum = None
        if activity_type:
            try:
                activity_type_enum = ActivityType(activity_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid activity type: {activity_type}")
        
        # Validate status if provided
        status_enum = None
        if status:
            try:
                status_enum = ActivityStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        query = ActivityLogQueryRequest(
            user_id=user_id,
            activity_type=activity_type_enum,
            status=status_enum,
            start_date=start_date,
            end_date=end_date,
            page=1,
            page_size=page_size
        )
        
        exported_data = activity_log_service.export_logs(query, format)
        
        # Set appropriate content type and filename
        media_type = "application/json" if format == "json" else "text/csv"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"activity_logs_{timestamp}.{format}"
        
        return Response(
            content=exported_data,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting activity logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/activity-logs/cleanup")
async def cleanup_old_logs(
    http_request: Request,
    days_to_keep: int = Query(90, description="Number of days to keep logs")
):
    """Clean up old log entries"""
    try:
        logger.info(f"Cleaning up logs older than {days_to_keep} days")
        
        removed_count = activity_log_service.cleanup_old_logs(days_to_keep)
        
        return {
            "message": f"Cleaned up {removed_count} old log entries",
            "removed_count": removed_count,
            "days_to_keep": days_to_keep
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity-logs/dashboard")
async def get_activity_dashboard(http_request: Request):
    """Get activity dashboard data"""
    try:
        logger.info("Getting activity dashboard data")
        
        # Get various statistics for dashboard
        summary_7d = activity_log_service.get_activity_summary(7)
        summary_30d = activity_log_service.get_activity_summary(30)
        recent_activities = activity_log_service.get_recent_activities(20)
        
        # Calculate trends
        total_7d = summary_7d.total_activities
        total_30d = summary_30d.total_activities
        avg_daily_30d = total_30d / 30 if total_30d > 0 else 0
        avg_daily_7d = total_7d / 7 if total_7d > 0 else 0
        
        trend = "up" if avg_daily_7d > avg_daily_30d else "down" if avg_daily_7d < avg_daily_30d else "stable"
        
        return {
            "summary_7d": summary_7d,
            "summary_30d": summary_30d,
            "recent_activities": recent_activities,
            "trends": {
                "avg_daily_7d": round(avg_daily_7d, 2),
                "avg_daily_30d": round(avg_daily_30d, 2),
                "trend": trend
            },
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting activity dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 