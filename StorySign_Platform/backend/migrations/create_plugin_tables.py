"""
Database migration for plugin system tables
Creates plugins and plugin_data tables
"""

import asyncio
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from config import get_config

logger = logging.getLogger(__name__)


async def create_plugin_tables():
    """Create all plugin system tables"""
    
    try:
        # Get database configuration
        config = get_config()
        db_config = config.database
        
        # Create async engine
        engine = create_async_engine(
            db_config.get_connection_url(async_driver=True),
            echo=db_config.echo_queries
        )
        
        logger.info("Creating plugin system tables...")
        
        async with engine.begin() as conn:
            # Create plugins table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS plugins (
                    id CHAR(36) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    version VARCHAR(50) NOT NULL,
                    description TEXT,
                    author VARCHAR(255),
                    manifest JSON NOT NULL,
                    status VARCHAR(50) NOT NULL DEFAULT 'installed',
                    installed_by CHAR(36) NOT NULL,
                    error_message TEXT,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    INDEX idx_plugins_name (name),
                    INDEX idx_plugins_status (status),
                    INDEX idx_plugins_installed_by (installed_by),
                    INDEX idx_plugins_author (author),
                    INDEX idx_plugins_version (version),
                    
                    CONSTRAINT check_valid_status CHECK (status IN ('installed', 'active', 'disabled', 'error', 'updating')),
                    
                    FOREIGN KEY (installed_by) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # Create plugin_data table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS plugin_data (
                    id CHAR(36) PRIMARY KEY,
                    plugin_id CHAR(36) NOT NULL,
                    user_id CHAR(36),
                    data_key VARCHAR(255) NOT NULL,
                    data_value JSON NOT NULL,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    INDEX idx_plugin_data_plugin_id (plugin_id),
                    INDEX idx_plugin_data_user_id (user_id),
                    INDEX idx_plugin_data_key (data_key),
                    INDEX idx_plugin_data_plugin_user (plugin_id, user_id),
                    INDEX idx_plugin_data_plugin_key (plugin_id, data_key),
                    
                    FOREIGN KEY (plugin_id) REFERENCES plugins(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            logger.info("Successfully created plugin system tables:")
            logger.info("- plugins")
            logger.info("- plugin_data")
        
        # Close engine
        await engine.dispose()
        
        logger.info("Plugin system schema migration completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to create plugin system tables: {e}")
        raise


async def drop_plugin_tables():
    """Drop all plugin system tables (for rollback)"""
    
    try:
        # Get database configuration
        config = get_config()
        db_config = config.database
        
        # Create async engine
        engine = create_async_engine(
            db_config.get_connection_url(async_driver=True),
            echo=db_config.echo_queries
        )
        
        logger.warning("Dropping plugin system tables...")
        
        async with engine.begin() as conn:
            # Drop tables in reverse dependency order
            tables = ["plugin_data", "plugins"]
            
            for table in tables:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                logger.warning(f"Dropped table: {table}")
        
        # Close engine
        await engine.dispose()
        
        logger.warning("All plugin system tables dropped")
        
    except Exception as e:
        logger.error(f"Failed to drop plugin system tables: {e}")
        raise


async def verify_plugin_tables():
    """Verify that all plugin tables were created successfully"""
    
    try:
        # Get database configuration
        config = get_config()
        db_config = config.database
        
        # Create async engine
        engine = create_async_engine(
            db_config.get_connection_url(async_driver=True),
            echo=False
        )
        
        async with engine.begin() as conn:
            # Check if tables exist
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = :database_name 
                AND table_name IN ('plugins', 'plugin_data')
                ORDER BY table_name
            """)
            
            result = await conn.execute(tables_query, {"database_name": db_config.database})
            tables = result.fetchall()
            
            expected_tables = {"plugins", "plugin_data"}
            found_tables = {row[0] for row in tables}
            
            if found_tables == expected_tables:
                logger.info("✓ All plugin system tables verified successfully")
                
                # Check table structures
                for table_name in expected_tables:
                    columns_query = text(f"""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_schema = :database_name AND table_name = :table_name
                        ORDER BY ordinal_position
                    """)
                    
                    columns_result = await conn.execute(
                        columns_query, 
                        {"database_name": db_config.database, "table_name": table_name}
                    )
                    columns = columns_result.fetchall()
                    
                    logger.info(f"✓ Table '{table_name}' has {len(columns)} columns")
                
                return True
            else:
                missing_tables = expected_tables - found_tables
                logger.error(f"✗ Missing tables: {missing_tables}")
                return False
        
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"Failed to verify plugin tables: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "create":
                await create_plugin_tables()
            elif command == "drop":
                await drop_plugin_tables()
            elif command == "verify":
                success = await verify_plugin_tables()
                sys.exit(0 if success else 1)
            else:
                print("Usage: python create_plugin_tables.py [create|drop|verify]")
                sys.exit(1)
        else:
            # Default: create tables
            await create_plugin_tables()
            await verify_plugin_tables()
    
    asyncio.run(main())


# Migration metadata
MIGRATION_NAME = "create_plugin_tables"
MIGRATION_VERSION = "001"
MIGRATION_DESCRIPTION = "Create tables for plugin system"