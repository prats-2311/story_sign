"""
Simple Analytics API
Simplified version for testing analytics functionality
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Simple request models
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

# Simple in-memory storage for testing
analytics_events = []
user_consents = {}

@router.post("/events", summary="Track Analytics Event")
async def track_event(event_request: AnalyticsEventRequest):
    """Track a general analytics event"""
    try:
        # Create event record
        event = {
            "id": len(analytics_events) + 1,
            "event_type": event_request.event_type,
            "module_name": event_request.module_name,
            "event_data": event_request.event_data,
            "session_id": event_request.session_id,
            "processing_time_ms": event_request.processing_time_ms,
            "force_anonymous": event_request.force_anonymous,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store event
        analytics_events.append(event)
        
        logger.info(f"Tracked analytics event: {event_request.event_type}")
        return {"status": "success", "message": "Event tracked successfully", "event_id": event["id"]}
        
    except Exception as e:
        logger.error(f"Error tracking analytics event: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/consent", summary="Manage User Consent")
async def manage_consent(consent_request: ConsentRequest):
    """Manage user consent for analytics collection"""
    try:
        # Store consent (using session_id as user identifier for testing)
        user_id = "test_user"  # In real implementation, get from auth
        
        if user_id not in user_consents:
            user_consents[user_id] = {}
        
        user_consents[user_id][consent_request.consent_type] = {
            "consent_given": consent_request.consent_given,
            "consent_version": consent_request.consent_version,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Updated consent for user {user_id}: {consent_request.consent_type} = {consent_request.consent_given}")
        
        return {
            "status": "success",
            "message": f"Consent {'granted' if consent_request.consent_given else 'revoked'} successfully"
        }
        
    except Exception as e:
        logger.error(f"Error managing consent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events", summary="Get Analytics Events")
async def get_events(limit: int = 10):
    """Get recent analytics events"""
    try:
        recent_events = analytics_events[-limit:] if analytics_events else []
        return {
            "events": recent_events,
            "total_count": len(analytics_events)
        }
    except Exception as e:
        logger.error(f"Error getting events: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/consent", summary="Get User Consents")
async def get_consents():
    """Get user consent status"""
    try:
        user_id = "test_user"  # In real implementation, get from auth
        consents = user_consents.get(user_id, {})
        return {"consents": consents}
    except Exception as e:
        logger.error(f"Error getting consents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", summary="Analytics Service Health Check")
async def health_check():
    """Check the health of the analytics service"""
    return {
        "status": "healthy",
        "events_count": len(analytics_events),
        "users_with_consent": len(user_consents),
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/event-types", summary="Get Available Event Types")
async def get_event_types():
    """Get list of available analytics event types"""
    return {
        "event_types": [
            "user_login", "user_logout", "user_registration",
            "practice_session_start", "practice_session_end", "sentence_attempt",
            "story_generated", "story_viewed", "content_shared",
            "gesture_detected", "ai_feedback_received", "error_occurred",
            "page_view", "feature_used", "plugin_activated"
        ],
        "consent_types": [
            "analytics", "research", "marketing", "performance", "social"
        ]
    }