"""
Create privacy and compliance tables migration
"""

import asyncio
import logging
from sqlalchemy import text
from core.database_service import DatabaseService

logger = logging.getLogger(__name__)


async def create_privacy_tables():
    """Create privacy and compliance tables"""
    
    db_service = DatabaseService()
    await db_service.initialize()
    
    try:
        async with db_service.get_session() as session:
            # User consents table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS user_consents (
                    id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36) NOT NULL,
                    consent_type VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    granted_at DATETIME(6),
                    withdrawn_at DATETIME(6),
                    expires_at DATETIME(6),
                    consent_version VARCHAR(20) NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    consent_details JSON,
                    withdrawal_reason TEXT,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    INDEX idx_user_consents_user_id (user_id),
                    INDEX idx_user_consents_type (consent_type),
                    INDEX idx_user_consents_status (status),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
            
            # Data processing records table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS data_processing_records (
                    id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36) NOT NULL,
                    processing_purpose VARCHAR(50) NOT NULL,
                    data_categories JSON NOT NULL,
                    legal_basis VARCHAR(100) NOT NULL,
                    processor_id VARCHAR(100),
                    processing_details JSON,
                    retention_policy VARCHAR(50) NOT NULL,
                    scheduled_deletion DATETIME(6),
                    processed_at DATETIME(6) NOT NULL,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    INDEX idx_data_processing_user_id (user_id),
                    INDEX idx_data_processing_purpose (processing_purpose),
                    INDEX idx_data_processing_scheduled_deletion (scheduled_deletion),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
            
            # Data deletion requests table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS data_deletion_requests (
                    id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36) NOT NULL,
                    request_type VARCHAR(50) NOT NULL,
                    requested_at DATETIME(6) NOT NULL,
                    processed_at DATETIME(6),
                    completed_at DATETIME(6),
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    deletion_scope JSON,
                    verification_token VARCHAR(255),
                    verification_expires DATETIME(6),
                    verified_at DATETIME(6),
                    processing_notes TEXT,
                    anonymization_mapping JSON,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    INDEX idx_deletion_requests_user_id (user_id),
                    INDEX idx_deletion_requests_status (status),
                    INDEX idx_deletion_requests_verification_token (verification_token),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
            
            # Data export requests table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS data_export_requests (
                    id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36) NOT NULL,
                    requested_at DATETIME(6) NOT NULL,
                    processed_at DATETIME(6),
                    completed_at DATETIME(6),
                    expires_at DATETIME(6),
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    export_format VARCHAR(20) NOT NULL DEFAULT 'json',
                    export_scope JSON,
                    file_path VARCHAR(500),
                    file_size INT,
                    download_token VARCHAR(255),
                    download_count INT DEFAULT 0,
                    max_downloads INT DEFAULT 3,
                    processing_notes TEXT,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    INDEX idx_export_requests_user_id (user_id),
                    INDEX idx_export_requests_status (status),
                    INDEX idx_export_requests_download_token (download_token),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
            
            # Privacy settings table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS privacy_settings (
                    id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36) NOT NULL UNIQUE,
                    allow_research_participation BOOLEAN DEFAULT FALSE,
                    allow_analytics_tracking BOOLEAN DEFAULT TRUE,
                    allow_performance_tracking BOOLEAN DEFAULT TRUE,
                    allow_social_features BOOLEAN DEFAULT TRUE,
                    allow_third_party_sharing BOOLEAN DEFAULT FALSE,
                    allow_marketing_communications BOOLEAN DEFAULT FALSE,
                    data_retention_preference VARCHAR(50) DEFAULT 'one_year',
                    auto_delete_inactive_data BOOLEAN DEFAULT TRUE,
                    inactive_threshold_days INT DEFAULT 365,
                    prefer_anonymization_over_deletion BOOLEAN DEFAULT TRUE,
                    anonymization_level VARCHAR(20) DEFAULT 'standard',
                    privacy_notification_email BOOLEAN DEFAULT TRUE,
                    data_breach_notification BOOLEAN DEFAULT TRUE,
                    policy_update_notification BOOLEAN DEFAULT TRUE,
                    privacy_settings_json JSON,
                    last_privacy_review DATETIME(6),
                    privacy_dashboard_enabled BOOLEAN DEFAULT TRUE,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    INDEX idx_privacy_settings_user_id (user_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
            
            # Anonymized user data table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS anonymized_user_data (
                    id CHAR(36) PRIMARY KEY,
                    anonymous_id VARCHAR(64) NOT NULL UNIQUE,
                    original_user_id CHAR(36),
                    anonymization_date DATETIME(6) NOT NULL,
                    anonymization_method VARCHAR(50) NOT NULL,
                    age_range VARCHAR(20),
                    region VARCHAR(50),
                    language_preference VARCHAR(10),
                    learning_goals_category VARCHAR(50),
                    total_practice_sessions INT,
                    total_practice_time_minutes INT,
                    average_session_score FLOAT,
                    skill_progression_data JSON,
                    research_consent_granted BOOLEAN NOT NULL,
                    research_consent_date DATETIME(6),
                    research_data_categories JSON,
                    retention_until DATETIME(6),
                    deletion_scheduled BOOLEAN DEFAULT FALSE,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    INDEX idx_anonymized_data_anonymous_id (anonymous_id),
                    INDEX idx_anonymized_data_research_consent (research_consent_granted),
                    INDEX idx_anonymized_data_retention_until (retention_until)
                )
            """))
            
            # Privacy audit log table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS privacy_audit_logs (
                    id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36),
                    action_type VARCHAR(50) NOT NULL,
                    action_details JSON,
                    performed_by CHAR(36),
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    legal_basis VARCHAR(100),
                    compliance_notes TEXT,
                    action_timestamp DATETIME(6) NOT NULL,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    INDEX idx_privacy_audit_user_id (user_id),
                    INDEX idx_privacy_audit_action_type (action_type),
                    INDEX idx_privacy_audit_timestamp (action_timestamp),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            """))
            
            await session.commit()
            logger.info("Privacy tables created successfully")
            
    except Exception as e:
        logger.error(f"Error creating privacy tables: {e}")
        raise
    
    finally:
        await db_service.cleanup()


async def drop_privacy_tables():
    """Drop privacy tables (for testing/rollback)"""
    
    db_service = DatabaseService()
    await db_service.initialize()
    
    try:
        async with db_service.get_session() as session:
            # Drop tables in reverse order to respect foreign key constraints
            tables = [
                "privacy_audit_logs",
                "anonymized_user_data", 
                "privacy_settings",
                "data_export_requests",
                "data_deletion_requests",
                "data_processing_records",
                "user_consents"
            ]
            
            for table in tables:
                await session.execute(text(f"DROP TABLE IF EXISTS {table}"))
            
            await session.commit()
            logger.info("Privacy tables dropped successfully")
            
    except Exception as e:
        logger.error(f"Error dropping privacy tables: {e}")
        raise
    
    finally:
        await db_service.cleanup()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "drop":
        asyncio.run(drop_privacy_tables())
    else:
        asyncio.run(create_privacy_tables())