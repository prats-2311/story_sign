#!/usr/bin/env python3
"""
Verify Research Tables Script
Checks if research data management tables were created successfully
"""

import sys
import os
import logging

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_tables_with_pymysql():
    """Verify tables using pymysql"""
    try:
        import pymysql
        
        # Get database config
        config = get_config()
        db_config = config.database
        
        # Create connection with SSL support for TiDB Cloud
        ssl_config = None if db_config.ssl_disabled else {}
        
        connection = pymysql.connect(
            host=db_config.host,
            port=db_config.port,
            user=db_config.username,
            password=db_config.password,
            database=db_config.database,
            charset='utf8mb4',
            ssl=ssl_config
        )
        
        try:
            with connection.cursor() as cursor:
                # Check if research tables exist
                verify_sql = """
                SELECT TABLE_NAME, TABLE_ROWS, CREATE_TIME 
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME IN ('research_participants', 'research_datasets', 'data_retention_rules', 'anonymized_data_mappings')
                ORDER BY TABLE_NAME
                """
                
                cursor.execute(verify_sql)
                results = cursor.fetchall()
                
                logger.info("=" * 60)
                logger.info("Research Tables Verification Results")
                logger.info("=" * 60)
                
                if not results:
                    logger.error("No research tables found!")
                    return False
                
                for row in results:
                    table_name, table_rows, create_time = row
                    logger.info(f"✓ {table_name}: {table_rows or 0} rows, created: {create_time}")
                
                # Check retention policies
                cursor.execute("SELECT COUNT(*) FROM data_retention_rules")
                policy_count = cursor.fetchone()[0]
                logger.info(f"✓ Data retention policies: {policy_count} rules configured")
                
                # List the policies
                cursor.execute("SELECT rule_name, data_type, retention_days FROM data_retention_rules ORDER BY rule_name")
                policies = cursor.fetchall()
                
                logger.info("")
                logger.info("Configured Retention Policies:")
                for policy in policies:
                    rule_name, data_type, retention_days = policy
                    logger.info(f"  • {rule_name}: {data_type} ({retention_days} days)")
                
                logger.info("")
                logger.info("=" * 60)
                logger.info("✓ Research Data Management Tables Successfully Created!")
                logger.info("=" * 60)
                
                return len(results) == 4 and policy_count > 0
                
        finally:
            connection.close()
            
    except ImportError:
        logger.error("pymysql not available. Install with: pip install pymysql")
        return False
    except Exception as e:
        logger.error(f"Failed to verify tables: {e}")
        return False

def main():
    """Main verification function"""
    logger.info("Verifying StorySign Research Data Management Tables...")
    
    try:
        # Get database configuration
        config = get_config()
        db_config = config.database
        logger.info(f"Database: {db_config.host}:{db_config.port}/{db_config.database}")
        
        # Verify tables
        success = verify_tables_with_pymysql()
        
        if success:
            logger.info("")
            logger.info("Next Steps:")
            logger.info("1. Test the research API endpoints")
            logger.info("2. Configure user authentication")
            logger.info("3. Set up automated retention policy execution")
            logger.info("4. Deploy frontend research consent components")
            logger.info("")
            logger.info("Available API endpoints:")
            logger.info("• POST /api/research/participants/register")
            logger.info("• PUT /api/research/participants/consent")
            logger.info("• POST /api/research/participants/withdraw")
            logger.info("• POST /api/research/data/anonymize")
            logger.info("• POST /api/research/datasets")
            logger.info("• GET /api/research/datasets")
            logger.info("• POST /api/research/retention/rules")
            logger.info("• POST /api/research/retention/execute")
            return True
        else:
            logger.error("Research tables verification failed!")
            return False
            
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)