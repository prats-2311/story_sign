"""
Privacy and GDPR compliance API endpoints
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request, Query, Body
from pydantic import BaseModel, Field
import logging

# Import with error handling
try:
    from services.privacy_service import PrivacyService
    from models.privacy import ConsentType, ConsentStatus, DataProcessingPurpose, DataRetentionPolicy
    PRIVACY_SERVICE_AVAILABLE = True
except ImportError:
    PRIVACY_SERVICE_AVAILABLE = False

try:
    from .auth import get_current_user
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

try:
    from core.database_service import DatabaseService
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/privacy", tags=["privacy"])


# Request/Response Models
class ConsentRequest(BaseModel):
    """Consent grant/withdrawal request"""
    consent_type: str = Field(..., description="Type of consent")
    action: str = Field(..., description="'grant' or 'withdraw'")
    consent_details: Optional[Dict[str, Any]] = Field(None, description="Additional consent details")
    withdrawal_reason: Optional[str] = Field(None, description="Reason for withdrawal")


class PrivacySettingsRequest(BaseModel):
    """Privacy settings update request"""
    allow_research_participation: Optional[bool] = None
    allow_analytics_tracking: Optional[bool] = None
    allow_performance_tracking: Optional[bool] = None
    allow_social_features: Optional[bool] = None
    allow_third_party_sharing: Optional[bool] = None
    allow_marketing_communications: Optional[bool] = None
    data_retention_preference: Optional[str] = None
    auto_delete_inactive_data: Optional[bool] = None
    inactive_threshold_days: Optional[int] = None
    prefer_anonymization_over_deletion: Optional[bool] = None
    anonymization_level: Optional[str] = None
    privacy_notification_email: Optional[bool] = None
    data_breach_notification: Optional[bool] = None
    policy_update_notification: Optional[bool] = None


class DataDeletionRequest(BaseModel):
    """Data deletion request"""
    request_type: str = Field(default="full_deletion", description="Type of deletion")
    deletion_scope: Optional[Dict[str, Any]] = Field(None, description="Scope of data to delete")


class DataExportRequest(BaseModel):
    """Data export request"""
    export_format: str = Field(default="json", description="Export format")
    export_scope: Optional[Dict[str, Any]] = Field(None, description="Scope of data to export")


# Dependency injection
async def get_privacy_service():
    """Get privacy service instance"""
    if not PRIVACY_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Privacy service not available")
    
    config = {
        "gdpr_enabled": True,
        "data_retention_days": 365,
        "anonymization_salt": "storysign_privacy_salt_2024"
    }
    service = PrivacyService(config=config)
    await service.initialize()
    return service


async def get_database_session():
    """Get database session"""
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    db_service = DatabaseService()
    await db_service.initialize()
    async with db_service.get_session() as session:
        yield session
    await db_service.cleanup()


async def require_authenticated_user(current_user = Depends(get_current_user)):
    """Require authenticated user for privacy endpoints"""
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Authentication not available")
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return current_user


# API Endpoints

@router.get("/dashboard")
async def get_privacy_dashboard(
    current_user = Depends(require_authenticated_user),
    privacy_service = Depends(get_privacy_service),
    db_session = Depends(get_database_session)
):
    """
    Get user privacy dashboard with consent status and settings
    
    Args:
        current_user: Current authenticated user
        privacy_service: Privacy service instance
        db_session: Database session
        
    Returns:
        Privacy dashboard data
    """
    try:
        # Get privacy settings
        privacy_settings = await privacy_service.get_privacy_settings(
            db_session, current_user.id
        )
        
        # Get consent status for all consent types
        consent_status = {}
        for consent_type in ConsentType:
            has_consent = await privacy_service.check_consent(
                db_session, current_user.id, consent_type
            )
            consent_status[consent_type.value] = has_consent
        
        # Get recent privacy actions (simplified)
        # In production, you'd query the privacy audit log
        
        return {
            "success": True,
            "privacy_dashboard": {
                "user_id": current_user.id,
                "privacy_settings": privacy_settings.__dict__ if privacy_settings else None,
                "consent_status": consent_status,
                "gdpr_rights": {
                    "right_to_access": True,
                    "right_to_rectification": True,
                    "right_to_erasure": True,
                    "right_to_portability": True,
                    "right_to_restrict_processing": True,
                    "right_to_object": True
                },
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Privacy dashboard error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load privacy dashboard")


@router.post("/consent")
async def manage_consent(
    request: ConsentRequest,
    http_request: Request,
    current_user = Depends(require_authenticated_user),
    privacy_service = Depends(get_privacy_service),
    db_session = Depends(get_database_session)
):
    """
    Grant or withdraw user consent
    
    Args:
        request: Consent management request
        http_request: HTTP request for IP/user agent
        current_user: Current authenticated user
        privacy_service: Privacy service instance
        db_session: Database session
        
    Returns:
        Consent management result
    """
    try:
        # Validate consent type
        try:
            consent_type = ConsentType(request.consent_type)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid consent type")
        
        # Get client info
        ip_address = http_request.client.host
        user_agent = http_request.headers.get("user-agent")
        
        if request.action == "grant":
            consent_record = await privacy_service.grant_consent(
                session=db_session,
                user_id=current_user.id,
                consent_type=consent_type,
                ip_address=ip_address,
                user_agent=user_agent,
                consent_details=request.consent_details
            )
            
            return {
                "success": True,
                "message": f"Consent granted for {consent_type.value}",
                "consent_id": consent_record.id,
                "granted_at": consent_record.granted_at.isoformat()
            }
            
        elif request.action == "withdraw":
            success = await privacy_service.withdraw_consent(
                session=db_session,
                user_id=current_user.id,
                consent_type=consent_type,
                withdrawal_reason=request.withdrawal_reason,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            if success:
                return {
                    "success": True,
                    "message": f"Consent withdrawn for {consent_type.value}",
                    "withdrawn_at": datetime.utcnow().isoformat()
                }
            else:
                raise HTTPException(status_code=404, detail="No active consent found to withdraw")
        
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'grant' or 'withdraw'")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Consent management error: {e}")
        raise HTTPException(status_code=500, detail="Failed to manage consent")


@router.get("/settings")
async def get_privacy_settings(
    current_user = Depends(require_authenticated_user),
    privacy_service = Depends(get_privacy_service),
    db_session = Depends(get_database_session)
):
    """
    Get user privacy settings
    
    Args:
        current_user: Current authenticated user
        privacy_service: Privacy service instance
        db_session: Database session
        
    Returns:
        User privacy settings
    """
    try:
        settings = await privacy_service.get_privacy_settings(
            db_session, current_user.id
        )
        
        if not settings:
            # Return default settings
            return {
                "success": True,
                "privacy_settings": {
                    "allow_research_participation": False,
                    "allow_analytics_tracking": True,
                    "allow_performance_tracking": True,
                    "allow_social_features": True,
                    "allow_third_party_sharing": False,
                    "allow_marketing_communications": False,
                    "data_retention_preference": "one_year",
                    "auto_delete_inactive_data": True,
                    "inactive_threshold_days": 365,
                    "prefer_anonymization_over_deletion": True,
                    "anonymization_level": "standard",
                    "privacy_notification_email": True,
                    "data_breach_notification": True,
                    "policy_update_notification": True,
                    "privacy_dashboard_enabled": True
                }
            }
        
        return {
            "success": True,
            "privacy_settings": {
                "allow_research_participation": settings.allow_research_participation,
                "allow_analytics_tracking": settings.allow_analytics_tracking,
                "allow_performance_tracking": settings.allow_performance_tracking,
                "allow_social_features": settings.allow_social_features,
                "allow_third_party_sharing": settings.allow_third_party_sharing,
                "allow_marketing_communications": settings.allow_marketing_communications,
                "data_retention_preference": settings.data_retention_preference,
                "auto_delete_inactive_data": settings.auto_delete_inactive_data,
                "inactive_threshold_days": settings.inactive_threshold_days,
                "prefer_anonymization_over_deletion": settings.prefer_anonymization_over_deletion,
                "anonymization_level": settings.anonymization_level,
                "privacy_notification_email": settings.privacy_notification_email,
                "data_breach_notification": settings.data_breach_notification,
                "policy_update_notification": settings.policy_update_notification,
                "privacy_dashboard_enabled": settings.privacy_dashboard_enabled,
                "last_privacy_review": settings.last_privacy_review.isoformat() if settings.last_privacy_review else None,
                "created_at": settings.created_at.isoformat(),
                "updated_at": settings.updated_at.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Get privacy settings error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get privacy settings")


@router.put("/settings")
async def update_privacy_settings(
    request: PrivacySettingsRequest,
    http_request: Request,
    current_user = Depends(require_authenticated_user),
    privacy_service = Depends(get_privacy_service),
    db_session = Depends(get_database_session)
):
    """
    Update user privacy settings
    
    Args:
        request: Privacy settings update request
        http_request: HTTP request for IP/user agent
        current_user: Current authenticated user
        privacy_service: Privacy service instance
        db_session: Database session
        
    Returns:
        Updated privacy settings
    """
    try:
        # Convert request to dict, excluding None values
        settings_update = {
            k: v for k, v in request.dict().items() 
            if v is not None
        }
        
        if not settings_update:
            raise HTTPException(status_code=400, detail="No settings provided to update")
        
        # Get client info
        ip_address = http_request.client.host
        user_agent = http_request.headers.get("user-agent")
        
        # Update settings
        updated_settings = await privacy_service.update_privacy_settings(
            session=db_session,
            user_id=current_user.id,
            settings_update=settings_update,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {
            "success": True,
            "message": "Privacy settings updated successfully",
            "updated_settings": settings_update,
            "last_updated": updated_settings.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update privacy settings error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update privacy settings")


@router.post("/delete-request")
async def request_data_deletion(
    request: DataDeletionRequest,
    current_user = Depends(require_authenticated_user),
    privacy_service = Depends(get_privacy_service),
    db_session = Depends(get_database_session)
):
    """
    Request data deletion (Right to be Forgotten)
    
    Args:
        request: Data deletion request
        current_user: Current authenticated user
        privacy_service: Privacy service instance
        db_session: Database session
        
    Returns:
        Deletion request confirmation
    """
    try:
        deletion_request = await privacy_service.request_data_deletion(
            session=db_session,
            user_id=current_user.id,
            request_type=request.request_type,
            deletion_scope=request.deletion_scope
        )
        
        return {
            "success": True,
            "message": "Data deletion request submitted successfully",
            "request_id": deletion_request.id,
            "verification_required": True,
            "verification_expires": deletion_request.verification_expires.isoformat(),
            "request_type": deletion_request.request_type,
            "status": deletion_request.status
        }
        
    except Exception as e:
        logger.error(f"Data deletion request error: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit deletion request")


@router.post("/export-request")
async def request_data_export(
    request: DataExportRequest,
    current_user = Depends(require_authenticated_user),
    privacy_service = Depends(get_privacy_service),
    db_session = Depends(get_database_session)
):
    """
    Request data export (Data Portability)
    
    Args:
        request: Data export request
        current_user: Current authenticated user
        privacy_service: Privacy service instance
        db_session: Database session
        
    Returns:
        Export request confirmation
    """
    try:
        export_request = await privacy_service.request_data_export(
            session=db_session,
            user_id=current_user.id,
            export_format=request.export_format,
            export_scope=request.export_scope
        )
        
        return {
            "success": True,
            "message": "Data export request submitted successfully",
            "request_id": export_request.id,
            "export_format": export_request.export_format,
            "expires_at": export_request.expires_at.isoformat(),
            "status": export_request.status,
            "estimated_processing_time": "24-48 hours"
        }
        
    except Exception as e:
        logger.error(f"Data export request error: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit export request")


@router.get("/consent-status")
async def get_consent_status(
    consent_type: Optional[str] = Query(None, description="Specific consent type to check"),
    current_user = Depends(require_authenticated_user),
    privacy_service = Depends(get_privacy_service),
    db_session = Depends(get_database_session)
):
    """
    Get user consent status
    
    Args:
        consent_type: Specific consent type to check (optional)
        current_user: Current authenticated user
        privacy_service: Privacy service instance
        db_session: Database session
        
    Returns:
        Consent status information
    """
    try:
        if consent_type:
            # Check specific consent type
            try:
                consent_enum = ConsentType(consent_type)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid consent type")
            
            has_consent = await privacy_service.check_consent(
                db_session, current_user.id, consent_enum
            )
            
            return {
                "success": True,
                "consent_type": consent_type,
                "has_consent": has_consent
            }
        
        else:
            # Get all consent statuses
            consent_status = {}
            for consent_enum in ConsentType:
                has_consent = await privacy_service.check_consent(
                    db_session, current_user.id, consent_enum
                )
                consent_status[consent_enum.value] = has_consent
            
            return {
                "success": True,
                "consent_status": consent_status
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Consent status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get consent status")


@router.get("/health")
async def privacy_health_check():
    """
    Privacy service health check
    
    Returns:
        Health status of privacy service
    """
    try:
        health_status = {
            "privacy_service": PRIVACY_SERVICE_AVAILABLE,
            "authentication": AUTH_AVAILABLE,
            "gdpr_compliance": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        all_healthy = all([
            health_status["privacy_service"],
            health_status["authentication"]
        ])
        
        return {
            "success": True,
            "healthy": all_healthy,
            "services": health_status
        }
        
    except Exception as e:
        logger.error(f"Privacy health check error: {e}")
        return {
            "success": False,
            "healthy": False,
            "error": str(e)
        }