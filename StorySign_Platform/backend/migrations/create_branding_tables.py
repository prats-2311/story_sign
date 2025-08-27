"""
Create branding and customization tables for white-labeling support.
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database_service import DatabaseService


async def create_branding_tables():
    """Create all branding-related tables."""
    db_service = DatabaseService()
    
    try:
        async with db_service.get_session() as session:
            # Create branding_configurations table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS branding_configurations (
                    id CHAR(36) PRIMARY KEY,
                    organization_name VARCHAR(255) NOT NULL,
                    domain VARCHAR(255) UNIQUE NOT NULL,
                    subdomain VARCHAR(100) UNIQUE,
                    logo_url VARCHAR(500),
                    favicon_url VARCHAR(500),
                    primary_color CHAR(7),
                    secondary_color CHAR(7),
                    accent_color CHAR(7),
                    background_color CHAR(7),
                    font_family VARCHAR(100),
                    font_size_base FLOAT DEFAULT 16.0,
                    custom_css TEXT,
                    contact_email VARCHAR(255),
                    support_url VARCHAR(500),
                    privacy_policy_url VARCHAR(500),
                    terms_of_service_url VARCHAR(500),
                    features_enabled JSON,
                    ssl_certificate_path VARCHAR(500),
                    ssl_private_key_path VARCHAR(500),
                    ssl_enabled BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_by CHAR(36) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_domain (domain),
                    INDEX idx_subdomain (subdomain),
                    INDEX idx_active (is_active)
                )
            """))
            
            # Create theme_configurations table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS theme_configurations (
                    id CHAR(36) PRIMARY KEY,
                    branding_id CHAR(36) NOT NULL,
                    theme_name VARCHAR(100) NOT NULL,
                    layout_type VARCHAR(50) DEFAULT 'standard',
                    sidebar_position VARCHAR(20) DEFAULT 'left',
                    header_style VARCHAR(50) DEFAULT 'default',
                    button_style JSON,
                    card_style JSON,
                    navigation_style JSON,
                    theme_mode VARCHAR(20) DEFAULT 'light',
                    component_overrides JSON,
                    is_default BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_branding_id (branding_id),
                    INDEX idx_theme_name (theme_name),
                    INDEX idx_default (is_default)
                )
            """))        
    # Create feature_flags table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS feature_flags (
                    id CHAR(36) PRIMARY KEY,
                    branding_id CHAR(36) NOT NULL,
                    flag_name VARCHAR(100) NOT NULL,
                    flag_key VARCHAR(100) NOT NULL,
                    is_enabled BOOLEAN DEFAULT FALSE,
                    flag_type VARCHAR(50) DEFAULT 'boolean',
                    flag_value JSON,
                    rollout_percentage FLOAT DEFAULT 0.0,
                    target_users JSON,
                    target_groups JSON,
                    description TEXT,
                    category VARCHAR(100),
                    environment VARCHAR(50) DEFAULT 'production',
                    start_date TIMESTAMP NULL,
                    end_date TIMESTAMP NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_branding_id (branding_id),
                    INDEX idx_flag_key (flag_key),
                    INDEX idx_environment (environment),
                    INDEX idx_active (is_active)
                )
            """))
            
            # Create custom_domains table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS custom_domains (
                    id CHAR(36) PRIMARY KEY,
                    branding_id CHAR(36) NOT NULL,
                    domain_name VARCHAR(255) UNIQUE NOT NULL,
                    cname_target VARCHAR(255),
                    dns_verified BOOLEAN DEFAULT FALSE,
                    dns_verification_token VARCHAR(255),
                    ssl_certificate TEXT,
                    ssl_private_key TEXT,
                    ssl_certificate_chain TEXT,
                    ssl_auto_renew BOOLEAN DEFAULT TRUE,
                    ssl_provider VARCHAR(50),
                    ssl_status VARCHAR(50) DEFAULT 'pending',
                    ssl_expires_at TIMESTAMP NULL,
                    status VARCHAR(50) DEFAULT 'pending',
                    verification_status VARCHAR(50) DEFAULT 'pending',
                    last_verified_at TIMESTAMP NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_branding_id (branding_id),
                    INDEX idx_domain_name (domain_name),
                    INDEX idx_status (status),
                    INDEX idx_ssl_status (ssl_status)
                )
            """))
            
            await session.commit()
            print("✅ Branding tables created successfully")
            
    except Exception as e:
        print(f"❌ Error creating branding tables: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(create_branding_tables())