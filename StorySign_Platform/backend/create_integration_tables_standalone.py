#!/usr/bin/env python3
"""
Standalone script to create integration tables
This script can be run independently without requiring the full application setup
"""

import asyncio
import logging
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "mysql+pymysql://root:password@localhost:4000/storysign_db"

def create_integration_tables():
    """Create all integration-related tables"""
    
    try:
        # Create engine and session
        engine = create_engine(DATABASE_URL, echo=True)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        logger.info("Creating integration tables...")
        
        # OAuth providers table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS oauth_providers (
                id CHAR(36) PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                client_id VARCHAR(255) NOT NULL,
                client_secret VARCHAR(255) NOT NULL,
                authorization_url VARCHAR(500) NOT NULL,
                token_url VARCHAR(500) NOT NULL,
                user_info_url VARCHAR(500) NOT NULL,
                scopes JSON NOT NULL,
                enabled BOOLEAN DEFAULT TRUE,
                provider_metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_oauth_providers_name (name),
                INDEX idx_oauth_providers_enabled (enabled)
            )
        """))
        
        # SAML providers table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS saml_providers (
                id CHAR(36) PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                entity_id VARCHAR(255) NOT NULL,
                sso_url VARCHAR(500) NOT NULL,
                slo_url VARCHAR(500),
                x509_cert TEXT NOT NULL,
                name_id_format VARCHAR(255) DEFAULT 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress',
                enabled BOOLEAN DEFAULT TRUE,
                saml_metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_saml_providers_name (name),
                INDEX idx_saml_providers_enabled (enabled)
            )
        """))
        
        # LTI providers table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS lti_providers (
                id CHAR(36) PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                consumer_key VARCHAR(255) NOT NULL,
                consumer_secret VARCHAR(255) NOT NULL,
                launch_url VARCHAR(500) NOT NULL,
                version VARCHAR(10) DEFAULT '1.1',
                enabled BOOLEAN DEFAULT TRUE,
                lti_metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_lti_providers_name (name),
                INDEX idx_lti_providers_enabled (enabled)
            )
        """))
        
        # External integrations table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS external_integrations (
                id CHAR(36) PRIMARY KEY,
                user_id CHAR(36) NOT NULL,
                provider_type VARCHAR(50) NOT NULL,
                provider_name VARCHAR(100) NOT NULL,
                external_user_id VARCHAR(255) NOT NULL,
                external_email VARCHAR(255),
                external_metadata JSON,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_external_integrations_user_id (user_id),
                INDEX idx_external_integrations_provider (provider_type, provider_name),
                INDEX idx_external_integrations_external_id (external_user_id),
                UNIQUE KEY uk_external_integrations (provider_type, provider_name, external_user_id)
            )
        """))
        
        # Webhook configurations table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS webhook_configs (
                id CHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                url VARCHAR(500) NOT NULL,
                events JSON NOT NULL,
                secret VARCHAR(255),
                headers JSON,
                enabled BOOLEAN DEFAULT TRUE,
                retry_count INT DEFAULT 3,
                timeout INT DEFAULT 30,
                created_by CHAR(36) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_webhook_configs_created_by (created_by),
                INDEX idx_webhook_configs_enabled (enabled)
            )
        """))
        
        # Webhook deliveries table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS webhook_deliveries (
                id CHAR(36) PRIMARY KEY,
                webhook_id CHAR(36) NOT NULL,
                event_type VARCHAR(100) NOT NULL,
                payload JSON,
                status_code INT,
                response_time FLOAT,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                retry_count INT DEFAULT 0,
                INDEX idx_webhook_deliveries_webhook_id (webhook_id),
                INDEX idx_webhook_deliveries_event_type (event_type),
                INDEX idx_webhook_deliveries_delivered_at (delivered_at),
                INDEX idx_webhook_deliveries_success (success)
            )
        """))
        
        # Embed configurations table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS embed_configs (
                id CHAR(36) PRIMARY KEY,
                widget_type VARCHAR(50) NOT NULL,
                name VARCHAR(255) NOT NULL,
                domain VARCHAR(255) NOT NULL,
                user_id CHAR(36),
                group_id CHAR(36),
                theme JSON,
                features JSON,
                dimensions JSON,
                enabled BOOLEAN DEFAULT TRUE,
                created_by CHAR(36) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_embed_configs_widget_type (widget_type),
                INDEX idx_embed_configs_domain (domain),
                INDEX idx_embed_configs_user_id (user_id),
                INDEX idx_embed_configs_group_id (group_id),
                INDEX idx_embed_configs_created_by (created_by),
                UNIQUE KEY uk_embed_configs (widget_type, domain, user_id, group_id)
            )
        """))
        
        # API keys table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id CHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                key_hash VARCHAR(255) UNIQUE NOT NULL,
                user_id CHAR(36) NOT NULL,
                scopes JSON NOT NULL,
                rate_limit INT DEFAULT 1000,
                enabled BOOLEAN DEFAULT TRUE,
                last_used TIMESTAMP,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_api_keys_user_id (user_id),
                INDEX idx_api_keys_enabled (enabled),
                INDEX idx_api_keys_expires_at (expires_at)
            )
        """))
        
        # Data synchronization table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS data_syncs (
                id CHAR(36) PRIMARY KEY,
                source_system VARCHAR(100) NOT NULL,
                sync_type VARCHAR(50) NOT NULL,
                entity_id VARCHAR(255) NOT NULL,
                local_id CHAR(36),
                sync_status VARCHAR(50) DEFAULT 'pending',
                sync_data JSON,
                error_message TEXT,
                last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                next_sync TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_data_syncs_source_system (source_system),
                INDEX idx_data_syncs_sync_type (sync_type),
                INDEX idx_data_syncs_entity_id (entity_id),
                INDEX idx_data_syncs_sync_status (sync_status),
                INDEX idx_data_syncs_last_sync (last_sync),
                INDEX idx_data_syncs_next_sync (next_sync),
                UNIQUE KEY uk_data_syncs (source_system, sync_type, entity_id)
            )
        """))
        
        # Integration events table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS integration_events (
                id CHAR(36) PRIMARY KEY,
                event_type VARCHAR(100) NOT NULL,
                integration_type VARCHAR(50) NOT NULL,
                user_id CHAR(36),
                external_id VARCHAR(255),
                event_data JSON,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(45),
                user_agent TEXT,
                INDEX idx_integration_events_event_type (event_type),
                INDEX idx_integration_events_integration_type (integration_type),
                INDEX idx_integration_events_user_id (user_id),
                INDEX idx_integration_events_occurred_at (occurred_at),
                INDEX idx_integration_events_success (success)
            )
        """))
        
        # White label configurations table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS white_label_configs (
                id CHAR(36) PRIMARY KEY,
                organization_id CHAR(36) NOT NULL,
                domain VARCHAR(255) UNIQUE NOT NULL,
                brand_name VARCHAR(255) NOT NULL,
                logo_url VARCHAR(500),
                primary_color VARCHAR(7),
                secondary_color VARCHAR(7),
                custom_css TEXT,
                features JSON,
                api_config JSON,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_white_label_configs_organization_id (organization_id),
                INDEX idx_white_label_configs_enabled (enabled)
            )
        """))
        
        session.commit()
        logger.info("✅ Integration tables created successfully")
        
        # Insert sample data
        insert_sample_data(session)
        
        session.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating integration tables: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

def insert_sample_data(session):
    """Insert sample integration data for testing"""
    
    try:
        logger.info("Inserting sample integration data...")
        
        # Sample OAuth providers
        oauth_providers = [
            {
                'id': 'google-oauth-provider',
                'name': 'google',
                'client_id': 'sample-google-client-id',
                'client_secret': 'sample-google-client-secret',
                'authorization_url': 'https://accounts.google.com/o/oauth2/v2/auth',
                'token_url': 'https://oauth2.googleapis.com/token',
                'user_info_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
                'scopes': '["openid", "profile", "email"]',
                'enabled': True
            },
            {
                'id': 'microsoft-oauth-provider',
                'name': 'microsoft',
                'client_id': 'sample-microsoft-client-id',
                'client_secret': 'sample-microsoft-client-secret',
                'authorization_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
                'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
                'user_info_url': 'https://graph.microsoft.com/v1.0/me',
                'scopes': '["openid", "profile", "email"]',
                'enabled': True
            }
        ]
        
        for provider in oauth_providers:
            session.execute(text("""
                INSERT IGNORE INTO oauth_providers 
                (id, name, client_id, client_secret, authorization_url, token_url, user_info_url, scopes, enabled)
                VALUES (:id, :name, :client_id, :client_secret, :authorization_url, :token_url, :user_info_url, :scopes, :enabled)
            """), provider)
        
        # Sample LTI provider
        session.execute(text("""
            INSERT IGNORE INTO lti_providers 
            (id, name, consumer_key, consumer_secret, launch_url, version, enabled)
            VALUES 
            ('sample-lti-provider', 'Sample LMS', 'storysign-consumer', 'sample-lti-secret', 
             '/api/v1/integrations/lti/launch', '1.1', TRUE)
        """))
        
        # Sample embed configurations (using placeholder user IDs)
        session.execute(text("""
            INSERT IGNORE INTO embed_configs 
            (id, widget_type, name, domain, theme, features, dimensions, enabled, created_by)
            VALUES 
            ('practice-widget-config', 'practice', 'Practice Widget', 'example.com', 
             '{"primary_color": "#007bff", "secondary_color": "#6c757d"}',
             '["video_practice", "gesture_feedback"]',
             '{"width": 800, "height": 600}', TRUE, 'admin-user-placeholder'),
            ('progress-widget-config', 'progress', 'Progress Widget', 'example.com',
             '{"primary_color": "#28a745", "secondary_color": "#6c757d"}',
             '["progress_charts", "achievements"]',
             '{"width": 400, "height": 300}', TRUE, 'admin-user-placeholder')
        """))
        
        session.commit()
        logger.info("✅ Sample integration data inserted successfully")
        
    except Exception as e:
        logger.error(f"⚠️  Warning: Could not insert sample data: {e}")
        # Don't fail the entire migration for sample data issues
        session.rollback()

def check_database_connection():
    """Check if database is accessible"""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def main():
    """Main function"""
    logger.info("Starting integration tables creation...")
    
    # Check database connection
    if not check_database_connection():
        logger.error("❌ Cannot connect to database. Please check:")
        logger.error("1. TiDB server is running")
        logger.error("2. Database credentials are correct")
        logger.error("3. Database 'storysign_db' exists")
        return False
    
    # Create tables
    success = create_integration_tables()
    
    if success:
        logger.info("🎉 Integration tables setup completed successfully!")
        logger.info("You can now use the external integration features:")
        logger.info("- OAuth2 authentication")
        logger.info("- SAML SSO")
        logger.info("- LTI integration")
        logger.info("- Webhooks")
        logger.info("- Embeddable widgets")
        logger.info("- Data synchronization")
    else:
        logger.error("❌ Integration tables setup failed")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)