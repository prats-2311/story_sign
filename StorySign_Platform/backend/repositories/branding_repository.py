"""
Repository for branding and customization data access.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.base_repository import BaseRepository
from models.branding import BrandingConfiguration, ThemeConfiguration, FeatureFlag, CustomDomain


class BrandingRepository(BaseRepository):
    """Repository for branding configuration operations."""
    
    async def create_branding_config(self, config_data: Dict[str, Any]) -> BrandingConfiguration:
        """Create a new branding configuration."""
        config = BrandingConfiguration(**config_data)
        self.session.add(config)
        await self.session.commit()
        await self.session.refresh(config)
        return config
    
    async def get_by_domain(self, domain: str) -> Optional[BrandingConfiguration]:
        """Get branding configuration by domain."""
        result = await self.session.execute(
            select(BrandingConfiguration).where(
                BrandingConfiguration.domain == domain,
                BrandingConfiguration.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_subdomain(self, subdomain: str) -> Optional[BrandingConfiguration]:
        """Get branding configuration by subdomain."""
        result = await self.session.execute(
            select(BrandingConfiguration).where(
                BrandingConfiguration.subdomain == subdomain,
                BrandingConfiguration.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    async def update_branding_config(self, config_id: str, update_data: Dict[str, Any]) -> Optional[BrandingConfiguration]:
        """Update branding configuration."""
        await self.session.execute(
            update(BrandingConfiguration)
            .where(BrandingConfiguration.id == config_id)
            .values(**update_data)
        )
        await self.session.commit()
        
        result = await self.session.execute(
            select(BrandingConfiguration).where(BrandingConfiguration.id == config_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all_active_configs(self) -> List[BrandingConfiguration]:
        """Get all active branding configurations."""
        result = await self.session.execute(
            select(BrandingConfiguration).where(BrandingConfiguration.is_active == True)
        )
        return result.scalars().all()


class ThemeRepository(BaseRepository):
    """Repository for theme configuration operations."""
    
    async def create_theme(self, theme_data: Dict[str, Any]) -> ThemeConfiguration:
        """Create a new theme configuration."""
        theme = ThemeConfiguration(**theme_data)
        self.session.add(theme)
        await self.session.commit()
        await self.session.refresh(theme)
        return theme
    
    async def get_themes_by_branding_id(self, branding_id: str) -> List[ThemeConfiguration]:
        """Get all themes for a branding configuration."""
        result = await self.session.execute(
            select(ThemeConfiguration).where(
                ThemeConfiguration.branding_id == branding_id,
                ThemeConfiguration.is_active == True
            )
        )
        return result.scalars().all()
    
    async def get_default_theme(self, branding_id: str) -> Optional[ThemeConfiguration]:
        """Get the default theme for a branding configuration."""
        result = await self.session.execute(
            select(ThemeConfiguration).where(
                ThemeConfiguration.branding_id == branding_id,
                ThemeConfiguration.is_default == True,
                ThemeConfiguration.is_active == True
            )
        )
        return result.scalar_one_or_none()


class FeatureFlagRepository(BaseRepository):
    """Repository for feature flag operations."""
    
    async def create_feature_flag(self, flag_data: Dict[str, Any]) -> FeatureFlag:
        """Create a new feature flag."""
        flag = FeatureFlag(**flag_data)
        self.session.add(flag)
        await self.session.commit()
        await self.session.refresh(flag)
        return flag
    
    async def get_flags_by_branding_id(self, branding_id: str) -> List[FeatureFlag]:
        """Get all feature flags for a branding configuration."""
        result = await self.session.execute(
            select(FeatureFlag).where(
                FeatureFlag.branding_id == branding_id,
                FeatureFlag.is_active == True
            )
        )
        return result.scalars().all()
    
    async def get_flag_by_key(self, branding_id: str, flag_key: str) -> Optional[FeatureFlag]:
        """Get a specific feature flag by key."""
        result = await self.session.execute(
            select(FeatureFlag).where(
                FeatureFlag.branding_id == branding_id,
                FeatureFlag.flag_key == flag_key,
                FeatureFlag.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    async def update_flag_status(self, flag_id: str, is_enabled: bool) -> Optional[FeatureFlag]:
        """Update feature flag enabled status."""
        await self.session.execute(
            update(FeatureFlag)
            .where(FeatureFlag.id == flag_id)
            .values(is_enabled=is_enabled)
        )
        await self.session.commit()
        
        result = await self.session.execute(
            select(FeatureFlag).where(FeatureFlag.id == flag_id)
        )
        return result.scalar_one_or_none()


class CustomDomainRepository(BaseRepository):
    """Repository for custom domain operations."""
    
    async def create_custom_domain(self, domain_data: Dict[str, Any]) -> CustomDomain:
        """Create a new custom domain."""
        domain = CustomDomain(**domain_data)
        self.session.add(domain)
        await self.session.commit()
        await self.session.refresh(domain)
        return domain
    
    async def get_by_domain_name(self, domain_name: str) -> Optional[CustomDomain]:
        """Get custom domain by domain name."""
        result = await self.session.execute(
            select(CustomDomain).where(
                CustomDomain.domain_name == domain_name,
                CustomDomain.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    async def get_domains_by_branding_id(self, branding_id: str) -> List[CustomDomain]:
        """Get all custom domains for a branding configuration."""
        result = await self.session.execute(
            select(CustomDomain).where(
                CustomDomain.branding_id == branding_id,
                CustomDomain.is_active == True
            )
        )
        return result.scalars().all()
    
    async def update_ssl_status(self, domain_id: str, ssl_status: str, ssl_expires_at=None) -> Optional[CustomDomain]:
        """Update SSL status for a custom domain."""
        update_data = {"ssl_status": ssl_status}
        if ssl_expires_at:
            update_data["ssl_expires_at"] = ssl_expires_at
            
        await self.session.execute(
            update(CustomDomain)
            .where(CustomDomain.id == domain_id)
            .values(**update_data)
        )
        await self.session.commit()
        
        result = await self.session.execute(
            select(CustomDomain).where(CustomDomain.id == domain_id)
        )
        return result.scalar_one_or_none()