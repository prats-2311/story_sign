"""
External Integration API endpoints
Handles OAuth2, SAML, LTI, webhooks, and embeddable widgets
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from uuid import uuid4
import json
import hmac
import hashlib
import base64

from fastapi import APIRouter, HTTPException, Depends, Request, Response, Query, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, HttpUrl, validator
import jwt

from core.database_service import get_database_service
from services.integration_service import IntegrationService
from services.auth_service import AuthService
from middleware.auth_middleware import get_current_user
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])
security = HTTPBearer()

# Pydantic models for external integrations

class OAuthProvider(BaseModel):
    """OAuth2 provider configuration"""
    name: str = Field(..., description="Provider name (google, microsoft, etc.)")
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")
    authorization_url: HttpUrl = Field(..., description="Authorization endpoint")
    token_url: HttpUrl = Field(..., description="Token endpoint")
    user_info_url: HttpUrl = Field(..., description="User info endpoint")
    scopes: List[str] = Field(default=["openid", "profile", "email"], description="Required scopes")
    enabled: bool = Field(default=True, description="Whether provider is enabled")

class SAMLConfig(BaseModel):
    """SAML configuration"""
    entity_id: str = Field(..., description="SAML entity ID")
    sso_url: HttpUrl = Field(..., description="Single Sign-On URL")
    slo_url: Optional[HttpUrl] = Field(None, description="Single Logout URL")
    x509_cert: str = Field(..., description="X.509 certificate for signature verification")
    name_id_format: str = Field(default="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress")
    enabled: bool = Field(default=True, description="Whether SAML is enabled")

class LTIConfig(BaseModel):
    """LTI (Learning Tools Interoperability) configuration"""
    consumer_key: str = Field(..., description="LTI consumer key")
    consumer_secret: str = Field(..., description="LTI consumer secret")
    launch_url: HttpUrl = Field(..., description="LTI launch URL")
    version: str = Field(default="1.1", description="LTI version")
    enabled: bool = Field(default=True, description="Whether LTI is enabled")

class WebhookConfig(BaseModel):
    """Webhook configuration"""
    name: str = Field(..., description="Webhook name")
    url: HttpUrl = Field(..., description="Webhook endpoint URL")
    events: List[str] = Field(..., description="Events to subscribe to")
    secret: Optional[str] = Field(None, description="Webhook secret for signature verification")
    headers: Optional[Dict[str, str]] = Field(default={}, description="Additional headers")
    enabled: bool = Field(default=True, description="Whether webhook is enabled")
    retry_count: int = Field(default=3, description="Number of retry attempts")
    timeout: int = Field(default=30, description="Request timeout in seconds")

class EmbedConfig(BaseModel):
    """Embeddable widget configuration"""
    widget_type: str = Field(..., description="Widget type (practice, progress, leaderboard)")
    domain: str = Field(..., description="Allowed domain for embedding")
    user_id: Optional[str] = Field(None, description="Specific user ID for personalized widgets")
    group_id: Optional[str] = Field(None, description="Group ID for group widgets")
    theme: Optional[Dict[str, Any]] = Field(default={}, description="Custom theme configuration")
    features: List[str] = Field(default=[], description="Enabled features")
    width: Optional[int] = Field(None, description="Widget width in pixels")
    height: Optional[int] = Field(None, description="Widget height in pixels")

class ExternalUserSync(BaseModel):
    """External user synchronization data"""
    external_id: str = Field(..., description="External system user ID")
    email: str = Field(..., description="User email")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    role: Optional[str] = Field(default="learner", description="User role")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional user metadata")

class WebhookEvent(BaseModel):
    """Webhook event payload"""
    event_type: str = Field(..., description="Event type")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    user_id: Optional[str] = Field(None, description="Associated user ID")
    data: Dict[str, Any] = Field(..., description="Event data")
    source: str = Field(default="storysign", description="Event source")

# OAuth2 endpoints

@router.get("/oauth/providers")
async def list_oauth_providers(
    integration_service: IntegrationService = Depends(get_database_service)
):
    """List available OAuth2 providers"""
    try:
        providers = await integration_service.get_oauth_providers()
        return {
            "providers": [
                {
                    "name": provider.name,
                    "authorization_url": str(provider.authorization_url),
                    "scopes": provider.scopes,
                    "enabled": provider.enabled
                }
                for provider in providers
            ]
        }
    except Exception as e:
        logger.error(f"Error listing OAuth providers: {e}")
        raise HTTPException(status_code=500, detail="Failed to list OAuth providers")

@router.post("/oauth/providers")
async def create_oauth_provider(
    provider: OAuthProvider,
    current_user: User = Depends(get_current_user),
    integration_service: IntegrationService = Depends(get_database_service)
):
    """Create OAuth2 provider configuration (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        created_provider = await integration_service.create_oauth_provider(provider)
        return {"message": "OAuth provider created successfully", "provider_id": created_provider.id}
    except Exception as e:
        logger.error(f"Error creating OAuth provider: {e}")
        raise HTTPException(status_code=500, detail="Failed to create OAuth provider")

@router.get("/oauth/{provider_name}/authorize")
async def oauth_authorize(
    provider_name: str,
    redirect_uri: str = Query(..., description="Redirect URI after authorization"),
    state: Optional[str] = Query(None, description="State parameter for CSRF protection"),
    integration_service: IntegrationService = Depends(get_database_service)
):
    """Initiate OAuth2 authorization flow"""
    try:
        auth_url = await integration_service.get_oauth_authorization_url(
            provider_name, redirect_uri, state
        )
        return {"authorization_url": auth_url}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error initiating OAuth authorization: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth authorization")

@router.post("/oauth/{provider_name}/callback")
async def oauth_callback(
    provider_name: str,
    code: str = Body(..., description="Authorization code"),
    state: Optional[str] = Body(None, description="State parameter"),
    integration_service: IntegrationService = Depends(get_database_service),
    auth_service: AuthService = Depends(get_database_service)
):
    """Handle OAuth2 callback and create/login user"""
    try:
        # Exchange code for tokens
        tokens = await integration_service.exchange_oauth_code(provider_name, code)
        
        # Get user info from provider
        user_info = await integration_service.get_oauth_user_info(provider_name, tokens["access_token"])
        
        # Create or login user
        user = await auth_service.create_or_login_oauth_user(provider_name, user_info)
        
        # Generate JWT tokens
        access_token = auth_service.create_access_token(user.id)
        refresh_token = auth_service.create_refresh_token(user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error handling OAuth callback: {e}")
        raise HTTPException(status_code=500, detail="Failed to process OAuth callback")

# SAML endpoints

@router.get("/saml/metadata")
async def saml_metadata(
    integration_service: IntegrationService = Depends(get_database_service)
):
    """Get SAML metadata XML"""
    try:
        metadata_xml = await integration_service.get_saml_metadata()
        return Response(content=metadata_xml, media_type="application/xml")
    except Exception as e:
        logger.error(f"Error generating SAML metadata: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate SAML metadata")

@router.post("/saml/sso")
async def saml_sso(
    request: Request,
    integration_service: IntegrationService = Depends(get_database_service),
    auth_service: AuthService = Depends(get_database_service)
):
    """Handle SAML SSO assertion"""
    try:
        # Parse SAML response
        saml_response = await request.form()
        assertion_data = await integration_service.parse_saml_response(
            saml_response.get("SAMLResponse")
        )
        
        # Create or login user
        user = await auth_service.create_or_login_saml_user(assertion_data)
        
        # Generate JWT tokens
        access_token = auth_service.create_access_token(user.id)
        refresh_token = auth_service.create_refresh_token(user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error handling SAML SSO: {e}")
        raise HTTPException(status_code=500, detail="Failed to process SAML SSO")

# LTI endpoints

@router.post("/lti/launch")
async def lti_launch(
    request: Request,
    integration_service: IntegrationService = Depends(get_database_service),
    auth_service: AuthService = Depends(get_database_service)
):
    """Handle LTI launch request"""
    try:
        # Parse LTI parameters
        form_data = await request.form()
        lti_params = dict(form_data)
        
        # Validate LTI signature
        is_valid = await integration_service.validate_lti_signature(lti_params, str(request.url))
        if not is_valid:
            raise HTTPException(status_code=401, detail="Invalid LTI signature")
        
        # Create or login user from LTI data
        user = await auth_service.create_or_login_lti_user(lti_params)
        
        # Generate JWT tokens
        access_token = auth_service.create_access_token(user.id)
        
        # Return launch page with embedded token
        launch_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>StorySign ASL Platform</title>
            <script>
                localStorage.setItem('access_token', '{access_token}');
                window.location.href = '/';
            </script>
        </head>
        <body>
            <p>Launching StorySign ASL Platform...</p>
        </body>
        </html>
        """
        return HTMLResponse(content=launch_html)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling LTI launch: {e}")
        raise HTTPException(status_code=500, detail="Failed to process LTI launch")

# Webhook endpoints

@router.get("/webhooks")
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    integration_service: IntegrationService = Depends(get_database_service)
):
    """List configured webhooks"""
    if current_user.role not in ["admin", "educator"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        webhooks = await integration_service.get_webhooks(current_user.id)
        return {"webhooks": webhooks}
    except Exception as e:
        logger.error(f"Error listing webhooks: {e}")
        raise HTTPException(status_code=500, detail="Failed to list webhooks")

@router.post("/webhooks")
async def create_webhook(
    webhook: WebhookConfig,
    current_user: User = Depends(get_current_user),
    integration_service: IntegrationService = Depends(get_database_service)
):
    """Create webhook configuration"""
    if current_user.role not in ["admin", "educator"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        created_webhook = await integration_service.create_webhook(webhook, current_user.id)
        return {"message": "Webhook created successfully", "webhook_id": created_webhook.id}
    except Exception as e:
        logger.error(f"Error creating webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to create webhook")

@router.post("/webhooks/test")
async def test_webhook(
    webhook_id: str,
    test_event: WebhookEvent,
    current_user: User = Depends(get_current_user),
    integration_service: IntegrationService = Depends(get_database_service)
):
    """Test webhook delivery"""
    if current_user.role not in ["admin", "educator"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        result = await integration_service.test_webhook(webhook_id, test_event)
        return {"message": "Webhook test completed", "result": result}
    except Exception as e:
        logger.error(f"Error testing webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to test webhook")

# Embeddable widget endpoints

@router.get("/embed/widget/{widget_type}")
async def get_embed_widget(
    widget_type: str,
    domain: str = Query(..., description="Embedding domain"),
    user_id: Optional[str] = Query(None, description="User ID for personalized widgets"),
    group_id: Optional[str] = Query(None, description="Group ID for group widgets"),
    theme: Optional[str] = Query(None, description="Theme name"),
    width: Optional[int] = Query(None, description="Widget width"),
    height: Optional[int] = Query(None, description="Widget height"),
    integration_service: IntegrationService = Depends(get_database_service)
):
    """Generate embeddable widget HTML"""
    try:
        # Validate domain and get widget configuration
        widget_config = await integration_service.get_widget_config(widget_type, domain)
        
        # Generate widget HTML
        widget_html = await integration_service.generate_widget_html(
            widget_type=widget_type,
            config=widget_config,
            user_id=user_id,
            group_id=group_id,
            theme=theme,
            width=width,
            height=height
        )
        
        return HTMLResponse(
            content=widget_html,
            headers={
                "X-Frame-Options": f"ALLOW-FROM {domain}",
                "Content-Security-Policy": f"frame-ancestors {domain}"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating embed widget: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate embed widget")

@router.get("/embed/script/{widget_type}")
async def get_embed_script(
    widget_type: str,
    domain: str = Query(..., description="Embedding domain"),
    integration_service: IntegrationService = Depends(get_database_service)
):
    """Generate JavaScript embed script"""
    try:
        # Generate embed script
        script_content = await integration_service.generate_embed_script(widget_type, domain)
        
        return Response(
            content=script_content,
            media_type="application/javascript",
            headers={
                "Access-Control-Allow-Origin": domain,
                "Cache-Control": "public, max-age=3600"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating embed script: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate embed script")

# Data synchronization endpoints

@router.post("/sync/users")
async def sync_external_users(
    users: List[ExternalUserSync],
    source_system: str = Body(..., description="Source system identifier"),
    current_user: User = Depends(get_current_user),
    integration_service: IntegrationService = Depends(get_database_service)
):
    """Synchronize users from external system"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        sync_result = await integration_service.sync_external_users(users, source_system)
        return {
            "message": "User synchronization completed",
            "created": sync_result["created"],
            "updated": sync_result["updated"],
            "errors": sync_result["errors"]
        }
    except Exception as e:
        logger.error(f"Error synchronizing users: {e}")
        raise HTTPException(status_code=500, detail="Failed to synchronize users")

@router.get("/sync/progress/{user_id}")
async def get_user_progress_for_sync(
    user_id: str,
    format: str = Query(default="json", description="Export format (json, csv, xml)"),
    current_user: User = Depends(get_current_user),
    integration_service: IntegrationService = Depends(get_database_service)
):
    """Get user progress data for external synchronization"""
    # Check permissions - user can access own data, educators can access their students
    if current_user.id != user_id and current_user.role not in ["admin", "educator"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        progress_data = await integration_service.get_user_progress_for_sync(user_id, format)
        
        if format == "csv":
            return Response(
                content=progress_data,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=user_{user_id}_progress.csv"}
            )
        elif format == "xml":
            return Response(
                content=progress_data,
                media_type="application/xml",
                headers={"Content-Disposition": f"attachment; filename=user_{user_id}_progress.xml"}
            )
        else:
            return JSONResponse(content=progress_data)
            
    except Exception as e:
        logger.error(f"Error getting user progress for sync: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user progress")

@router.post("/sync/progress/{user_id}")
async def sync_user_progress(
    user_id: str,
    progress_data: Dict[str, Any],
    source_system: str = Body(..., description="Source system identifier"),
    current_user: User = Depends(get_current_user),
    integration_service: IntegrationService = Depends(get_database_service)
):
    """Synchronize user progress from external system"""
    if current_user.role not in ["admin", "educator"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        sync_result = await integration_service.sync_user_progress(user_id, progress_data, source_system)
        return {
            "message": "Progress synchronization completed",
            "updated_sessions": sync_result["updated_sessions"],
            "created_sessions": sync_result["created_sessions"]
        }
    except Exception as e:
        logger.error(f"Error synchronizing user progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to synchronize user progress")

# Event notification endpoints

@router.get("/events/types")
async def get_event_types():
    """Get available event types for webhooks"""
    return {
        "event_types": [
            "user.registered",
            "user.login",
            "user.logout",
            "session.started",
            "session.completed",
            "progress.updated",
            "story.created",
            "story.completed",
            "group.created",
            "group.member_added",
            "assignment.created",
            "assignment.completed",
            "collaboration.started",
            "collaboration.ended"
        ]
    }

@router.post("/events/trigger")
async def trigger_event(
    event: WebhookEvent,
    current_user: User = Depends(get_current_user),
    integration_service: IntegrationService = Depends(get_database_service)
):
    """Manually trigger an event (for testing)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        await integration_service.trigger_webhook_event(event)
        return {"message": "Event triggered successfully"}
    except Exception as e:
        logger.error(f"Error triggering event: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger event")