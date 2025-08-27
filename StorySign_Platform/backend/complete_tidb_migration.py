#!/usr/bin/env python3
"""
Complete TiDB Migration Script
Creates all remaining database tables for StorySign platform
"""

import asyncio
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from config import get_config

logger = logging.getLogger(__name__)


async def create_content_tables():
    """Create content management tables"""
    
    try:
        config = get_config()
        db_config = config.database
        
        engine = create_async_engine(
            db_config.get_connection_url(async_driver=True),
            echo=False,  # Disable echo to reduce output
            connect_args=db_config.get_connect_args(),
            pool_timeout=60,  # Increase timeout
        )
        
        logger.info("Creating content management tables...")
        
        async with engine.begin() as conn:
            # Create stories table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS stories (
                    id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    content JSON NOT NULL,
                    difficulty_level VARCHAR(20) NOT NULL DEFAULT 'beginner',
                    category VARCHAR(100),
                    tags JSON,
                    is_published BOOLEAN NOT NULL DEFAULT FALSE,
                    created_by CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    INDEX idx_stories_difficulty (difficulty_level),
                    INDEX idx_stories_category (category),
                    INDEX idx_stories_published (is_published),
                    INDEX idx_stories_created_by (created_by),
                    
                    CONSTRAINT check_valid_difficulty_stories CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
                    CONSTRAINT fk_stories_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # Create lessons table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS lessons (
                    id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    content JSON NOT NULL,
                    difficulty_level VARCHAR(20) NOT NULL DEFAULT 'beginner',
                    skill_areas JSON,
                    estimated_duration INTEGER,
                    is_published BOOLEAN NOT NULL DEFAULT FALSE,
                    created_by CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    INDEX idx_lessons_difficulty (difficulty_level),
                    INDEX idx_lessons_published (is_published),
                    INDEX idx_lessons_created_by (created_by),
                    
                    CONSTRAINT check_valid_difficulty_lessons CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
                    CONSTRAINT fk_lessons_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # Create vocabulary table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS vocabulary (
                    id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL PRIMARY KEY,
                    word VARCHAR(255) NOT NULL,
                    definition TEXT,
                    category VARCHAR(100),
                    difficulty_level VARCHAR(20) NOT NULL DEFAULT 'beginner',
                    gesture_data JSON,
                    video_url VARCHAR(500),
                    created_by CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    INDEX idx_vocabulary_word (word),
                    INDEX idx_vocabulary_category (category),
                    INDEX idx_vocabulary_difficulty (difficulty_level),
                    INDEX idx_vocabulary_created_by (created_by),
                    
                    CONSTRAINT check_valid_difficulty_vocabulary CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
                    CONSTRAINT fk_vocabulary_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            logger.info("✅ Created content management tables")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        logger.error(f"Failed to create content tables: {e}")
        return False


async def create_collaborative_tables():
    """Create collaborative features tables"""
    
    try:
        config = get_config()
        db_config = config.database
        
        engine = create_async_engine(
            db_config.get_connection_url(async_driver=True),
            echo=False,
            connect_args=db_config.get_connect_args(),
            pool_timeout=60,
        )
        
        logger.info("Creating collaborative features tables...")
        
        async with engine.begin() as conn:
            # Create shared_sessions table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS shared_sessions (
                    id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL PRIMARY KEY,
                    session_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                    host_user_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                    session_name VARCHAR(255),
                    max_participants INTEGER DEFAULT 4,
                    current_participants INTEGER DEFAULT 1,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    session_data JSON,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    INDEX idx_shared_sessions_session_id (session_id),
                    INDEX idx_shared_sessions_host (host_user_id),
                    INDEX idx_shared_sessions_active (is_active),
                    
                    CONSTRAINT fk_shared_sessions_session_id FOREIGN KEY (session_id) REFERENCES practice_sessions(id) ON DELETE CASCADE,
                    CONSTRAINT fk_shared_sessions_host FOREIGN KEY (host_user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # Create collaboration_invites table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS collaboration_invites (
                    id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL PRIMARY KEY,
                    shared_session_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                    inviter_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                    invitee_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    invited_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    responded_at DATETIME(6),
                    
                    INDEX idx_collaboration_invites_session (shared_session_id),
                    INDEX idx_collaboration_invites_inviter (inviter_id),
                    INDEX idx_collaboration_invites_invitee (invitee_id),
                    INDEX idx_collaboration_invites_status (status),
                    
                    CONSTRAINT check_valid_invite_status CHECK (status IN ('pending', 'accepted', 'declined', 'expired')),
                    CONSTRAINT fk_collaboration_invites_session FOREIGN KEY (shared_session_id) REFERENCES shared_sessions(id) ON DELETE CASCADE,
                    CONSTRAINT fk_collaboration_invites_inviter FOREIGN KEY (inviter_id) REFERENCES users(id) ON DELETE CASCADE,
                    CONSTRAINT fk_collaboration_invites_invitee FOREIGN KEY (invitee_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            logger.info("✅ Created collaborative features tables")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        logger.error(f"Failed to create collaborative tables: {e}")
        return False


async def create_plugin_tables():
    """Create plugin system tables"""
    
    try:
        config = get_config()
        db_config = config.database
        
        engine = create_async_engine(
            db_config.get_connection_url(async_driver=True),
            echo=False,
            connect_args=db_config.get_connect_args(),
            pool_timeout=60,
        )
        
        logger.info("Creating plugin system tables...")
        
        async with engine.begin() as conn:
            # Create plugins table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS plugins (
                    id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL UNIQUE,
                    version VARCHAR(50) NOT NULL,
                    description TEXT,
                    author VARCHAR(255),
                    plugin_type VARCHAR(50) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'inactive',
                    config JSON,
                    permissions JSON,
                    installed_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    INDEX idx_plugins_name (name),
                    INDEX idx_plugins_type (plugin_type),
                    INDEX idx_plugins_status (status),
                    
                    CONSTRAINT check_valid_plugin_status CHECK (status IN ('active', 'inactive', 'error', 'updating'))
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # Create plugin_configs table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS plugin_configs (
                    id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL PRIMARY KEY,
                    plugin_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                    user_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                    config_key VARCHAR(255) NOT NULL,
                    config_value JSON,
                    is_global BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    INDEX idx_plugin_configs_plugin (plugin_id),
                    INDEX idx_plugin_configs_user (user_id),
                    INDEX idx_plugin_configs_key (config_key),
                    INDEX idx_plugin_configs_global (is_global),
                    
                    CONSTRAINT fk_plugin_configs_plugin FOREIGN KEY (plugin_id) REFERENCES plugins(id) ON DELETE CASCADE,
                    CONSTRAINT fk_plugin_configs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # Create plugin_permissions table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS plugin_permissions (
                    id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL PRIMARY KEY,
                    plugin_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
                    permission_type VARCHAR(100) NOT NULL,
                    resource VARCHAR(255),
                    granted BOOLEAN NOT NULL DEFAULT FALSE,
                    granted_by CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
                    granted_at DATETIME(6),
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    
                    INDEX idx_plugin_permissions_plugin (plugin_id),
                    INDEX idx_plugin_permissions_type (permission_type),
                    INDEX idx_plugin_permissions_granted (granted),
                    
                    CONSTRAINT fk_plugin_permissions_plugin FOREIGN KEY (plugin_id) REFERENCES plugins(id) ON DELETE CASCADE,
                    CONSTRAINT fk_plugin_permissions_granted_by FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            logger.info("✅ Created plugin system tables")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        logger.error(f"Failed to create plugin tables: {e}")
        return False


async def verify_all_tables():
    """Verify all tables were created successfully"""
    
    try:
        config = get_config()
        db_config = config.database
        
        engine = create_async_engine(
            db_config.get_connection_url(async_driver=True),
            echo=False,
            connect_args=db_config.get_connect_args()
        )
        
        async with engine.begin() as conn:
            # Get all tables
            tables_query = text("""
                SELECT table_name, table_rows, data_length
                FROM information_schema.tables 
                WHERE table_schema = :database_name
                ORDER BY table_name
            """)
            
            result = await conn.execute(tables_query, {"database_name": db_config.database})
            tables = result.fetchall()
            
            logger.info("📋 All tables in database:")
            for table in tables:
                logger.info(f"   ✓ {table.table_name}: {table.table_rows} rows, {table.data_length} bytes")
            
            # Check foreign keys
            fk_query = text("""
                SELECT 
                    TABLE_NAME,
                    COLUMN_NAME,
                    CONSTRAINT_NAME,
                    REFERENCED_TABLE_NAME,
                    REFERENCED_COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = :database_name
                AND REFERENCED_TABLE_NAME IS NOT NULL
                ORDER BY TABLE_NAME, COLUMN_NAME
            """)
            
            fk_result = await conn.execute(fk_query, {"database_name": db_config.database})
            foreign_keys = fk_result.fetchall()
            
            logger.info("🔗 Foreign key relationships:")
            for fk in foreign_keys:
                logger.info(f"   {fk.TABLE_NAME}.{fk.COLUMN_NAME} -> {fk.REFERENCED_TABLE_NAME}.{fk.REFERENCED_COLUMN_NAME}")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        logger.error(f"Failed to verify tables: {e}")
        return False


async def main():
    """Main migration function"""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🗄️  Complete TiDB Migration for StorySign")
    print("=" * 60)
    print("This will create all remaining database tables")
    print()
    
    # Test connection first
    try:
        config = get_config()
        db_config = config.database
        
        engine = create_async_engine(
            db_config.get_connection_url(async_driver=True),
            echo=False,
            connect_args=db_config.get_connect_args()
        )
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            
            if row:
                logger.info("✅ Database connection successful")
            else:
                logger.error("❌ Database connection failed")
                return 1
        
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return 1
    
    # Run migrations
    migrations = [
        ("Content Management", create_content_tables),
        ("Collaborative Features", create_collaborative_tables),
        ("Plugin System", create_plugin_tables),
    ]
    
    success_count = 0
    
    for name, migration_func in migrations:
        logger.info(f"🔨 Creating {name} tables...")
        
        try:
            success = await migration_func()
            if success:
                logger.info(f"✅ {name} migration completed")
                success_count += 1
            else:
                logger.error(f"❌ {name} migration failed")
        except Exception as e:
            logger.error(f"❌ {name} migration failed: {e}")
    
    # Verify all tables
    logger.info("🔍 Verifying all tables...")
    await verify_all_tables()
    
    print("\n" + "=" * 60)
    print(f"🎯 Migration Summary: {success_count}/{len(migrations)} migrations completed")
    
    if success_count == len(migrations):
        print("🎉 All migrations completed successfully!")
        print("\nYour StorySign database is now fully set up with:")
        print("• User Management (users, user_profiles, user_sessions)")
        print("• Progress Tracking (practice_sessions, sentence_attempts, user_progress)")
        print("• Content Management (stories, lessons, vocabulary)")
        print("• Collaborative Features (shared_sessions, collaboration_invites)")
        print("• Plugin System (plugins, plugin_configs, plugin_permissions)")
        return 0
    else:
        print(f"⚠️  {len(migrations) - success_count} migrations failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)