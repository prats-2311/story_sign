"""
Create synchronization tables for cross-platform sync functionality
"""

import asyncio
from sqlalchemy import text
from core.database_service import DatabaseService


async def create_sync_tables():
    """
    Create all synchronization-related tables
    """
    db_service = DatabaseService()
    await db_service.initialize()
    
    try:
        async with db_service.get_session() as session:
            # Device Sessions table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS device_sessions (
                    id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36) NOT NULL,
                    device_id VARCHAR(32) NOT NULL,
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    device_info JSON NOT NULL,
                    session_data JSON DEFAULT ('{}'),
                    sync_version INT DEFAULT 1,
                    last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    bandwidth_profile VARCHAR(20) DEFAULT 'medium',
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    
                    INDEX idx_device_sessions_user_id (user_id),
                    INDEX idx_device_sessions_device_id (device_id),
                    INDEX idx_device_sessions_token (session_token),
                    INDEX idx_device_sessions_active (is_active),
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """))
            
            # Sync Operations table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS sync_operations (
                    id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36) NOT NULL,
                    device_session_id CHAR(36),
                    operation_type VARCHAR(50) NOT NULL,
                    operation_data JSON NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    priority INT DEFAULT 1,
                    retry_count INT DEFAULT 0,
                    checksum VARCHAR(32) NOT NULL,
                    error_message TEXT,
                    completed_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    
                    INDEX idx_sync_operations_user_id (user_id),
                    INDEX idx_sync_operations_status (status),
                    INDEX idx_sync_operations_type (operation_type),
                    INDEX idx_sync_operations_priority (priority),
                    INDEX idx_sync_operations_created (created_at),
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (device_session_id) REFERENCES device_sessions(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """))
            
            # Sync Conflicts table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS sync_conflicts (
                    id CHAR(36) PRIMARY KEY,
                    sync_operation_id CHAR(36) NOT NULL,
                    field_name VARCHAR(100) NOT NULL,
                    server_value JSON,
                    client_value JSON,
                    conflict_type VARCHAR(50) NOT NULL,
                    resolution_strategy VARCHAR(50),
                    resolved_value JSON,
                    is_resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMP NULL,
                    resolved_by VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    
                    INDEX idx_sync_conflicts_operation (sync_operation_id),
                    INDEX idx_sync_conflicts_resolved (is_resolved),
                    INDEX idx_sync_conflicts_type (conflict_type),
                    
                    FOREIGN KEY (sync_operation_id) REFERENCES sync_operations(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """))
            
            # Offline Changes table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS offline_changes (
                    id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36) NOT NULL,
                    device_id VARCHAR(32) NOT NULL,
                    change_type VARCHAR(50) NOT NULL,
                    entity_type VARCHAR(50) NOT NULL,
                    entity_id VARCHAR(36),
                    change_data JSON NOT NULL,
                    local_timestamp TIMESTAMP NOT NULL,
                    is_processed BOOLEAN DEFAULT FALSE,
                    processed_at TIMESTAMP NULL,
                    conflict_resolution JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    
                    INDEX idx_offline_changes_user_id (user_id),
                    INDEX idx_offline_changes_device_id (device_id),
                    INDEX idx_offline_changes_processed (is_processed),
                    INDEX idx_offline_changes_type (change_type),
                    INDEX idx_offline_changes_entity (entity_type, entity_id),
                    INDEX idx_offline_changes_timestamp (local_timestamp),
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """))
            
            # Sync Metrics table
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS sync_metrics (
                    id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36) NOT NULL,
                    device_id VARCHAR(32) NOT NULL,
                    sync_duration_ms INT,
                    data_size_bytes INT,
                    operations_count INT,
                    conflicts_count INT DEFAULT 0,
                    bandwidth_profile VARCHAR(20),
                    success_rate FLOAT,
                    error_count INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    
                    INDEX idx_sync_metrics_user_id (user_id),
                    INDEX idx_sync_metrics_device_id (device_id),
                    INDEX idx_sync_metrics_created (created_at),
                    INDEX idx_sync_metrics_bandwidth (bandwidth_profile),
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """))
            
            await session.commit()
            print("✅ Synchronization tables created successfully")
            
    except Exception as e:
        print(f"❌ Error creating synchronization tables: {e}")
        raise
    finally:
        await db_service.cleanup()


async def drop_sync_tables():
    """
    Drop all synchronization tables (for testing/cleanup)
    """
    db_service = DatabaseService()
    await db_service.initialize()
    
    try:
        async with db_service.get_session() as session:
            # Drop tables in reverse order due to foreign key constraints
            tables = [
                "sync_metrics",
                "offline_changes", 
                "sync_conflicts",
                "sync_operations",
                "device_sessions"
            ]
            
            for table in tables:
                await session.execute(text(f"DROP TABLE IF EXISTS {table}"))
            
            await session.commit()
            print("✅ Synchronization tables dropped successfully")
            
    except Exception as e:
        print(f"❌ Error dropping synchronization tables: {e}")
        raise
    finally:
        await db_service.cleanup()


async def verify_sync_tables():
    """
    Verify that all synchronization tables exist and have correct structure
    """
    db_service = DatabaseService()
    await db_service.initialize()
    
    try:
        async with db_service.get_session() as session:
            # Check if tables exist
            tables_to_check = [
                "device_sessions",
                "sync_operations", 
                "sync_conflicts",
                "offline_changes",
                "sync_metrics"
            ]
            
            for table in tables_to_check:
                result = await session.execute(text(f"""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    AND table_name = '{table}'
                """))
                
                count = result.scalar()
                if count == 0:
                    print(f"❌ Table {table} does not exist")
                    return False
                else:
                    print(f"✅ Table {table} exists")
            
            # Check indexes
            index_checks = [
                ("device_sessions", "idx_device_sessions_user_id"),
                ("sync_operations", "idx_sync_operations_user_id"),
                ("sync_conflicts", "idx_sync_conflicts_operation"),
                ("offline_changes", "idx_offline_changes_user_id"),
                ("sync_metrics", "idx_sync_metrics_user_id")
            ]
            
            for table, index in index_checks:
                result = await session.execute(text(f"""
                    SELECT COUNT(*) as count
                    FROM information_schema.statistics
                    WHERE table_schema = DATABASE()
                    AND table_name = '{table}'
                    AND index_name = '{index}'
                """))
                
                count = result.scalar()
                if count == 0:
                    print(f"⚠️  Index {index} on table {table} does not exist")
                else:
                    print(f"✅ Index {index} on table {table} exists")
            
            print("✅ Synchronization tables verification completed")
            return True
            
    except Exception as e:
        print(f"❌ Error verifying synchronization tables: {e}")
        return False
    finally:
        await db_service.cleanup()


async def add_sample_sync_data():
    """
    Add sample synchronization data for testing
    """
    db_service = DatabaseService()
    await db_service.initialize()
    
    try:
        async with db_service.get_session() as session:
            # Sample device session
            await session.execute(text("""
                INSERT INTO device_sessions (
                    id, user_id, device_id, session_token, device_info, 
                    session_data, bandwidth_profile, expires_at
                ) VALUES (
                    'sample-session-1',
                    'sample-user-1', 
                    'web-chrome-001',
                    'token-12345',
                    '{"platform": "web", "browser": "chrome", "version": "91.0"}',
                    '{"current_story": "story-1", "progress": {"score": 85}}',
                    'high',
                    DATE_ADD(NOW(), INTERVAL 1 HOUR)
                )
            """))
            
            # Sample sync operation
            await session.execute(text("""
                INSERT INTO sync_operations (
                    id, user_id, device_session_id, operation_type, 
                    operation_data, status, priority, checksum
                ) VALUES (
                    'sample-operation-1',
                    'sample-user-1',
                    'sample-session-1',
                    'practice_session',
                    '{"session_id": "session-1", "score": 90}',
                    'completed',
                    1,
                    'abc123'
                )
            """))
            
            # Sample offline change
            await session.execute(text("""
                INSERT INTO offline_changes (
                    id, user_id, device_id, change_type, entity_type,
                    entity_id, change_data, local_timestamp
                ) VALUES (
                    'sample-offline-1',
                    'sample-user-1',
                    'mobile-android-001',
                    'update',
                    'practice_session',
                    'session-1',
                    '{"score": 95, "completed_offline": true}',
                    NOW()
                )
            """))
            
            # Sample sync metrics
            await session.execute(text("""
                INSERT INTO sync_metrics (
                    id, user_id, device_id, sync_duration_ms, data_size_bytes,
                    operations_count, conflicts_count, bandwidth_profile, success_rate
                ) VALUES (
                    'sample-metrics-1',
                    'sample-user-1',
                    'web-chrome-001',
                    150,
                    2048,
                    5,
                    0,
                    'high',
                    1.0
                )
            """))
            
            await session.commit()
            print("✅ Sample synchronization data added successfully")
            
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")
        raise
    finally:
        await db_service.cleanup()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "create":
            asyncio.run(create_sync_tables())
        elif command == "drop":
            asyncio.run(drop_sync_tables())
        elif command == "verify":
            asyncio.run(verify_sync_tables())
        elif command == "sample":
            asyncio.run(add_sample_sync_data())
        else:
            print("Usage: python create_sync_tables.py [create|drop|verify|sample]")
    else:
        # Default: create tables
        asyncio.run(create_sync_tables())