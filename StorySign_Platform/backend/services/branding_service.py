"""
Service layer for branding and customization functionality.
"""
import json
import ssl
import socket
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from repositories.branding_repository import (
    BrandingRepository, ThemeRepository, FeatureFlagRepository, CustomDomainRepository
)
from models.branding import BrandingConfiguration, ThemeConfiguration, FeatureFlag, CustomDomain


class BrandingService:
    """Service for managing branding configurations."""
    
    def __init__(self, branding_repo: BrandingRepository):
        self.branding_repo = branding_repo
    
    async def create_branding_configuration(self, config_data: Dict[str, Any], created_by: str) -> BrandingConfiguration:
        """Create a new branding configuration."""
        config_data["created_by"] = created_by
        
        # Set default values if not provided
        if "features_enabled" not in config_data:
            config_data["features_enabled"] = self._get_default_features()
        
        return await self.branding_repo.create_branding_config(config_data)
    
    async def get_branding_by_domain(self, domain: str) -> Optional[BrandingConfiguration]:
        """Get branding configuration by domain."""
        return await self.branding_repo.get_by_domain(domain)
    
    async def get_branding_by_subdomain(self, subdomain: str) -> Optional[BrandingConfiguration]:
        """Get branding configuration by subdomain."""
        return await self.branding_repo.get_by_subdomain(subdomain)
    
    async def update_branding_configuration(self, config_id: str, update_data: Dict[str, Any]) -> Optional[BrandingConfiguration]:
        """Update branding configuration."""
        return await self.branding_repo.update_branding_config(config_id, update_data)
    
    def _get_default_features(self) -> Dict[str, bool]:
        """Get default feature flags for new branding configurations."""
        return {
            "asl_world": True,
            "harmony": False,
            "reconnect": False,
            "analytics": True,
            "collaborative_sessions": True,
            "plugin_system": False,
            "research_participation": True,
            "social_features": True,
            "group_management": True,
            "custom_themes": True,
            "api_access": False,
            "white_labeling": True
        }


class ThemeService:
    """Service for managing theme configurations."""
    
    def __init__(self, theme_repo: ThemeRepository):
        self.theme_repo = theme_repo
    
    async def create_theme(self, theme_data: Dict[str, Any]) -> ThemeConfiguration:
        """Create a new theme configuration."""
        # Set default component styles if not provided
        if "button_style" not in theme_data:
            theme_data["button_style"] = self._get_default_button_style()
        if "card_style" not in theme_data:
            theme_data["card_style"] = self._get_default_card_style()
        if "navigation_style" not in theme_data:
            theme_data["navigation_style"] = self._get_default_navigation_style()
        
        return await self.theme_repo.create_theme(theme_data)
    
    async def get_themes_for_branding(self, branding_id: str) -> List[ThemeConfiguration]:
        """Get all themes for a branding configuration."""
        return await self.theme_repo.get_themes_by_branding_id(branding_id)
    
    async def get_default_theme(self, branding_id: str) -> Optional[ThemeConfiguration]:
        """Get the default theme for a branding configuration."""
        return await self.theme_repo.get_default_theme(branding_id)
    
    def _get_default_button_style(self) -> Dict[str, Any]:
        """Get default button styling."""
        return {
            "border_radius": "8px",
            "padding": "12px 24px",
            "font_weight": "600",
            "transition": "all 0.2s ease",
            "variants": {
                "primary": {
                    "background": "var(--primary-color)",
                    "color": "white",
                    "border": "none"
                },
                "secondary": {
                    "background": "transparent",
                    "color": "var(--primary-color)",
                    "border": "2px solid var(--primary-color)"
                }
            }
        }    

    def _get_default_card_style(self) -> Dict[str, Any]:
        """Get default card styling."""
        return {
            "border_radius": "12px",
            "padding": "24px",
            "box_shadow": "0 4px 6px rgba(0, 0, 0, 0.1)",
            "background": "white",
            "border": "1px solid #e5e7eb"
        }
    
    def _get_default_navigation_style(self) -> Dict[str, Any]:
        """Get default navigation styling."""
        return {
            "background": "var(--background-color, #ffffff)",
            "border_bottom": "1px solid #e5e7eb",
            "padding": "16px 24px",
            "item_padding": "8px 16px",
            "item_border_radius": "6px",
            "active_background": "var(--primary-color)",
            "active_color": "white"
        }


class FeatureFlagService:
    """Service for managing feature flags."""
    
    def __init__(self, flag_repo: FeatureFlagRepository):
        self.flag_repo = flag_repo
    
    async def create_feature_flag(self, flag_data: Dict[str, Any]) -> FeatureFlag:
        """Create a new feature flag."""
        return await self.flag_repo.create_feature_flag(flag_data)
    
    async def get_flags_for_branding(self, branding_id: str) -> List[FeatureFlag]:
        """Get all feature flags for a branding configuration."""
        return await self.flag_repo.get_flags_by_branding_id(branding_id)
    
    async def is_feature_enabled(self, branding_id: str, flag_key: str, user_id: str = None) -> bool:
        """Check if a feature is enabled for a user."""
        flag = await self.flag_repo.get_flag_by_key(branding_id, flag_key)
        
        if not flag or not flag.is_active:
            return False
        
        # Check if flag is within date range
        now = datetime.utcnow()
        if flag.start_date and now < flag.start_date:
            return False
        if flag.end_date and now > flag.end_date:
            return False
        
        # Simple boolean flag
        if flag.flag_type == "boolean":
            return flag.is_enabled
        
        # Rollout percentage check
        if flag.rollout_percentage < 100 and user_id:
            # Simple hash-based rollout
            user_hash = hash(f"{flag.id}:{user_id}") % 100
            if user_hash >= flag.rollout_percentage:
                return False
        
        # Target user check
        if flag.target_users and user_id:
            if user_id not in flag.target_users:
                return False
        
        return flag.is_enabled
    
    async def get_feature_value(self, branding_id: str, flag_key: str, default_value: Any = None) -> Any:
        """Get the value of a feature flag."""
        flag = await self.flag_repo.get_flag_by_key(branding_id, flag_key)
        
        if not flag or not flag.is_active or not flag.is_enabled:
            return default_value
        
        return flag.flag_value if flag.flag_value is not None else default_value
    
    async def toggle_feature_flag(self, flag_id: str) -> Optional[FeatureFlag]:
        """Toggle a feature flag on/off."""
        flag = await self.flag_repo.get_by_id(flag_id)
        if flag:
            return await self.flag_repo.update_flag_status(flag_id, not flag.is_enabled)
        return None


class CustomDomainService:
    """Service for managing custom domains and SSL certificates."""
    
    def __init__(self, domain_repo: CustomDomainRepository):
        self.domain_repo = domain_repo
    
    async def create_custom_domain(self, domain_data: Dict[str, Any]) -> CustomDomain:
        """Create a new custom domain configuration."""
        # Generate DNS verification token
        import secrets
        domain_data["dns_verification_token"] = secrets.token_urlsafe(32)
        domain_data["cname_target"] = f"storysign-{secrets.token_hex(8)}.platform.com"
        
        return await self.domain_repo.create_custom_domain(domain_data)
    
    async def verify_domain_dns(self, domain_id: str) -> bool:
        """Verify DNS configuration for a custom domain."""
        domain = await self.domain_repo.get_by_id(domain_id)
        if not domain:
            return False
        
        try:
            # Check CNAME record
            import dns.resolver
            answers = dns.resolver.resolve(domain.domain_name, 'CNAME')
            for answer in answers:
                if str(answer.target).rstrip('.') == domain.cname_target:
                    await self.domain_repo.update_custom_domain(
                        domain_id, 
                        {"dns_verified": True, "last_verified_at": datetime.utcnow()}
                    )
                    return True
        except Exception:
            pass
        
        return False
    
    async def provision_ssl_certificate(self, domain_id: str) -> bool:
        """Provision SSL certificate for a custom domain."""
        domain = await self.domain_repo.get_by_id(domain_id)
        if not domain or not domain.dns_verified:
            return False
        
        try:
            # In a real implementation, this would integrate with Let's Encrypt or another CA
            # For now, we'll simulate the process
            
            # Update SSL status to active
            expires_at = datetime.utcnow() + timedelta(days=90)
            await self.domain_repo.update_ssl_status(domain_id, "active", expires_at)
            
            return True
        except Exception:
            await self.domain_repo.update_ssl_status(domain_id, "error")
            return False
    
    async def check_ssl_expiry(self, domain_name: str) -> Optional[datetime]:
        """Check SSL certificate expiry for a domain."""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain_name, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain_name) as ssock:
                    cert = ssock.getpeercert()
                    expiry_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    return expiry_date
        except Exception:
            return None