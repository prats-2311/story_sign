"""
Database migration for collaborative learning features
Creates tables for learning groups, memberships, collaborative sessions, and analytics
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def create_collaborative_tables(session: AsyncSession) -> None:
    """Create all collaborative learning tables"""
    
    # Create learning_groups table
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS learning_groups (
            id CHAR(36) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            creator_id CHAR(36) NOT NULL,
            privacy_level VARCHAR(20) NOT NULL DEFAULT 'private',
            is_public BOOLEAN NOT NULL DEFAULT FALSE,
            join_code VARCHAR(20) UNIQUE,
            max_members INT,
            requires_approval BOOLEAN NOT NULL DEFAULT FALSE,
            skill_focus JSON,
            difficulty_level VARCHAR(20),
            learning_goals JSON,
            tags JSON,
            language VARCHAR(10) NOT NULL DEFAULT 'en',
            timezone VARCHAR(50),
            last_activity_at DATETIME(6),
            total_sessions INT NOT NULL DEFAULT 0,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            archived_at DATETIME(6),
            created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            
            INDEX idx_learning_groups_creator_active (creator_id, is_active),
            INDEX idx_learning_groups_privacy_public (privacy_level, is_public),
            INDEX idx_learning_groups_difficulty (difficulty_level),
            INDEX idx_learning_groups_last_activity (last_activity_at),
            INDEX idx_learning_groups_join_code (join_code),
            
            CONSTRAINT check_valid_privacy_level CHECK (privacy_level IN ('public', 'private', 'invite_only')),
            CONSTRAINT check_valid_difficulty CHECK (difficulty_level IS NULL OR difficulty_level IN ('beginner', 'intermediate', 'advanced')),
            CONSTRAINT check_max_members_positive CHECK (max_members IS NULL OR max_members > 0),
            CONSTRAINT check_total_sessions_positive CHECK (total_sessions >= 0),
            
            FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))
    
    # Create group_memberships table
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS group_memberships (
            id CHAR(36) PRIMARY KEY,
            group_id CHAR(36) NOT NULL,
            user_id CHAR(36) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'member',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            joined_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            left_at DATETIME(6),
            invited_by CHAR(36),
            approved_by CHAR(36),
            approved_at DATETIME(6),
            data_sharing_level VARCHAR(20) NOT NULL DEFAULT 'basic',
            share_progress BOOLEAN NOT NULL DEFAULT TRUE,
            share_performance BOOLEAN NOT NULL DEFAULT FALSE,
            share_practice_sessions BOOLEAN NOT NULL DEFAULT FALSE,
            allow_peer_feedback BOOLEAN NOT NULL DEFAULT TRUE,
            notify_new_sessions BOOLEAN NOT NULL DEFAULT TRUE,
            notify_group_updates BOOLEAN NOT NULL DEFAULT TRUE,
            notify_peer_achievements BOOLEAN NOT NULL DEFAULT TRUE,
            custom_role_name VARCHAR(100),
            member_notes TEXT,
            created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            
            UNIQUE KEY uq_group_user_membership (group_id, user_id),
            INDEX idx_group_memberships_group_active (group_id, is_active),
            INDEX idx_group_memberships_user_active (user_id, is_active),
            INDEX idx_group_memberships_role (role),
            INDEX idx_group_memberships_joined_at (joined_at),
            
            CONSTRAINT check_valid_role CHECK (role IN ('owner', 'educator', 'moderator', 'member', 'observer')),
            CONSTRAINT check_valid_data_sharing_level CHECK (data_sharing_level IN ('none', 'basic', 'detailed', 'full')),
            
            FOREIGN KEY (group_id) REFERENCES learning_groups(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (invited_by) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))
    
    # Create collaborative_sessions table
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS collaborative_sessions (
            id CHAR(36) PRIMARY KEY,
            session_name VARCHAR(255) NOT NULL,
            description TEXT,
            host_id CHAR(36) NOT NULL,
            group_id CHAR(36) NOT NULL,
            story_id CHAR(36),
            story_content JSON,
            session_config JSON,
            participant_ids JSON,
            max_participants INT,
            scheduled_start DATETIME(6),
            scheduled_end DATETIME(6),
            actual_start DATETIME(6),
            actual_end DATETIME(6),
            status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
            session_data JSON,
            performance_summary JSON,
            allow_peer_feedback BOOLEAN NOT NULL DEFAULT TRUE,
            enable_voice_chat BOOLEAN NOT NULL DEFAULT FALSE,
            enable_text_chat BOOLEAN NOT NULL DEFAULT TRUE,
            record_session BOOLEAN NOT NULL DEFAULT FALSE,
            is_public BOOLEAN NOT NULL DEFAULT FALSE,
            requires_approval BOOLEAN NOT NULL DEFAULT FALSE,
            difficulty_level VARCHAR(20),
            skill_focus JSON,
            tags JSON,
            created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            
            INDEX idx_collaborative_sessions_host_status (host_id, status),
            INDEX idx_collaborative_sessions_group_scheduled (group_id, scheduled_start),
            INDEX idx_collaborative_sessions_status_start (status, scheduled_start),
            INDEX idx_collaborative_sessions_public (is_public),
            
            CONSTRAINT check_valid_status CHECK (status IN ('scheduled', 'active', 'paused', 'completed', 'cancelled')),
            CONSTRAINT check_valid_difficulty CHECK (difficulty_level IS NULL OR difficulty_level IN ('beginner', 'intermediate', 'advanced')),
            CONSTRAINT check_max_participants_positive CHECK (max_participants IS NULL OR max_participants > 0),
            
            FOREIGN KEY (host_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (group_id) REFERENCES learning_groups(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))
    
    # Create group_analytics table
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS group_analytics (
            id CHAR(36) PRIMARY KEY,
            group_id CHAR(36) NOT NULL,
            period_start DATETIME(6) NOT NULL,
            period_end DATETIME(6) NOT NULL,
            period_type VARCHAR(20) NOT NULL,
            total_members INT NOT NULL DEFAULT 0,
            active_members INT NOT NULL DEFAULT 0,
            total_sessions INT NOT NULL DEFAULT 0,
            collaborative_sessions INT NOT NULL DEFAULT 0,
            total_practice_time INT NOT NULL DEFAULT 0,
            average_group_score FLOAT,
            average_completion_rate FLOAT,
            skill_progress JSON,
            peer_feedback_count INT NOT NULL DEFAULT 0,
            group_interactions INT NOT NULL DEFAULT 0,
            milestones_achieved JSON,
            group_achievements JSON,
            anonymized_data JSON,
            created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            
            UNIQUE KEY uq_group_analytics_period (group_id, period_start, period_end, period_type),
            INDEX idx_group_analytics_group_period (group_id, period_start, period_end),
            INDEX idx_group_analytics_period_type (period_type),
            
            CONSTRAINT check_total_members_positive CHECK (total_members >= 0),
            CONSTRAINT check_active_members_positive CHECK (active_members >= 0),
            CONSTRAINT check_active_members_valid CHECK (active_members <= total_members),
            CONSTRAINT check_total_sessions_positive CHECK (total_sessions >= 0),
            CONSTRAINT check_collaborative_sessions_positive CHECK (collaborative_sessions >= 0),
            CONSTRAINT check_collaborative_sessions_valid CHECK (collaborative_sessions <= total_sessions),
            CONSTRAINT check_practice_time_positive CHECK (total_practice_time >= 0),
            CONSTRAINT check_average_score_range CHECK (average_group_score IS NULL OR (average_group_score >= 0.0 AND average_group_score <= 1.0)),
            CONSTRAINT check_completion_rate_range CHECK (average_completion_rate IS NULL OR (average_completion_rate >= 0.0 AND average_completion_rate <= 1.0)),
            CONSTRAINT check_feedback_count_positive CHECK (peer_feedback_count >= 0),
            CONSTRAINT check_interactions_positive CHECK (group_interactions >= 0),
            CONSTRAINT check_valid_period_type CHECK (period_type IN ('daily', 'weekly', 'monthly', 'custom')),
            
            FOREIGN KEY (group_id) REFERENCES learning_groups(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """))
    
    await session.commit()


async def drop_collaborative_tables(session: AsyncSession) -> None:
    """Drop all collaborative learning tables (for rollback)"""
    
    # Drop tables in reverse order due to foreign key constraints
    tables = [
        "group_analytics",
        "collaborative_sessions", 
        "group_memberships",
        "learning_groups"
    ]
    
    for table in tables:
        await session.execute(text(f"DROP TABLE IF EXISTS {table}"))
    
    await session.commit()


# Migration metadata
MIGRATION_NAME = "create_collaborative_tables"
MIGRATION_VERSION = "001"
MIGRATION_DESCRIPTION = "Create tables for collaborative learning features"