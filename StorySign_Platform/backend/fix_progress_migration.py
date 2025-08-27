#!/usr/bin/env python3
"""
Fixed Progress Tables Migration
Creates progress tracking tables with proper foreign key compatibility
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


async def create_progress_tables_fixed():
    """Create progress tracking tables with fixed foreign key constraints"""
    
    try:
        # Get database configuration
        config = get_config()
        db_config = config.database
        
        # Create async engine
        engine = create_async_engine(
            db_config.get_connection_url(async_driver=True),
            echo=db_config.echo_queries,
            connect_args=db_config.get_connect_args()
        )
        
        logger.info("Creating progress tracking tables with fixed constraints...")
        
        async with engine.begin() as conn:
            # First, check the users table character set and collation
            users_info = await conn.execute(text("""
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_SET_NAME,
                    COLLATION_NAME
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = :database_name 
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME = 'id'
            """), {"database_name": db_config.database})
            
            users_row = users_info.fetchone()
            if users_row:
                logger.info(f"Users.id column: {users_row.DATA_TYPE}, charset: {users_row.CHARACTER_SET_NAME}, collation: {users_row.COLLATION_NAME}")
            
            # Create practice_sessions table with matching character set
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS practice_sessions (
                    id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL PRIMARY KEY COMMENT 'Primary key UUID',
                    user_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ID of user who created this session',
                    story_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT 'ID of story used in this session (null for generated stories)',
                    session_type VARCHAR(50) NOT NULL DEFAULT 'individual' COMMENT 'Type of session: individual, collaborative, assessment',
                    session_name VARCHAR(255) NULL COMMENT 'Optional custom name for the session',
                    session_data JSON NULL COMMENT 'Module-specific session configuration and metadata',
                    story_content JSON NULL COMMENT 'Story content used in session (for generated stories)',
                    overall_score FLOAT NULL COMMENT 'Overall session score (0.0 to 1.0)',
                    sentences_completed INTEGER NOT NULL DEFAULT 0 COMMENT 'Number of sentences completed in session',
                    total_sentences INTEGER NULL COMMENT 'Total number of sentences in the story',
                    started_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'When the session was started',
                    completed_at DATETIME(6) NULL COMMENT 'When the session was completed (null if ongoing)',
                    duration_seconds INTEGER NULL COMMENT 'Total session duration in seconds',
                    performance_metrics JSON NULL COMMENT 'Detailed performance metrics and analytics',
                    status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'Session status: active, completed, paused, abandoned',
                    difficulty_level VARCHAR(20) NULL COMMENT 'Difficulty level: beginner, intermediate, advanced',
                    skill_areas JSON NULL COMMENT 'List of skill areas practiced in this session',
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Record creation timestamp',
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT 'Record last update timestamp',
                    
                    INDEX idx_practice_sessions_user_id (user_id),
                    INDEX idx_practice_sessions_user_created (user_id, created_at),
                    INDEX idx_practice_sessions_status_created (status, created_at),
                    INDEX idx_practice_sessions_type_difficulty (session_type, difficulty_level),
                    
                    CONSTRAINT check_overall_score_range CHECK (overall_score IS NULL OR (overall_score >= 0.0 AND overall_score <= 1.0)),
                    CONSTRAINT check_sentences_completed_positive CHECK (sentences_completed >= 0),
                    CONSTRAINT check_total_sentences_positive CHECK (total_sentences IS NULL OR total_sentences > 0),
                    CONSTRAINT check_duration_positive CHECK (duration_seconds IS NULL OR duration_seconds >= 0),
                    CONSTRAINT check_valid_status CHECK (status IN ('active', 'completed', 'paused', 'abandoned')),
                    CONSTRAINT check_valid_session_type CHECK (session_type IN ('individual', 'collaborative', 'assessment', 'practice')),
                    CONSTRAINT check_valid_difficulty CHECK (difficulty_level IS NULL OR difficulty_level IN ('beginner', 'intermediate', 'advanced')),
                    
                    CONSTRAINT fk_practice_sessions_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            logger.info("✅ Created practice_sessions table")
            
            # Create sentence_attempts table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sentence_attempts (
                    id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL PRIMARY KEY COMMENT 'Primary key UUID',
                    session_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ID of the practice session this attempt belongs to',
                    sentence_index INTEGER NOT NULL COMMENT 'Index of sentence within the story (0-based)',
                    target_sentence TEXT NOT NULL COMMENT 'The target sentence text being practiced',
                    landmark_data JSON NULL COMMENT 'MediaPipe landmark data captured during attempt',
                    gesture_sequence JSON NULL COMMENT 'Sequence of detected gestures and their timing',
                    confidence_score FLOAT NULL COMMENT 'AI confidence score for gesture recognition (0.0 to 1.0)',
                    accuracy_score FLOAT NULL COMMENT 'Accuracy score compared to target sentence (0.0 to 1.0)',
                    fluency_score FLOAT NULL COMMENT 'Fluency score based on gesture timing and smoothness (0.0 to 1.0)',
                    ai_feedback TEXT NULL COMMENT 'AI-generated feedback for the attempt',
                    suggestions JSON NULL COMMENT 'Specific suggestions for improvement',
                    detected_errors JSON NULL COMMENT 'List of detected errors and their types',
                    attempted_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'When this attempt was made',
                    duration_ms INTEGER NULL COMMENT 'Duration of the attempt in milliseconds',
                    attempt_number INTEGER NOT NULL DEFAULT 1 COMMENT 'Attempt number for this sentence (1-based)',
                    is_successful BOOLEAN NULL COMMENT 'Whether the attempt was considered successful',
                    video_start_frame INTEGER NULL COMMENT 'Starting frame number for this attempt',
                    video_end_frame INTEGER NULL COMMENT 'Ending frame number for this attempt',
                    
                    INDEX idx_sentence_attempts_session_id (session_id),
                    INDEX idx_sentence_attempts_session_sentence (session_id, sentence_index),
                    INDEX idx_sentence_attempts_session_attempt (session_id, attempt_number),
                    INDEX idx_sentence_attempts_attempted_at (attempted_at),
                    
                    CONSTRAINT check_confidence_score_range CHECK (confidence_score IS NULL OR (confidence_score >= 0.0 AND confidence_score <= 1.0)),
                    CONSTRAINT check_accuracy_score_range CHECK (accuracy_score IS NULL OR (accuracy_score >= 0.0 AND accuracy_score <= 1.0)),
                    CONSTRAINT check_fluency_score_range CHECK (fluency_score IS NULL OR (fluency_score >= 0.0 AND fluency_score <= 1.0)),
                    CONSTRAINT check_sentence_index_positive CHECK (sentence_index >= 0),
                    CONSTRAINT check_attempt_number_positive CHECK (attempt_number >= 1),
                    CONSTRAINT check_duration_positive CHECK (duration_ms IS NULL OR duration_ms > 0),
                    
                    CONSTRAINT fk_sentence_attempts_session_id FOREIGN KEY (session_id) REFERENCES practice_sessions(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            logger.info("✅ Created sentence_attempts table")
            
            # Create user_progress table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_progress (
                    id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL PRIMARY KEY COMMENT 'Primary key UUID',
                    user_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ID of the user this progress belongs to',
                    skill_area VARCHAR(100) NOT NULL COMMENT 'Skill area being tracked',
                    skill_category VARCHAR(50) NULL COMMENT 'Category of skill',
                    current_level FLOAT NOT NULL DEFAULT 0.0 COMMENT 'Current skill level (0.0 to 10.0)',
                    experience_points FLOAT NOT NULL DEFAULT 0.0 COMMENT 'Total experience points earned in this skill area',
                    total_practice_time INTEGER NOT NULL DEFAULT 0 COMMENT 'Total practice time in seconds',
                    total_sessions INTEGER NOT NULL DEFAULT 0 COMMENT 'Total number of practice sessions',
                    total_attempts INTEGER NOT NULL DEFAULT 0 COMMENT 'Total number of sentence attempts',
                    successful_attempts INTEGER NOT NULL DEFAULT 0 COMMENT 'Number of successful attempts',
                    average_score FLOAT NULL COMMENT 'Average performance score (0.0 to 1.0)',
                    average_confidence FLOAT NULL COMMENT 'Average confidence score (0.0 to 1.0)',
                    average_accuracy FLOAT NULL COMMENT 'Average accuracy score (0.0 to 1.0)',
                    average_fluency FLOAT NULL COMMENT 'Average fluency score (0.0 to 1.0)',
                    milestones JSON NULL COMMENT 'List of achieved milestones and their timestamps',
                    learning_streak INTEGER NOT NULL DEFAULT 0 COMMENT 'Current learning streak in days',
                    longest_streak INTEGER NOT NULL DEFAULT 0 COMMENT 'Longest learning streak achieved',
                    last_practice_date DATETIME(6) NULL COMMENT 'Date of last practice session',
                    current_difficulty VARCHAR(20) NOT NULL DEFAULT 'beginner' COMMENT 'Current difficulty level',
                    target_level FLOAT NULL COMMENT 'Target skill level to achieve',
                    weekly_goal_minutes INTEGER NULL COMMENT 'Weekly practice goal in minutes',
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT 'Record creation timestamp',
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT 'Record last update timestamp',
                    
                    UNIQUE INDEX idx_user_progress_user_skill (user_id, skill_area),
                    INDEX idx_user_progress_skill_level (skill_area, current_level),
                    INDEX idx_user_progress_last_practice (last_practice_date),
                    
                    CONSTRAINT check_current_level_range CHECK (current_level >= 0.0 AND current_level <= 10.0),
                    CONSTRAINT check_experience_points_positive CHECK (experience_points >= 0.0),
                    CONSTRAINT check_practice_time_positive CHECK (total_practice_time >= 0),
                    CONSTRAINT check_total_sessions_positive CHECK (total_sessions >= 0),
                    CONSTRAINT check_total_attempts_positive CHECK (total_attempts >= 0),
                    CONSTRAINT check_successful_attempts_positive CHECK (successful_attempts >= 0),
                    CONSTRAINT check_successful_attempts_valid CHECK (successful_attempts <= total_attempts),
                    CONSTRAINT check_average_score_range CHECK (average_score IS NULL OR (average_score >= 0.0 AND average_score <= 1.0)),
                    CONSTRAINT check_average_confidence_range CHECK (average_confidence IS NULL OR (average_confidence >= 0.0 AND average_confidence <= 1.0)),
                    CONSTRAINT check_average_accuracy_range CHECK (average_accuracy IS NULL OR (average_accuracy >= 0.0 AND average_accuracy <= 1.0)),
                    CONSTRAINT check_average_fluency_range CHECK (average_fluency IS NULL OR (average_fluency >= 0.0 AND average_fluency <= 1.0)),
                    CONSTRAINT check_learning_streak_positive CHECK (learning_streak >= 0),
                    CONSTRAINT check_longest_streak_positive CHECK (longest_streak >= 0),
                    CONSTRAINT check_longest_streak_valid CHECK (longest_streak >= learning_streak),
                    CONSTRAINT check_valid_difficulty CHECK (current_difficulty IN ('beginner', 'intermediate', 'advanced')),
                    CONSTRAINT check_target_level_range CHECK (target_level IS NULL OR (target_level >= 0.0 AND target_level <= 10.0)),
                    CONSTRAINT check_weekly_goal_positive CHECK (weekly_goal_minutes IS NULL OR weekly_goal_minutes > 0),
                    
                    CONSTRAINT fk_user_progress_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            logger.info("✅ Created user_progress table")
            
            logger.info("Successfully created all progress tracking tables:")
            logger.info("- practice_sessions")
            logger.info("- sentence_attempts")
            logger.info("- user_progress")
        
        # Close engine
        await engine.dispose()
        
        logger.info("Progress tracking schema migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create progress tracking tables: {e}")
        return False


async def verify_progress_tables():
    """Verify that all progress tables were created successfully"""
    
    try:
        # Get database configuration
        config = get_config()
        db_config = config.database
        
        # Create async engine
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
                AND table_name IN ('practice_sessions', 'sentence_attempts', 'user_progress')
                ORDER BY table_name
            """)
            
            result = await conn.execute(tables_query, {"database_name": db_config.database})
            tables = result.fetchall()
            
            expected_tables = {"practice_sessions", "sentence_attempts", "user_progress"}
            found_tables = {row[0] for row in tables}
            
            if found_tables == expected_tables:
                logger.info("✓ All progress tracking tables verified successfully")
                
                # Check foreign key constraints
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
                    AND TABLE_NAME IN ('practice_sessions', 'sentence_attempts', 'user_progress')
                    ORDER BY TABLE_NAME, COLUMN_NAME
                """)
                
                fk_result = await conn.execute(fk_query, {"database_name": db_config.database})
                foreign_keys = fk_result.fetchall()
                
                logger.info("✓ Foreign key constraints:")
                for fk in foreign_keys:
                    logger.info(f"   {fk.TABLE_NAME}.{fk.COLUMN_NAME} -> {fk.REFERENCED_TABLE_NAME}.{fk.REFERENCED_COLUMN_NAME}")
                
                return True
            else:
                missing_tables = expected_tables - found_tables
                logger.error(f"✗ Missing tables: {missing_tables}")
                return False
        
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"Failed to verify progress tables: {e}")
        return False


async def main():
    """Main function"""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🔧 Fixed Progress Tables Migration")
    print("=" * 50)
    
    # Create tables
    success = await create_progress_tables_fixed()
    
    if success:
        # Verify tables
        verified = await verify_progress_tables()
        
        if verified:
            print("\n✅ Progress tracking tables created and verified successfully!")
            return 0
        else:
            print("\n❌ Table verification failed!")
            return 1
    else:
        print("\n❌ Table creation failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)