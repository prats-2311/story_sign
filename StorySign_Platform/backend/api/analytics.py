"""
Analytics API
Provides endpoints for analytics data collection, consent management, and reporting
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from services.enhanced_analytics_service import get_analytics_service, AnalyticsService
# from services.auth_service import get_current_user  # TODO: Implement proper auth
from core.database_service import DatabaseService
from models.analytics import EventType, ConsentType
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Simple auth dependency for now - TODO: Replace with proper auth
async def get_current_user(token: str = Depends(security)) -> Optional[Dict]:
    """Simple auth dependency - replace with proper implementation"""
    # For now, return a mock user for testing
    return {"id": "test_user_123", "role": "user"}

# Simple database service dependency - TODO: Replace with proper DI
def get_database_service() -> DatabaseService:
    """Simple database service dependency"""
    return DatabaseService()


# Pydantic models for request/response
class AnalyticsEventRequest(BaseModel):
    event_type: str = Field(..., description="Type of analytics event")
    module_name: str = Field(..., description="Module generating the event")
    event_data: Dict[str, Any] = Field(..., description="Event-specific data")
    session_id: str = Field(..., description="Session identifier")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    force_anonymous: bool = Field(False, description="Force event to be anonymous")


class ConsentRequest(BaseModel):
    consent_type: str = Field(..., description="Type of consent")
    consent_given: bool = Field(..., description="Whether consent is given")
    consent_version: str = Field("1.0", description="Version of consent agreement")


class AnalyticsQuery(BaseModel):
    start_date: Optional[datetime] = Field(None, description="Start date for analytics query")
    end_date: Optional[datetime] = Field(None, description="End date for analytics query")
    event_types: Optional[List[str]] = Field(None, description="Filter by event types")
    module_name: Optional[str] = Field(None, description="Filter by module name")
    include_anonymous: bool = Field(True, description="Include anonymous events")


class UserActionRequest(BaseModel):
    action: str = Field(..., description="Action performed by user")
    module: str = Field(..., description="Module where action occurred")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional action details")
    session_id: str = Field(..., description="Session identifier")


class PerformanceMetricRequest(BaseModel):
    metric_name: str = Field(..., description="Name of the performance metric")
    metric_value: float = Field(..., description="Value of the metric")
    module: str = Field(..., description="Module generating the metric")
    session_id: str = Field(..., description="Session identifier")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional metric data")


class LearningEventRequest(BaseModel):
    event_type: str = Field(..., description="Type of learning event")
    session_id: str = Field(..., description="Session identifier")
    story_id: Optional[str] = Field(None, description="Story identifier")
    sentence_index: Optional[int] = Field(None, description="Sentence index")
    score: Optional[float] = Field(None, description="Performance score")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional event data")


@router.post("/events", summary="Track Analytics Event")
async def track_event(
    event_request: AnalyticsEventRequest,
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """Track a general analytics event"""
    try:
        # Get analytics service instance
        analytics_service = get_analytics_service(get_database_service())
        
        user_id = current_user.get('id') if current_user else None
        
        success = await analytics_service.track_event(
            user_id=user_id,
            session_id=event_request.session_id,
            event_type=event_request.event_type,
            module_name=event_request.module_name,
            event_data=event_request.event_data,
            processing_time_ms=event_request.processing_time_ms,
            force_anonymous=event_request.force_anonymous
        )
        
        if success:
            return {"status": "success", "message": "Event tracked successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to track event")
            
    except Exception as e:
        logger.error(f"Error tracking analytics event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/user-action", summary="Track User Action")
async def track_user_action(
    action_request: UserActionRequest,
    current_user: Dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(lambda: get_analytics_service(get_database_service()))
):
    """Track a user action event"""
    try:
        success = await analytics_service.track_user_action(
            user_id=current_user['id'],
            session_id=action_request.session_id,
            action=action_request.action,
            module=action_request.module,
            details=action_request.details
        )
        
        if success:
            return {"status": "success", "message": "User action tracked successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to track user action")
            
    except Exception as e:
        logger.error(f"Error tracking user action: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/performance", summary="Track Performance Metric")
async def track_performance_metric(
    metric_request: PerformanceMetricRequest,
    current_user: Optional[Dict] = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(lambda: get_analytics_service(get_database_service()))
):
    """Track a performance metric"""
    try:
        user_id = current_user.get('id') if current_user else None
        
        success = await analytics_service.track_performance_metric(
            user_id=user_id,
            session_id=metric_request.session_id,
            metric_name=metric_request.metric_name,
            metric_value=metric_request.metric_value,
            module=metric_request.module,
            additional_data=metric_request.additional_data
        )
        
        if success:
            return {"status": "success", "message": "Performance metric tracked successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to track performance metric")
            
    except Exception as e:
        logger.error(f"Error tracking performance metric: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/learning", summary="Track Learning Event")
async def track_learning_event(
    learning_request: LearningEventRequest,
    current_user: Dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(lambda: get_analytics_service(get_database_service()))
):
    """Track a learning-specific event"""
    try:
        success = await analytics_service.track_learning_event(
            user_id=current_user['id'],
            session_id=learning_request.session_id,
            event_type=learning_request.event_type,
            story_id=learning_request.story_id,
            sentence_index=learning_request.sentence_index,
            score=learning_request.score,
            additional_data=learning_request.additional_data
        )
        
        if success:
            return {"status": "success", "message": "Learning event tracked successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to track learning event")
            
    except Exception as e:
        logger.error(f"Error tracking learning event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}", summary="Get User Analytics")
async def get_user_analytics(
    user_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    event_types: Optional[str] = Query(None, description="Comma-separated event types"),
    include_raw_events: bool = Query(False, description="Include raw event data"),
    current_user: Dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(lambda: get_analytics_service(get_database_service()))
):
    """Get analytics data for a specific user"""
    try:
        # Check if user can access this data (self or admin)
        if current_user['id'] != user_id and current_user.get('role') != 'admin':
            raise HTTPException(status_code=403, detail="Access denied")
        
        event_types_list = event_types.split(',') if event_types else None
        
        analytics_data = await analytics_service.get_user_analytics(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            event_types=event_types_list,
            include_raw_events=include_raw_events
        )
        
        return analytics_data
        
    except Exception as e:
        logger.error(f"Error getting user analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platform", summary="Get Platform Analytics")
async def get_platform_analytics(
    start_date: datetime = Query(..., description="Start date for analytics"),
    end_date: datetime = Query(..., description="End date for analytics"),
    module_name: Optional[str] = Query(None, description="Filter by module name"),
    include_anonymous: bool = Query(True, description="Include anonymous events"),
    current_user: Dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(lambda: get_analytics_service(get_database_service()))
):
    """Get platform-wide analytics (admin only)"""
    try:
        # Check admin permissions
        if current_user.get('role') != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        analytics_data = await analytics_service.get_platform_analytics(
            start_date=start_date,
            end_date=end_date,
            module_name=module_name,
            include_anonymous=include_anonymous
        )
        
        return analytics_data
        
    except Exception as e:
        logger.error(f"Error getting platform analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consent", summary="Manage User Consent")
async def manage_consent(
    consent_request: ConsentRequest,
    current_user: Dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(lambda: get_analytics_service(get_database_service()))
):
    """Manage user consent for analytics collection"""
    try:
        consent = await analytics_service.manage_user_consent(
            user_id=current_user['id'],
            consent_type=consent_request.consent_type,
            consent_given=consent_request.consent_given,
            consent_version=consent_request.consent_version
        )
        
        return {
            "status": "success",
            "message": f"Consent {'granted' if consent_request.consent_given else 'revoked'} successfully",
            "consent": consent.to_dict()
        }
        
    except Exception as e:
        logger.error(f"Error managing consent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/consent", summary="Get User Consents")
async def get_user_consents(
    current_user: Dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(lambda: get_analytics_service(get_database_service()))
):
    """Get all consents for the current user"""
    try:
        consents = await analytics_service.get_user_consents(current_user['id'])
        return {"consents": consents}
        
    except Exception as e:
        logger.error(f"Error getting user consents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export", summary="Export Analytics Data")
async def export_analytics_data(
    start_date: datetime = Query(..., description="Start date for export"),
    end_date: datetime = Query(..., description="End date for export"),
    format: str = Query("json", description="Export format (json, csv, xlsx)"),
    include_anonymous: bool = Query(True, description="Include anonymous events"),
    include_personal_data: bool = Query(False, description="Include personal data"),
    event_types: Optional[str] = Query(None, description="Comma-separated event types"),
    modules: Optional[str] = Query(None, description="Comma-separated module names"),
    aggregation_level: str = Query("raw", description="Aggregation level"),
    current_user: Dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(lambda: get_analytics_service(get_database_service()))
):
    """Export analytics data in various formats for research and analysis"""
    try:
        # Check permissions for personal data export
        if include_personal_data and current_user.get('role') not in ['admin', 'researcher']:
            raise HTTPException(status_code=403, detail="Insufficient permissions for personal data export")
        
        # Parse filter parameters
        event_types_list = event_types.split(',') if event_types else None
        modules_list = modules.split(',') if modules else None
        
        # Get analytics data
        if current_user.get('role') == 'admin':
            # Admin can export platform-wide data
            analytics_data = await analytics_service.get_platform_analytics(
                start_date=start_date,
                end_date=end_date,
                include_anonymous=include_anonymous
            )
        else:
            # Regular users can only export their own data
            analytics_data = await analytics_service.get_user_analytics(
                user_id=current_user['id'],
                start_date=start_date,
                end_date=end_date,
                event_types=event_types_list,
                include_raw_events=True
            )
        
        # Format data based on requested format
        if format.lower() == 'json':
            from fastapi.responses import JSONResponse
            return JSONResponse(content=analytics_data)
        elif format.lower() == 'csv':
            import csv
            import io
            from fastapi.responses import StreamingResponse
            
            output = io.StringIO()
            if 'events' in analytics_data:
                events = analytics_data['events']
                if events:
                    writer = csv.DictWriter(output, fieldnames=events[0].keys())
                    writer.writeheader()
                    writer.writerows(events)
            
            output.seek(0)
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode()),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=analytics_export_{start_date.strftime('%Y%m%d')}.csv"}
            )
        else:
            # Default to JSON for unsupported formats
            from fastapi.responses import JSONResponse
            return JSONResponse(content=analytics_data)
        
    except Exception as e:
        logger.error(f"Error exporting analytics data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/user", summary="Export User Data")
async def export_user_data(
    current_user: Dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(lambda: get_analytics_service(get_database_service()))
):
    """Export all analytics data for the current user (GDPR compliance)"""
    try:
        export_data = await analytics_service.export_user_data(current_user['id'])
        return export_data
        
    except Exception as e:
        logger.error(f"Error exporting user data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/user-data", summary="Delete User Data")
async def delete_user_data(
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(lambda: get_analytics_service(get_database_service()))
):
    """Delete all analytics data for the current user (GDPR right to be forgotten)"""
    try:
        # Run deletion in background to avoid timeout
        background_tasks.add_task(
            analytics_service.delete_user_data,
            current_user['id']
        )
        
        return {
            "status": "success",
            "message": "User data deletion initiated. This process may take a few minutes."
        }
        
    except Exception as e:
        logger.error(f"Error initiating user data deletion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/event-types", summary="Get Available Event Types")
async def get_event_types():
    """Get list of available analytics event types"""
    return {
        "event_types": [event_type.value for event_type in EventType],
        "consent_types": [consent_type.value for consent_type in ConsentType]
    }


@router.get("/health", summary="Analytics Service Health Check")
async def health_check(
    analytics_service: AnalyticsService = Depends(lambda: get_analytics_service(get_database_service()))
):
    """Check the health of the analytics service"""
    try:
        # Simple health check - verify service is running
        queue_size = analytics_service._event_queue.qsize()
        
        return {
            "status": "healthy",
            "queue_size": queue_size,
            "processing_active": analytics_service._processing_task is not None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Analytics health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }