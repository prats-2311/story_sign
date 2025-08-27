"""
Database migration for user management tables
Creates users, user_profiles, and user_sessions tables
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


async def create_user_tables():
    """Create all user management tables"""
    
    try:
        # Get database configuration
        config = get_config()
        db_config = config.database
        
        # Create async engine with proper SSL configuration
        engine = create_async_engine(
            db_config.get_connection_url(async_driver=True),
            echo=db_config.echo_queries,
            connect_args=db_config.get_connect_args()
        )
        
        logger.info("Creating user management tables...")
        
        async with engine.begin() as conn:
            # Create users table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id CHAR(36) PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    username VARCHAR(100) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
                    verification_token VARCHAR(255),
                    reset_token VARCHAR(255),
                    reset_token_expires DATETIME(6),
                    last_login DATETIME(6),
                    login_count INT NOT NULL DEFAULT 0,
                    preferences JSON,
                    metadata JSON,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    INDEX idx_users_email (email),
                    INDEX idx_users_username (username),
                    INDEX idx_users_active (is_active),
                    INDEX idx_users_verified (is_verified),
                    INDEX idx_users_last_login (last_login)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # Create user_profiles table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36) NOT NULL,
                    avatar_url VARCHAR(500),
                    bio TEXT,
                    location VARCHAR(255),
                    timezone VARCHAR(50),
                    language VARCHAR(10) NOT NULL DEFAULT 'en',
                    skill_level VARCHAR(20) NOT NULL DEFAULT 'beginner',
                    learning_goals JSON,
                    interests JSON,
                    accessibility_settings JSON,
                    privacy_settings JSON,
                    notification_settings JSON,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    INDEX idx_user_profiles_user_id (user_id),
                    INDEX idx_user_profiles_skill_level (skill_level),
                    INDEX idx_user_profiles_language (language),
                    
                    CONSTRAINT check_valid_skill_level CHECK (skill_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # Create user_sessions table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36) NOT NULL,
                    session_token VARCHAR(255) NOT NULL UNIQUE,
                    expires_at DATETIME(6) NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    INDEX idx_user_sessions_user_id (user_id),
                    INDEX idx_user_sessions_token (session_token),
                    INDEX idx_user_sessions_expires (expires_at),
                    INDEX idx_user_sessions_active (is_active),
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            logger.info("Successfully created user management tables:")
            logger.info("- users")
            logger.info("- user_profiles")
            logger.info("- user_sessions")
        
        # Close engine
        await engine.dispose()
        
        logger.info("User management schema migration completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to create user management tables: {e}")
        raise


async def drop_user_tables():
    """Drop all user management tables (for rollback)"""
    
    try:
        # Get database configuration
        config = get_config()
        db_config = config.database
        
        # Create async engine with proper SSL configuration
        engine = create_async_engine(
            db_config.get_connection_url(async_driver=True),
            echo=db_config.echo_queries,
            connect_args=db_config.get_connect_args()
        )
        
        logger.warning("Dropping user management tables...")
        
        async with engine.begin() as conn:
            # Drop tables in reverse dependency order
            tables = ["user_sessions", "user_profiles", "users"]
            
            for table in tables:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                logger.warning(f"Dropped table: {table}")
        
        # Close engine
        await engine.dispose()
        
        logger.warning("All user management tables dropped")
        
    except Exception as e:
        logger.error(f"Failed to drop user management tables: {e}")
        raise


async def verify_user_tables():
    """Verify that all user tables were created successfully"""
    
    try:
        # Get database configuration
        config = get_config()
        db_config = config.database
        
        # Create async engine with proper SSL configuration
        engine = create_async_engine(
            db_config.get_connection_url(async_driver=True),
            echo=False,
            connect_args=db_config.get_connect_args()
        )
        
        async with engine.begin() as conn:
            # Check if tables exist
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = :database_name 
                AND table_name IN ('users', 'user_profiles', 'user_sessions')
                ORDER BY table_name
            """)
            
            result = await conn.execute(tables_query, {"database_name": db_config.database})
            tables = result.fetchall()
            
            expected_tables = {"users", "user_profiles", "user_sessions"}
            found_tables = {row[0] for row in tables}
            
            if found_tables == expected_tables:
                logger.info("✓ All user management tables verified successfully")
                
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
        logger.error(f"Failed to verify user tables: {e}")
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
                await create_user_tables()
            elif command == "drop":
                await drop_user_tables()
            elif command == "verify":
                success = await verify_user_tables()
                sys.exit(0 if success else 1)
            else:
                print("Usage: python create_user_tables.py [create|drop|verify]")
                sys.exit(1)
        else:
            # Default: create tables
            await create_user_tables()
            await verify_user_tables()
    
    asyncio.run(main())


# Migration metadata
MIGRATION_NAME = "create_user_tables"
MIGRATION_VERSION = "001"
MIGRATION_DESCRIPTION = "Create tables for user management"