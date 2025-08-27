"""
Check database migration status and identify missing tables
"""

import asyncio
import logging
from typing import Dict, List, Set
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from config import get_config

logger = logging.getLogger(__name__)


async def check_database_status():
    """Check current database status and identify missing tables"""
    
    print("🔍 Checking TiDB Database Migration Status")
    print("=" * 50)
    
    try:
        # Get database configuration
        config = get_config()
        db_config = config.database
        
        # Create async engine
        connection_url = db_config.get_connection_url(async_driver=True)
        engine = create_async_engine(connection_url, echo=False)
        
        print(f"📊 Database: {db_config.database}")
        print(f"🏠 Host: {db_config.host}:{db_config.port}")
        print(f"👤 User: {db_config.username}")
        print()
        
        async with engine.begin() as conn:
            # Test connection
            await conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            
            # Get existing tables
            existing_tables = await get_existing_tables(conn, db_config.database)
            print(f"📋 Found {len(existing_tables)} existing tables")
            
            # Define expected tables from models
            expected_tables = get_expected_tables()
            print(f"🎯 Expected {len(expected_tables)} tables from models")
            
            # Check migration status
            await check_migration_status(existing_tables, expected_tables)
            
            # Check table structures for existing tables
            await check_table_structures(conn, db_config.database, existing_tables)
            
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def get_existing_tables(conn, database_name: str) -> Set[str]:
    """Get list of existing tables in the database"""
    
    query = text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = :database_name
        ORDER BY table_name
    """)
    
    result = await conn.execute(query, {"database_name": database_name})
    tables = {row[0] for row in result.fetchall()}
    
    if tables:
        print("\n📋 Existing Tables:")
        for table in sorted(tables):
            print(f"  ✓ {table}")
    else:
        print("\n📋 No existing tables found")
    
    return tables


def get_expected_tables() -> Dict[str, str]:
    """Get expected tables from models with their migration source"""
    
    return {
        # User management tables
        "users": "user_models",
        "user_profiles": "user_models", 
        "user_sessions": "user_models",
        
        # Content management tables
        "stories": "content_migration",
        "story_tags": "content_migration",
        "story_versions": "content_migration",
        "story_ratings": "content_migration",
        "content_approvals": "content_migration",
        
        # Progress tracking tables
        "practice_sessions": "progress_migration",
        "sentence_attempts": "progress_migration",
        "user_progress": "progress_migration",
        
        # Collaborative learning tables
        "learning_groups": "collaborative_migration",
        "group_memberships": "collaborative_migration",
        "collaborative_sessions": "collaborative_migration",
        "group_analytics": "collaborative_migration",
        
        # Plugin system tables
        "plugins": "plugin_models",
        "plugin_data": "plugin_models"
    }


async def check_migration_status(existing_tables: Set[str], expected_tables: Dict[str, str]):
    """Check which migrations have been applied and which are missing"""
    
    print("\n🔄 Migration Status Analysis:")
    print("-" * 30)
    
    # Group by migration source
    migration_groups = {}
    for table, source in expected_tables.items():
        if source not in migration_groups:
            migration_groups[source] = {"expected": [], "existing": [], "missing": []}
        
        migration_groups[source]["expected"].append(table)
        if table in existing_tables:
            migration_groups[source]["existing"].append(table)
        else:
            migration_groups[source]["missing"].append(table)
    
    # Report status for each migration group
    for source, tables in migration_groups.items():
        expected_count = len(tables["expected"])
        existing_count = len(tables["existing"])
        missing_count = len(tables["missing"])
        
        if missing_count == 0:
            status = "✅ COMPLETE"
        elif existing_count == 0:
            status = "❌ NOT APPLIED"
        else:
            status = "⚠️  PARTIAL"
        
        print(f"\n{status} {source}")
        print(f"  Expected: {expected_count} tables")
        print(f"  Existing: {existing_count} tables")
        
        if tables["existing"]:
            print(f"  ✓ Applied: {', '.join(sorted(tables['existing']))}")
        
        if tables["missing"]:
            print(f"  ❌ Missing: {', '.join(sorted(tables['missing']))}")
    
    # Overall summary
    total_expected = len(expected_tables)
    total_existing = len(existing_tables.intersection(expected_tables.keys()))
    total_missing = total_expected - total_existing
    
    print(f"\n📊 Overall Migration Status:")
    print(f"  Total Expected: {total_expected}")
    print(f"  Total Applied: {total_existing}")
    print(f"  Total Missing: {total_missing}")
    
    if total_missing == 0:
        print("  🎉 All migrations applied!")
    else:
        print(f"  ⚠️  {total_missing} tables need migration")
    
    return total_missing == 0


async def check_table_structures(conn, database_name: str, existing_tables: Set[str]):
    """Check structure of existing tables"""
    
    if not existing_tables:
        return
    
    print(f"\n🏗️  Table Structure Analysis:")
    print("-" * 30)
    
    for table_name in sorted(existing_tables):
        try:
            # Get column information
            columns_query = text("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    column_key
                FROM information_schema.columns
                WHERE table_schema = :database_name 
                AND table_name = :table_name
                ORDER BY ordinal_position
            """)
            
            result = await conn.execute(
                columns_query, 
                {"database_name": database_name, "table_name": table_name}
            )
            columns = result.fetchall()
            
            # Get index information
            indexes_query = text("""
                SELECT 
                    index_name,
                    column_name,
                    non_unique
                FROM information_schema.statistics
                WHERE table_schema = :database_name 
                AND table_name = :table_name
                ORDER BY index_name, seq_in_index
            """)
            
            result = await conn.execute(
                indexes_query,
                {"database_name": database_name, "table_name": table_name}
            )
            indexes = result.fetchall()
            
            print(f"\n📋 {table_name}")
            print(f"  Columns: {len(columns)}")
            print(f"  Indexes: {len(set(idx[0] for idx in indexes))}")
            
            # Show key columns
            key_columns = [col[0] for col in columns if col[4] in ('PRI', 'UNI', 'MUL')]
            if key_columns:
                print(f"  Key columns: {', '.join(key_columns)}")
            
        except Exception as e:
            print(f"  ❌ Error analyzing {table_name}: {e}")


async def create_missing_migrations():
    """Create migration files for missing tables"""
    
    print("\n🔧 Creating Missing Migration Files:")
    print("-" * 35)
    
    # Check if user tables migration exists
    user_migration_path = "StorySign_Platform/backend/migrations/create_user_tables.py"
    plugin_migration_path = "StorySign_Platform/backend/migrations/create_plugin_tables.py"
    
    # Create user tables migration
    if not os.path.exists(user_migration_path):
        await create_user_tables_migration()
        print("✅ Created user tables migration")
    
    # Create plugin tables migration  
    if not os.path.exists(plugin_migration_path):
        await create_plugin_tables_migration()
        print("✅ Created plugin tables migration")


async def create_user_tables_migration():
    """Create migration for user tables"""
    
    migration_content = '''"""
Database migration for user management tables
Creates users, user_profiles, and user_sessions tables
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def create_user_tables(session: AsyncSession) -> None:
    """Create all user management tables"""
    
    # Create users table
    await session.execute(text("""
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
            INDEX idx_users_verified (is_verified)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))
    
    # Create user_profiles table
    await session.execute(text("""
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
            
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))
    
    # Create user_sessions table
    await session.execute(text("""
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
    
    await session.commit()


async def drop_user_tables(session: AsyncSession) -> None:
    """Drop all user management tables (for rollback)"""
    
    tables = ["user_sessions", "user_profiles", "users"]
    
    for table in tables:
        await session.execute(text(f"DROP TABLE IF EXISTS {table}"))
    
    await session.commit()


# Migration metadata
MIGRATION_NAME = "create_user_tables"
MIGRATION_VERSION = "001"
MIGRATION_DESCRIPTION = "Create tables for user management"
'''
    
    with open("StorySign_Platform/backend/migrations/create_user_tables.py", "w") as f:
        f.write(migration_content)


async def create_plugin_tables_migration():
    """Create migration for plugin tables"""
    
    migration_content = '''"""
Database migration for plugin system tables
Creates plugins and plugin_data tables
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def create_plugin_tables(session: AsyncSession) -> None:
    """Create all plugin system tables"""
    
    # Create plugins table
    await session.execute(text("""
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
            
            FOREIGN KEY (installed_by) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))
    
    # Create plugin_data table
    await session.execute(text("""
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
            
            FOREIGN KEY (plugin_id) REFERENCES plugins(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))
    
    await session.commit()


async def drop_plugin_tables(session: AsyncSession) -> None:
    """Drop all plugin system tables (for rollback)"""
    
    tables = ["plugin_data", "plugins"]
    
    for table in tables:
        await session.execute(text(f"DROP TABLE IF EXISTS {table}"))
    
    await session.commit()


# Migration metadata
MIGRATION_NAME = "create_plugin_tables"
MIGRATION_VERSION = "001"
MIGRATION_DESCRIPTION = "Create tables for plugin system"
'''
    
    with open("StorySign_Platform/backend/migrations/create_plugin_tables.py", "w") as f:
        f.write(migration_content)


if __name__ == "__main__":
    import os
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        success = await check_database_status()
        
        if success:
            print("\n🎉 Database migration check completed!")
            print("\nNext steps:")
            print("  1. Run missing migrations if any were identified")
            print("  2. Verify all tables are created correctly")
            print("  3. Test application functionality")
        else:
            print("\n❌ Database migration check failed!")
            return False
        
        return True
    
    success = asyncio.run(main())
    exit(0 if success else 1)