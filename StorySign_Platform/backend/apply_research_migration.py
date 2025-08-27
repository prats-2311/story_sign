#!/usr/bin/env python3
"""
Direct Research Tables Migration Script
Applies research data management tables to the database
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any
import uuid
from datetime import datetime, timedelta

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# SQL statements for creating research tables
CREATE_RESEARCH_PARTICIPANTS_TABLE = """
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
    INDEX idx_research_participant_code (participant_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

CREATE_RESEARCH_DATASETS_TABLE = """
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
    INDEX idx_research_dataset_research (research_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

CREATE_DATA_RETENTION_RULES_TABLE = """
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

CREATE_ANONYMIZED_DATA_MAPPINGS_TABLE = """
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

# Default retention policies
DEFAULT_RETENTION_POLICIES = [
    {
        "rule_name": "GDPR_Analytics_Events",
        "data_type": "analytics_events",
        "retention_days": 1095,  # 3 years
        "anonymize_after_days": 365,  # 1 year
        "compliance_framework": "GDPR",
        "rule_config": '{"description": "GDPR compliant retention for analytics events", "legal_basis": "Legitimate interest for service improvement"}'
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
        "rule_config": '{"description": "Research data retention for longitudinal studies", "legal_basis": "Research consent"}'
    },
    {
        "rule_name": "User_Generated_Content",
        "data_type": "stories",
        "retention_days": 3650,  # 10 years
        "anonymize_after_days": 1095,  # 3 years
        "rule_config": '{"description": "User generated stories and content", "preserve_public_content": true}'
    },
    {
        "rule_name": "Video_Analysis_Data",
        "data_type": "sentence_attempts",
        "retention_days": 1095,  # 3 years
        "anonymize_after_days": 180,  # 6 months
        "hard_delete_after_days": 1825,  # 5 years
        "rule_config": '{"description": "Video analysis and gesture recognition data", "remove_biometric_data": true}'
    }
]

async def execute_sql_with_pymysql(sql: str, params: Dict[str, Any] = None) -> bool:
    """Execute SQL using pymysql (sync driver)"""
    try:
        import pymysql
        
        # Get database config
        config = get_config()
        db_config = config.database
        
        # Create connection with SSL support for TiDB Cloud
        connection = pymysql.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.username,
            password=db_config.password,
            database=db_config.database,
            charset='utf8mb4',
            autocommit=False,
            ssl={'ssl_disabled': False} if not db_config.ssl_disabled else None,
            ssl_disabled=db_config.ssl_disabled
        )
        
        try:
            with connection.cursor() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                connection.commit()
                logger.info(f"SQL executed successfully: {sql[:50]}...")
                return True
                
        finally:
            connection.close()
            
    except ImportError:
        logger.error("pymysql not available. Install with: pip install pymysql")
        return False
    except Exception as e:
        logger.error(f"Failed to execute SQL: {e}")
        return False

async def execute_sql_with_asyncmy(sql: str, params: Dict[str, Any] = None) -> bool:
    """Execute SQL using asyncmy (async driver)"""
    try:
        import asyncmy
        
        # Get database config
        config = get_config()
        db_config = config.database
        
        # Create connection with SSL support for TiDB Cloud
        connection = await asyncmy.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.username,
            password=db_config.password,
            db=db_config.database,
            charset='utf8mb4',
            autocommit=False,
            ssl={'ssl_disabled': False} if not db_config.ssl_disabled else None,
            ssl_disabled=db_config.ssl_disabled
        )
        
        try:
            async with connection.cursor() as cursor:
                if params:
                    await cursor.execute(sql, params)
                else:
                    await cursor.execute(sql)
                await connection.commit()
                logger.info(f"SQL executed successfully: {sql[:50]}...")
                return True
                
        finally:
            await connection.ensure_closed()
            
    except ImportError:
        logger.error("asyncmy not available. Install with: pip install asyncmy")
        return False
    except Exception as e:
        logger.error(f"Failed to execute SQL: {e}")
        return False

async def create_research_tables():
    """Create research data management tables"""
    logger.info("Creating research data management tables...")
    
    tables = [
        ("Research Participants", CREATE_RESEARCH_PARTICIPANTS_TABLE),
        ("Research Datasets", CREATE_RESEARCH_DATASETS_TABLE),
        ("Data Retention Rules", CREATE_DATA_RETENTION_RULES_TABLE),
        ("Anonymized Data Mappings", CREATE_ANONYMIZED_DATA_MAPPINGS_TABLE)
    ]
    
    success_count = 0
    
    for table_name, sql in tables:
        logger.info(f"Creating {table_name} table...")
        
        # Try asyncmy first, then pymysql
        success = await execute_sql_with_asyncmy(sql)
        if not success:
            success = await execute_sql_with_pymysql(sql)
        
        if success:
            logger.info(f"✓ {table_name} table created successfully")
            success_count += 1
        else:
            logger.error(f"✗ Failed to create {table_name} table")
    
    return success_count == len(tables)

async def insert_default_retention_policies():
    """Insert default data retention policies"""
    logger.info("Inserting default retention policies...")
    
    success_count = 0
    
    for policy in DEFAULT_RETENTION_POLICIES:
        logger.info(f"Inserting retention policy: {policy['rule_name']}")
        
        # Generate UUID for the policy
        policy_id = str(uuid.uuid4())
        next_execution = datetime.now() + timedelta(days=1)
        
        insert_sql = """
        INSERT INTO data_retention_rules (
            id, rule_name, data_type, retention_days, anonymize_after_days,
            hard_delete_after_days, applies_to_research_data, applies_to_non_research_data,
            consent_required, compliance_framework, rule_config, next_execution_at
        ) VALUES (
            %(id)s, %(rule_name)s, %(data_type)s, %(retention_days)s, %(anonymize_after_days)s,
            %(hard_delete_after_days)s, %(applies_to_research_data)s, %(applies_to_non_research_data)s,
            %(consent_required)s, %(compliance_framework)s, %(rule_config)s, %(next_execution_at)s
        ) ON DUPLICATE KEY UPDATE
            retention_days = VALUES(retention_days),
            anonymize_after_days = VALUES(anonymize_after_days),
            hard_delete_after_days = VALUES(hard_delete_after_days),
            rule_config = VALUES(rule_config),
            updated_at = CURRENT_TIMESTAMP(6)
        """
        
        params = {
            'id': policy_id,
            'rule_name': policy["rule_name"],
            'data_type': policy["data_type"],
            'retention_days': policy["retention_days"],
            'anonymize_after_days': policy.get("anonymize_after_days"),
            'hard_delete_after_days': policy.get("hard_delete_after_days"),
            'applies_to_research_data': policy.get("applies_to_research_data", True),
            'applies_to_non_research_data': policy.get("applies_to_non_research_data", True),
            'consent_required': policy.get("consent_required", False),
            'compliance_framework': policy.get("compliance_framework", ""),
            'rule_config': policy["rule_config"],
            'next_execution_at': next_execution
        }
        
        # Try asyncmy first, then pymysql
        success = await execute_sql_with_asyncmy(insert_sql, params)
        if not success:
            success = await execute_sql_with_pymysql(insert_sql, params)
        
        if success:
            logger.info(f"✓ {policy['rule_name']} policy inserted successfully")
            success_count += 1
        else:
            logger.error(f"✗ Failed to insert {policy['rule_name']} policy")
    
    return success_count == len(DEFAULT_RETENTION_POLICIES)

async def verify_tables():
    """Verify that tables were created successfully"""
    logger.info("Verifying research tables...")
    
    verify_sql = """
    SELECT TABLE_NAME, TABLE_ROWS, CREATE_TIME 
    FROM information_schema.TABLES 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME IN ('research_participants', 'research_datasets', 'data_retention_rules', 'anonymized_data_mappings')
    ORDER BY TABLE_NAME
    """
    
    try:
        # Try to get database config and execute verification
        config = get_config()
        db_config = config.database
        
        # Try asyncmy first
        try:
            import asyncmy
            
            connection = await asyncmy.connect(
                host=db_config.host,
                port=db_config.port,
                user=db_config.username,
                password=db_config.password,
                db=db_config.database,
                charset='utf8mb4',
                ssl={'ssl_disabled': False} if not db_config.ssl_disabled else None,
                ssl_disabled=db_config.ssl_disabled
            )
            
            try:
                async with connection.cursor() as cursor:
                    await cursor.execute(verify_sql)
                    results = await cursor.fetchall()
                    
                    logger.info("Research tables verification:")
                    for row in results:
                        table_name, table_rows, create_time = row
                        logger.info(f"✓ {table_name}: {table_rows or 0} rows, created: {create_time}")
                    
                    return len(results) == 4
                    
            finally:
                await connection.ensure_closed()
                
        except ImportError:
            # Fall back to pymysql
            import pymysql
            
            connection = pymysql.connect(
                host=db_config.host,
                port=db_config.port,
                user=db_config.username,
                password=db_config.password,
                database=db_config.database,
                charset='utf8mb4',
                ssl={'ssl_disabled': False} if not db_config.ssl_disabled else None,
                ssl_disabled=db_config.ssl_disabled
            )
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute(verify_sql)
                    results = cursor.fetchall()
                    
                    logger.info("Research tables verification:")
                    for row in results:
                        table_name, table_rows, create_time = row
                        logger.info(f"✓ {table_name}: {table_rows or 0} rows, created: {create_time}")
                    
                    return len(results) == 4
                    
            finally:
                connection.close()
                
    except Exception as e:
        logger.error(f"Failed to verify tables: {e}")
        return False

async def main():
    """Main migration function"""
    logger.info("=" * 60)
    logger.info("StorySign Research Data Management Migration")
    logger.info("=" * 60)
    
    try:
        # Check database configuration
        config = get_config()
        db_config = config.database
        logger.info(f"Database: {db_config.host}:{db_config.port}/{db_config.database}")
        logger.info(f"Username: {db_config.username}")
        
        # Create tables
        tables_created = await create_research_tables()
        if not tables_created:
            logger.error("Failed to create all research tables")
            return False
        
        # Insert default policies
        policies_inserted = await insert_default_retention_policies()
        if not policies_inserted:
            logger.error("Failed to insert all default retention policies")
            return False
        
        # Verify tables
        tables_verified = await verify_tables()
        if not tables_verified:
            logger.error("Failed to verify all research tables")
            return False
        
        logger.info("=" * 60)
        logger.info("✓ Research Data Management Migration Completed Successfully!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Available features:")
        logger.info("• Research participant consent management")
        logger.info("• Data anonymization and aggregation")
        logger.info("• Research dataset export")
        logger.info("• Automated data retention policies")
        logger.info("• GDPR and research ethics compliance")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Test the research API endpoints")
        logger.info("2. Configure user authentication")
        logger.info("3. Set up automated retention policy execution")
        logger.info("4. Deploy frontend research consent components")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)