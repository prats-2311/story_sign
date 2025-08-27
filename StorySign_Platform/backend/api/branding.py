"""
API endpoints for branding and customization management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from core.database_service import DatabaseService
from repositories.branding_repository import (
    BrandingRepository, ThemeRepository, FeatureFlagRepository, CustomDomainRepository
)
from services.branding_service import BrandingService, ThemeService, FeatureFlagService, CustomDomainService
from middleware.auth_middleware import get_current_user


router = APIRouter()


# Pydantic models for request/response
class BrandingConfigCreate(BaseModel):
    organization_name: str
    domain: str
    subdomain: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = "#3B82F6"
    secondary_color: Optional[str] = "#6B7280"
    accent_color: Optional[str] = "#10B981"
    background_color: Optional[str] = "#FFFFFF"
    font_family: Optional[str] = "Inter, sans-serif"
    font_size_base: Optional[float] = 16.0
    custom_css: Optional[str] = None
    contact_email: Optional[str] = None
    support_url: Optional[str] = None
    privacy_policy_url: Optional[str] = None
    terms_of_service_url: Optional[str] = None
    features_enabled: Optional[Dict[str, bool]] = None


class BrandingConfigUpdate(BaseModel):
    organization_name: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    background_color: Optional[str] = None
    font_family: Optional[str] = None
    font_size_base: Optional[float] = None
    custom_css: Optional[str] = None
    contact_email: Optional[str] = None
    support_url: Optional[str] = None
    privacy_policy_url: Optional[str] = None
    terms_of_service_url: Optional[str] = None
    features_enabled: Optional[Dict[str, bool]] = None


class ThemeConfigCreate(BaseModel):
    branding_id: str
    theme_name: str
    layout_type: Optional[str] = "standard"
    sidebar_position: Optional[str] = "left"
    header_style: Optional[str] = "default"
    theme_mode: Optional[str] = "light"
    button_style: Optional[Dict[str, Any]] = None
    card_style: Optional[Dict[str, Any]] = None
    navigation_style: Optional[Dict[str, Any]] = None
    component_overrides: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = False


class FeatureFlagCreate(BaseModel):
    branding_id: str
    flag_name: str
    flag_key: str
    is_enabled: Optional[bool] = False
    flag_type: Optional[str] = "boolean"
    flag_value: Optional[Any] = None
    rollout_percentage: Optional[float] = 0.0
    target_users: Optional[List[str]] = None
    target_groups: Optional[List[str]] = None
    description: Optional[str] = None
    category: Optional[str] = None
    environment: Optional[str] = "production"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class CustomDomainCreate(BaseModel):
    branding_id: str
    domain_name: str
    ssl_auto_renew: Optional[bool] = True
    ssl_provider: Optional[str] = "letsencrypt"


# Dependency injection
async def get_branding_service() -> BrandingService:
    db_service = DatabaseService()
    async with db_service.get_session() as session:
        branding_repo = BrandingRepository(session)
        return BrandingService(branding_repo)


async def get_theme_service() -> ThemeService:
    db_service = DatabaseService()
    async with db_service.get_session() as session:
        theme_repo = ThemeRepository(session)
        return ThemeService(theme_repo)


async def get_feature_flag_service() -> FeatureFlagService:
    db_service = DatabaseService()
    async with db_service.get_session() as session:
        flag_repo = FeatureFlagRepository(session)
        return FeatureFlagService(flag_repo)


async def get_custom_domain_service() -> CustomDomainService:
    db_service = DatabaseService()
    async with db_service.get_session() as session:
        domain_repo = CustomDomainRepository(session)
        return CustomDomainService(domain_repo)
# Branding Configuration Endpoints
@router.post("/branding", status_code=status.HTTP_201_CREATED)
async def create_branding_configuration(
    config: BrandingConfigCreate,
    current_user = Depends(get_current_user),
    branding_service: BrandingService = Depends(get_branding_service)
):
    """Create a new branding configuration."""
    try:
        config_data = config.dict(exclude_unset=True)
        branding_config = await branding_service.create_branding_configuration(
            config_data, current_user.id
        )
        return {
            "id": branding_config.id,
            "organization_name": branding_config.organization_name,
            "domain": branding_config.domain,
            "subdomain": branding_config.subdomain,
            "created_at": branding_config.created_at
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create branding configuration: {str(e)}"
        )


@router.get("/branding/domain/{domain}")
async def get_branding_by_domain(
    domain: str,
    branding_service: BrandingService = Depends(get_branding_service)
):
    """Get branding configuration by domain."""
    branding_config = await branding_service.get_branding_by_domain(domain)
    if not branding_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branding configuration not found"
        )
    
    return {
        "id": branding_config.id,
        "organization_name": branding_config.organization_name,
        "domain": branding_config.domain,
        "subdomain": branding_config.subdomain,
        "logo_url": branding_config.logo_url,
        "favicon_url": branding_config.favicon_url,
        "primary_color": branding_config.primary_color,
        "secondary_color": branding_config.secondary_color,
        "accent_color": branding_config.accent_color,
        "background_color": branding_config.background_color,
        "font_family": branding_config.font_family,
        "font_size_base": branding_config.font_size_base,
        "custom_css": branding_config.custom_css,
        "contact_email": branding_config.contact_email,
        "support_url": branding_config.support_url,
        "privacy_policy_url": branding_config.privacy_policy_url,
        "terms_of_service_url": branding_config.terms_of_service_url,
        "features_enabled": branding_config.features_enabled
    }


@router.put("/branding/{config_id}")
async def update_branding_configuration(
    config_id: str,
    config: BrandingConfigUpdate,
    current_user = Depends(get_current_user),
    branding_service: BrandingService = Depends(get_branding_service)
):
    """Update branding configuration."""
    try:
        update_data = config.dict(exclude_unset=True)
        branding_config = await branding_service.update_branding_configuration(
            config_id, update_data
        )
        
        if not branding_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branding configuration not found"
            )
        
        return {"message": "Branding configuration updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update branding configuration: {str(e)}"
        )


# Theme Configuration Endpoints
@router.post("/themes", status_code=status.HTTP_201_CREATED)
async def create_theme_configuration(
    theme: ThemeConfigCreate,
    current_user = Depends(get_current_user),
    theme_service: ThemeService = Depends(get_theme_service)
):
    """Create a new theme configuration."""
    try:
        theme_data = theme.dict(exclude_unset=True)
        theme_config = await theme_service.create_theme(theme_data)
        return {
            "id": theme_config.id,
            "theme_name": theme_config.theme_name,
            "branding_id": theme_config.branding_id,
            "is_default": theme_config.is_default
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create theme configuration: {str(e)}"
        )


@router.get("/themes/branding/{branding_id}")
async def get_themes_for_branding(
    branding_id: str,
    theme_service: ThemeService = Depends(get_theme_service)
):
    """Get all themes for a branding configuration."""
    themes = await theme_service.get_themes_for_branding(branding_id)
    return [
        {
            "id": theme.id,
            "theme_name": theme.theme_name,
            "layout_type": theme.layout_type,
            "sidebar_position": theme.sidebar_position,
            "header_style": theme.header_style,
            "theme_mode": theme.theme_mode,
            "is_default": theme.is_default,
            "button_style": theme.button_style,
            "card_style": theme.card_style,
            "navigation_style": theme.navigation_style,
            "component_overrides": theme.component_overrides
        }
        for theme in themes
    ]


# Feature Flag Endpoints
@router.post("/feature-flags", status_code=status.HTTP_201_CREATED)
async def create_feature_flag(
    flag: FeatureFlagCreate,
    current_user = Depends(get_current_user),
    flag_service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """Create a new feature flag."""
    try:
        flag_data = flag.dict(exclude_unset=True)
        feature_flag = await flag_service.create_feature_flag(flag_data)
        return {
            "id": feature_flag.id,
            "flag_name": feature_flag.flag_name,
            "flag_key": feature_flag.flag_key,
            "is_enabled": feature_flag.is_enabled,
            "branding_id": feature_flag.branding_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create feature flag: {str(e)}"
        )


@router.get("/feature-flags/branding/{branding_id}")
async def get_feature_flags_for_branding(
    branding_id: str,
    flag_service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """Get all feature flags for a branding configuration."""
    flags = await flag_service.get_flags_for_branding(branding_id)
    return [
        {
            "id": flag.id,
            "flag_name": flag.flag_name,
            "flag_key": flag.flag_key,
            "is_enabled": flag.is_enabled,
            "flag_type": flag.flag_type,
            "flag_value": flag.flag_value,
            "rollout_percentage": flag.rollout_percentage,
            "description": flag.description,
            "category": flag.category,
            "environment": flag.environment,
            "start_date": flag.start_date,
            "end_date": flag.end_date
        }
        for flag in flags
    ]


@router.get("/feature-flags/{branding_id}/check/{flag_key}")
async def check_feature_flag(
    branding_id: str,
    flag_key: str,
    user_id: Optional[str] = None,
    flag_service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """Check if a feature flag is enabled."""
    is_enabled = await flag_service.is_feature_enabled(branding_id, flag_key, user_id)
    return {"flag_key": flag_key, "is_enabled": is_enabled}


@router.post("/feature-flags/{flag_id}/toggle")
async def toggle_feature_flag(
    flag_id: str,
    current_user = Depends(get_current_user),
    flag_service: FeatureFlagService = Depends(get_feature_flag_service)
):
    """Toggle a feature flag on/off."""
    try:
        flag = await flag_service.toggle_feature_flag(flag_id)
        if not flag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feature flag not found"
            )
        
        return {
            "id": flag.id,
            "flag_key": flag.flag_key,
            "is_enabled": flag.is_enabled
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to toggle feature flag: {str(e)}"
        )


# Custom Domain Endpoints
@router.post("/custom-domains", status_code=status.HTTP_201_CREATED)
async def create_custom_domain(
    domain: CustomDomainCreate,
    current_user = Depends(get_current_user),
    domain_service: CustomDomainService = Depends(get_custom_domain_service)
):
    """Create a new custom domain configuration."""
    try:
        domain_data = domain.dict(exclude_unset=True)
        custom_domain = await domain_service.create_custom_domain(domain_data)
        return {
            "id": custom_domain.id,
            "domain_name": custom_domain.domain_name,
            "cname_target": custom_domain.cname_target,
            "dns_verification_token": custom_domain.dns_verification_token,
            "status": custom_domain.status
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create custom domain: {str(e)}"
        )


@router.post("/custom-domains/{domain_id}/verify-dns")
async def verify_domain_dns(
    domain_id: str,
    current_user = Depends(get_current_user),
    domain_service: CustomDomainService = Depends(get_custom_domain_service)
):
    """Verify DNS configuration for a custom domain."""
    try:
        verified = await domain_service.verify_domain_dns(domain_id)
        return {"verified": verified}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to verify DNS: {str(e)}"
        )


@router.post("/custom-domains/{domain_id}/provision-ssl")
async def provision_ssl_certificate(
    domain_id: str,
    current_user = Depends(get_current_user),
    domain_service: CustomDomainService = Depends(get_custom_domain_service)
):
    """Provision SSL certificate for a custom domain."""
    try:
        provisioned = await domain_service.provision_ssl_certificate(domain_id)
        return {"provisioned": provisioned}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to provision SSL certificate: {str(e)}"
        )


# Public endpoint for getting branding configuration (no auth required)
@router.get("/public/branding")
async def get_public_branding_config(
    request: Request,
    branding_service: BrandingService = Depends(get_branding_service)
):
    """Get public branding configuration based on request domain."""
    host = request.headers.get("host", "").split(":")[0]
    
    # Try to find branding config by domain or subdomain
    branding_config = await branding_service.get_branding_by_domain(host)
    if not branding_config:
        # Try subdomain
        subdomain = host.split(".")[0] if "." in host else host
        branding_config = await branding_service.get_branding_by_subdomain(subdomain)
    
    if not branding_config:
        # Return default branding
        return {
            "organization_name": "StorySign",
            "primary_color": "#3B82F6",
            "secondary_color": "#6B7280",
            "accent_color": "#10B981",
            "background_color": "#FFFFFF",
            "font_family": "Inter, sans-serif",
            "font_size_base": 16.0,
            "features_enabled": {
                "asl_world": True,
                "harmony": False,
                "reconnect": False,
                "analytics": True,
                "collaborative_sessions": True
            }
        }
    
    return {
        "organization_name": branding_config.organization_name,
        "logo_url": branding_config.logo_url,
        "favicon_url": branding_config.favicon_url,
        "primary_color": branding_config.primary_color,
        "secondary_color": branding_config.secondary_color,
        "accent_color": branding_config.accent_color,
        "background_color": branding_config.background_color,
        "font_family": branding_config.font_family,
        "font_size_base": branding_config.font_size_base,
        "custom_css": branding_config.custom_css,
        "contact_email": branding_config.contact_email,
        "support_url": branding_config.support_url,
        "privacy_policy_url": branding_config.privacy_policy_url,
        "terms_of_service_url": branding_config.terms_of_service_url,
        "features_enabled": branding_config.features_enabled
    }