"""
Create Research Data Management Tables
Migration to create tables for research consent, data anonymization, and retention policies
"""

import asyncio
from sqlalchemy import text
from core.database_service import DatabaseService
import logging

logger = logging.getLogger(__name__)


async def create_research_tables():
    """Create all research-related tables"""
    
    # Research participants table
    research_participants_sql = """
    CREATE TABLE IF NOT EXISTS research_participants (
        id CHAR(36) PRIMARY KEY,
        user_id CHAR(36) NOT NULL,
        research_id VARCHAR(100) NOT NULL,
        participant_code VARCHAR(50) NOT NULL UNIQUE,
        consent_given BOOLEAN NOT NULL DEFAULT FALSE,
        consent_date DATETIME(6),
        consent_version VARCHAR(20) NOT NULL,
        consent_document_url VARCHAR(500),
        study_start_date DATETIME(6),
        study_end_date DATETIME(6),
        participation_status VARCHAR(50) NOT NULL DEFAULT 'active',
        withdrawal_date DATETIME(6),
        withdrawal_reason TEXT,
        anonymization_level ENUM('none', 'pseudonymized', 'anonymized', 'aggregated') NOT NULL DEFAULT 'pseudonymized',
        data_retention_years INT NOT NULL DEFAULT 5,
        allow_data_sharing BOOLEAN NOT NULL DEFAULT FALSE,
        research_metadata JSON,
        created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
        updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
        INDEX idx_research_participant_user (user_id, research_id),
        INDEX idx_research_participant_status (participation_status, study_end_date),
        INDEX idx_research_participant_code (participant_code),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # Research datasets table
    research_datasets_sql = """
    CREATE TABLE IF NOT EXISTS research_datasets (
        id CHAR(36) PRIMARY KEY,
        dataset_name VARCHAR(255) NOT NULL,
        research_id VARCHAR(100) NOT NULL,
        researcher_id CHAR(36) NOT NULL,
        query_parameters JSON NOT NULL,
        anonymization_level ENUM('none', 'pseudonymized', 'anonymized', 'aggregated') NOT NULL,
        include_demographics BOOLEAN NOT NULL DEFAULT FALSE,
        include_video_data BOOLEAN NOT NULL DEFAULT FALSE,
        data_start_date DATETIME(6) NOT NULL,
        data_end_date DATETIME(6) NOT NULL,
        export_format VARCHAR(20) NOT NULL DEFAULT 'json',
        file_path VARCHAR(500),
        file_size_bytes INT,
        record_count INT,
        status VARCHAR(50) NOT NULL DEFAULT 'pending',
        processing_started_at DATETIME(6),
        processing_completed_at DATETIME(6),
        error_message TEXT,
        download_count INT NOT NULL DEFAULT 0,
        last_downloaded_at DATETIME(6),
        expires_at DATETIME(6),
        created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
        updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
        INDEX idx_research_dataset_researcher (researcher_id, created_at),
        INDEX idx_research_dataset_status (status, created_at),
        INDEX idx_research_dataset_research (research_id),
        FOREIGN KEY (researcher_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # Data retention rules table
    data_retention_rules_sql = """
    CREATE TABLE IF NOT EXISTS data_retention_rules (
        id CHAR(36) PRIMARY KEY,
        rule_name VARCHAR(100) NOT NULL UNIQUE,
        data_type VARCHAR(50) NOT NULL,
        retention_days INT NOT NULL,
        anonymize_after_days INT,
        hard_delete_after_days INT,
        applies_to_research_data BOOLEAN NOT NULL DEFAULT TRUE,
        applies_to_non_research_data BOOLEAN NOT NULL DEFAULT TRUE,
        consent_required BOOLEAN NOT NULL DEFAULT FALSE,
        compliance_framework VARCHAR(50),
        legal_basis TEXT,
        rule_config JSON NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        last_executed_at DATETIME(6),
        next_execution_at DATETIME(6),
        execution_frequency_hours INT NOT NULL DEFAULT 24,
        created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
        updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
        INDEX idx_retention_rule_data_type (data_type),
        INDEX idx_retention_rule_execution (is_active, next_execution_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    # Anonymized data mappings table
    anonymized_data_mappings_sql = """
    CREATE TABLE IF NOT EXISTS anonymized_data_mappings (
        id CHAR(36) PRIMARY KEY,
        original_id CHAR(36) NOT NULL,
        anonymized_id CHAR(36) NOT NULL,
        data_type VARCHAR(50) NOT NULL,
        research_id VARCHAR(100) NOT NULL,
        anonymization_method VARCHAR(50) NOT NULL,
        anonymization_key_hash VARCHAR(64),
        original_created_at DATETIME(6) NOT NULL,
        anonymized_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
        expires_at DATETIME(6),
        created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
        updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
        INDEX idx_anonymized_mapping_original (original_id, data_type),
        INDEX idx_anonymized_mapping_research (research_id, data_type),
        INDEX idx_anonymized_mapping_anonymized (anonymized_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    try:
        db_service = DatabaseService()
        await db_service.initialize()
        
        async with db_service.get_session() as session:
            logger.info("Creating research participants table...")
            await session.execute(text(research_participants_sql))
            
            logger.info("Creating research datasets table...")
            await session.execute(text(research_datasets_sql))
            
            logger.info("Creating data retention rules table...")
            await session.execute(text(data_retention_rules_sql))
            
            logger.info("Creating anonymized data mappings table...")
            await session.execute(text(anonymized_data_mappings_sql))
            
            await session.commit()
            logger.info("Successfully created all research tables")
            
    except Exception as e:
        logger.error(f"Error creating research tables: {str(e)}")
        raise


async def create_default_retention_policies():
    """Create default data retention policies"""
    
    default_policies = [
        {
            "rule_name": "GDPR_Analytics_Events",
            "data_type": "analytics_events",
            "retention_days": 1095,  # 3 years
            "anonymize_after_days": 365,  # 1 year
            "compliance_framework": "GDPR",
            "rule_config": {
                "description": "GDPR compliant retention for analytics events",
                "legal_basis": "Legitimate interest for service improvement"
            }
        },
        {
            "rule_name": "Research_Data_Retention",
            "data_type": "practice_sessions",
            "retention_days": 2555,  # 7 years
            "anonymize_after_days": 730,  # 2 years
            "applies_to_research_data": True,
            "applies_to_non_research_data": False,
            "consent_required": True,
            "compliance_framework": "Research Ethics",
            "rule_config": {
                "description": "Research data retention for longitudinal studies",
                "legal_basis": "Research consent"
            }
        },
        {
            "rule_name": "User_Generated_Content",
            "data_type": "stories",
            "retention_days": 3650,  # 10 years
            "anonymize_after_days": 1095,  # 3 years
            "rule_config": {
                "description": "User generated stories and content",
                "preserve_public_content": True
            }
        },
        {
            "rule_name": "Video_Analysis_Data",
            "data_type": "sentence_attempts",
            "retention_days": 1095,  # 3 years
            "anonymize_after_days": 180,  # 6 months
            "hard_delete_after_days": 1825,  # 5 years
            "rule_config": {
                "description": "Video analysis and gesture recognition data",
                "remove_biometric_data": True
            }
        }
    ]
    
    try:
        db_service = DatabaseService()
        
        async with db_service.get_session() as session:
            for policy in default_policies:
                # Check if policy already exists
                existing = await session.execute(
                    text("SELECT id FROM data_retention_rules WHERE rule_name = :rule_name"),
                    {"rule_name": policy["rule_name"]}
                )
                
                if existing.scalar_one_or_none():
                    logger.info(f"Retention policy {policy['rule_name']} already exists, skipping")
                    continue
                
                # Insert new policy
                insert_sql = """
                INSERT INTO data_retention_rules (
                    id, rule_name, data_type, retention_days, anonymize_after_days,
                    hard_delete_after_days, applies_to_research_data, applies_to_non_research_data,
                    consent_required, compliance_framework, rule_config, next_execution_at
                ) VALUES (
                    UUID(), :rule_name, :data_type, :retention_days, :anonymize_after_days,
                    :hard_delete_after_days, :applies_to_research_data, :applies_to_non_research_data,
                    :consent_required, :compliance_framework, :rule_config, DATE_ADD(NOW(), INTERVAL 1 DAY)
                )
                """
                
                await session.execute(text(insert_sql), {
                    "rule_name": policy["rule_name"],
                    "data_type": policy["data_type"],
                    "retention_days": policy["retention_days"],
                    "anonymize_after_days": policy.get("anonymize_after_days"),
                    "hard_delete_after_days": policy.get("hard_delete_after_days"),
                    "applies_to_research_data": policy.get("applies_to_research_data", True),
                    "applies_to_non_research_data": policy.get("applies_to_non_research_data", True),
                    "consent_required": policy.get("consent_required", False),
                    "compliance_framework": policy.get("compliance_framework"),
                    "rule_config": str(policy["rule_config"]).replace("'", '"')  # Convert to JSON string
                })
                
                logger.info(f"Created retention policy: {policy['rule_name']}")
            
            await session.commit()
            logger.info("Successfully created default retention policies")
            
    except Exception as e:
        logger.error(f"Error creating default retention policies: {str(e)}")
        raise


async def run_migration():
    """Run the complete research tables migration"""
    try:
        logger.info("Starting research tables migration...")
        
        # Create tables
        await create_research_tables()
        
        # Create default policies
        await create_default_retention_policies()
        
        logger.info("Research tables migration completed successfully")
        
    except Exception as e:
        logger.error(f"Research tables migration failed: {str(e)}")
        raise


if __name__ == "__main__":
    # Run migration
    asyncio.run(run_migration())