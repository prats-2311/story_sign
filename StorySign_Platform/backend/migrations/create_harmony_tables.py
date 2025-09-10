"""
Database migration for Harmony module tables
Creates emotion_sessions, emotion_detections, facial_landmarks, emotion_progress, 
emotion_challenges, and user_challenge_progress tables
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


async def create_harmony_tables():
    """Create all Harmony module tables"""
    
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
        
        logger.info("Creating Harmony module tables...")
        
        async with engine.begin() as conn:
            # Create emotion_sessions table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS emotion_sessions (
                    id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36),
                    session_token VARCHAR(255) NOT NULL UNIQUE,
                    target_emotion VARCHAR(50) NOT NULL,
                    difficulty_level VARCHAR(20) NOT NULL DEFAULT 'normal',
                    session_duration INT,
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    total_detections INT NOT NULL DEFAULT 0,
                    target_matches INT NOT NULL DEFAULT 0,
                    average_confidence FLOAT NOT NULL DEFAULT 0.0,
                    session_score INT NOT NULL DEFAULT 0,
                    session_metadata JSON,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    INDEX idx_emotion_sessions_user_id (user_id),
                    INDEX idx_emotion_sessions_token (session_token),
                    INDEX idx_emotion_sessions_target_emotion (target_emotion),
                    INDEX idx_emotion_sessions_status (status),
                    INDEX idx_emotion_sessions_created_at (created_at),
                    
                    CONSTRAINT check_difficulty_level CHECK (difficulty_level IN ('easy', 'normal', 'hard')),
                    CONSTRAINT check_session_status CHECK (status IN ('active', 'completed', 'abandoned')),
                    CONSTRAINT check_valid_emotion CHECK (target_emotion IN ('happy', 'sad', 'surprised', 'angry', 'fearful', 'disgusted', 'neutral')),
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # Create emotion_detections table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS emotion_detections (
                    id CHAR(36) PRIMARY KEY,
                    session_id CHAR(36) NOT NULL,
                    detected_emotion VARCHAR(50) NOT NULL,
                    confidence_score FLOAT NOT NULL,
                    is_target_match BOOLEAN NOT NULL DEFAULT FALSE,
                    processing_time_ms INT,
                    frame_timestamp DATETIME(6),
                    detection_metadata JSON,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    INDEX idx_emotion_detections_session_id (session_id),
                    INDEX idx_emotion_detections_emotion (detected_emotion),
                    INDEX idx_emotion_detections_confidence (confidence_score),
                    INDEX idx_emotion_detections_target_match (is_target_match),
                    INDEX idx_emotion_detections_timestamp (frame_timestamp),
                    
                    CONSTRAINT check_confidence_range CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
                    CONSTRAINT check_valid_detected_emotion CHECK (detected_emotion IN ('happy', 'sad', 'surprised', 'angry', 'fearful', 'disgusted', 'neutral')),
                    
                    FOREIGN KEY (session_id) REFERENCES emotion_sessions(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # Create facial_landmarks table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS facial_landmarks (
                    id CHAR(36) PRIMARY KEY,
                    session_id CHAR(36) NOT NULL,
                    detection_id CHAR(36),
                    landmarks_data JSON NOT NULL,
                    num_landmarks INT,
                    face_confidence FLOAT,
                    frame_width INT,
                    frame_height INT,
                    extracted_features JSON,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    INDEX idx_facial_landmarks_session_id (session_id),
                    INDEX idx_facial_landmarks_detection_id (detection_id),
                    INDEX idx_facial_landmarks_num_landmarks (num_landmarks),
                    INDEX idx_facial_landmarks_confidence (face_confidence),
                    
                    FOREIGN KEY (session_id) REFERENCES emotion_sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (detection_id) REFERENCES emotion_detections(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # Create emotion_progress table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS emotion_progress (
                    id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36) NOT NULL,
                    emotion VARCHAR(50) NOT NULL,
                    total_sessions INT NOT NULL DEFAULT 0,
                    total_practice_time INT NOT NULL DEFAULT 0,
                    best_accuracy FLOAT NOT NULL DEFAULT 0.0,
                    average_accuracy FLOAT NOT NULL DEFAULT 0.0,
                    best_confidence FLOAT NOT NULL DEFAULT 0.0,
                    average_confidence FLOAT NOT NULL DEFAULT 0.0,
                    skill_level VARCHAR(20) NOT NULL DEFAULT 'beginner',
                    mastery_percentage FLOAT NOT NULL DEFAULT 0.0,
                    last_session_id CHAR(36),
                    last_session_score INT,
                    last_practiced_at DATETIME(6),
                    progress_metadata JSON,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    UNIQUE KEY unique_user_emotion (user_id, emotion),
                    INDEX idx_emotion_progress_user_id (user_id),
                    INDEX idx_emotion_progress_emotion (emotion),
                    INDEX idx_emotion_progress_skill_level (skill_level),
                    INDEX idx_emotion_progress_mastery (mastery_percentage),
                    INDEX idx_emotion_progress_last_practiced (last_practiced_at),
                    
                    CONSTRAINT check_skill_level CHECK (skill_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
                    CONSTRAINT check_valid_progress_emotion CHECK (emotion IN ('happy', 'sad', 'surprised', 'angry', 'fearful', 'disgusted', 'neutral')),
                    CONSTRAINT check_accuracy_range CHECK (best_accuracy >= 0.0 AND best_accuracy <= 100.0),
                    CONSTRAINT check_avg_accuracy_range CHECK (average_accuracy >= 0.0 AND average_accuracy <= 100.0),
                    CONSTRAINT check_confidence_range_progress CHECK (best_confidence >= 0.0 AND best_confidence <= 1.0),
                    CONSTRAINT check_avg_confidence_range CHECK (average_confidence >= 0.0 AND average_confidence <= 1.0),
                    CONSTRAINT check_mastery_range CHECK (mastery_percentage >= 0.0 AND mastery_percentage <= 100.0),
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # Create emotion_challenges table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS emotion_challenges (
                    id CHAR(36) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    challenge_type VARCHAR(50) NOT NULL,
                    target_emotion VARCHAR(50),
                    required_sessions INT NOT NULL DEFAULT 1,
                    required_accuracy FLOAT,
                    required_confidence FLOAT,
                    time_limit INT,
                    difficulty_level VARCHAR(20) NOT NULL DEFAULT 'normal',
                    points_reward INT NOT NULL DEFAULT 0,
                    badge_icon VARCHAR(100),
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    challenge_metadata JSON,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    INDEX idx_emotion_challenges_type (challenge_type),
                    INDEX idx_emotion_challenges_target_emotion (target_emotion),
                    INDEX idx_emotion_challenges_difficulty (difficulty_level),
                    INDEX idx_emotion_challenges_active (is_active),
                    INDEX idx_emotion_challenges_points (points_reward),
                    
                    CONSTRAINT check_challenge_difficulty CHECK (difficulty_level IN ('easy', 'normal', 'hard', 'expert')),
                    CONSTRAINT check_challenge_type CHECK (challenge_type IN ('accuracy', 'consistency', 'speed', 'endurance', 'multi_emotion')),
                    CONSTRAINT check_challenge_target_emotion CHECK (target_emotion IS NULL OR target_emotion IN ('happy', 'sad', 'surprised', 'angry', 'fearful', 'disgusted', 'neutral'))
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # Create user_challenge_progress table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_challenge_progress (
                    id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36) NOT NULL,
                    challenge_id CHAR(36) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
                    progress_percentage FLOAT NOT NULL DEFAULT 0.0,
                    sessions_completed INT NOT NULL DEFAULT 0,
                    best_score INT NOT NULL DEFAULT 0,
                    completed_at DATETIME(6),
                    completion_time INT,
                    progress_data JSON,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    UNIQUE KEY unique_user_challenge (user_id, challenge_id),
                    INDEX idx_user_challenge_progress_user_id (user_id),
                    INDEX idx_user_challenge_progress_challenge_id (challenge_id),
                    INDEX idx_user_challenge_progress_status (status),
                    INDEX idx_user_challenge_progress_completed (completed_at),
                    INDEX idx_user_challenge_progress_percentage (progress_percentage),
                    
                    CONSTRAINT check_progress_status CHECK (status IN ('in_progress', 'completed', 'failed')),
                    CONSTRAINT check_progress_percentage_range CHECK (progress_percentage >= 0.0 AND progress_percentage <= 100.0),
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (challenge_id) REFERENCES emotion_challenges(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            logger.info("Successfully created Harmony module tables:")
            logger.info("- emotion_sessions")
            logger.info("- emotion_detections")
            logger.info("- facial_landmarks")
            logger.info("- emotion_progress")
            logger.info("- emotion_challenges")
            logger.info("- user_challenge_progress")
        
        # Close engine
        await engine.dispose()
        
        logger.info("Harmony module schema migration completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to create Harmony module tables: {e}")
        raise


async def drop_harmony_tables():
    """Drop all Harmony module tables (for rollback)"""
    
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
        
        logger.warning("Dropping Harmony module tables...")
        
        async with engine.begin() as conn:
            # Drop tables in reverse dependency order
            tables = [
                "user_challenge_progress",
                "emotion_challenges", 
                "emotion_progress",
                "facial_landmarks",
                "emotion_detections",
                "emotion_sessions"
            ]
            
            for table in tables:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                logger.warning(f"Dropped table: {table}")
        
        # Close engine
        await engine.dispose()
        
        logger.warning("All Harmony module tables dropped")
        
    except Exception as e:
        logger.error(f"Failed to drop Harmony module tables: {e}")
        raise


async def verify_harmony_tables():
    """Verify that all Harmony tables were created successfully"""
    
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
                AND table_name IN (
                    'emotion_sessions', 'emotion_detections', 'facial_landmarks',
                    'emotion_progress', 'emotion_challenges', 'user_challenge_progress'
                )
                ORDER BY table_name
            """)
            
            result = await conn.execute(tables_query, {"database_name": db_config.database})
            tables = result.fetchall()
            
            expected_tables = {
                "emotion_sessions", "emotion_detections", "facial_landmarks",
                "emotion_progress", "emotion_challenges", "user_challenge_progress"
            }
            found_tables = {row[0] for row in tables}
            
            if found_tables == expected_tables:
                logger.info("✓ All Harmony module tables verified successfully")
                
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
        logger.error(f"Failed to verify Harmony tables: {e}")
        return False


async def insert_default_challenges():
    """Insert default emotion challenges"""
    
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
        
        logger.info("Inserting default emotion challenges...")
        
        async with engine.begin() as conn:
            # Check if challenges already exist
            count_query = text("SELECT COUNT(*) FROM emotion_challenges")
            result = await conn.execute(count_query)
            count = result.scalar()
            
            if count > 0:
                logger.info("Default challenges already exist, skipping insertion")
                return
            
            # Insert default challenges
            challenges = [
                {
                    "id": "happy-master-001",
                    "name": "Happy Master",
                    "description": "Master the art of expressing happiness with 90% accuracy",
                    "challenge_type": "accuracy",
                    "target_emotion": "happy",
                    "required_sessions": 5,
                    "required_accuracy": 90.0,
                    "required_confidence": 0.8,
                    "difficulty_level": "normal",
                    "points_reward": 100,
                    "badge_icon": "😊"
                },
                {
                    "id": "emotion-explorer-001",
                    "name": "Emotion Explorer",
                    "description": "Practice all 7 basic emotions in a single session",
                    "challenge_type": "multi_emotion",
                    "target_emotion": None,
                    "required_sessions": 1,
                    "required_accuracy": 70.0,
                    "required_confidence": 0.7,
                    "difficulty_level": "hard",
                    "points_reward": 200,
                    "badge_icon": "🎭"
                },
                {
                    "id": "consistency-champion-001",
                    "name": "Consistency Champion",
                    "description": "Maintain 80% accuracy across 10 consecutive sessions",
                    "challenge_type": "consistency",
                    "target_emotion": None,
                    "required_sessions": 10,
                    "required_accuracy": 80.0,
                    "required_confidence": 0.75,
                    "difficulty_level": "expert",
                    "points_reward": 300,
                    "badge_icon": "🏆"
                },
                {
                    "id": "speed-demon-001",
                    "name": "Speed Demon",
                    "description": "Complete a practice session in under 30 seconds with 75% accuracy",
                    "challenge_type": "speed",
                    "target_emotion": None,
                    "required_sessions": 1,
                    "required_accuracy": 75.0,
                    "required_confidence": 0.7,
                    "time_limit": 30000,  # 30 seconds in milliseconds
                    "difficulty_level": "hard",
                    "points_reward": 150,
                    "badge_icon": "⚡"
                }
            ]
            
            for challenge in challenges:
                insert_query = text("""
                    INSERT INTO emotion_challenges (
                        id, name, description, challenge_type, target_emotion,
                        required_sessions, required_accuracy, required_confidence,
                        time_limit, difficulty_level, points_reward, badge_icon,
                        is_active, challenge_metadata
                    ) VALUES (
                        :id, :name, :description, :challenge_type, :target_emotion,
                        :required_sessions, :required_accuracy, :required_confidence,
                        :time_limit, :difficulty_level, :points_reward, :badge_icon,
                        TRUE, '{}'
                    )
                """)
                
                await conn.execute(insert_query, challenge)
                logger.info(f"Inserted challenge: {challenge['name']}")
        
        await engine.dispose()
        logger.info("Default challenges inserted successfully")
        
    except Exception as e:
        logger.error(f"Failed to insert default challenges: {e}")
        raise


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
                await create_harmony_tables()
                await insert_default_challenges()
            elif command == "drop":
                await drop_harmony_tables()
            elif command == "verify":
                success = await verify_harmony_tables()
                sys.exit(0 if success else 1)
            elif command == "challenges":
                await insert_default_challenges()
            else:
                print("Usage: python create_harmony_tables.py [create|drop|verify|challenges]")
                sys.exit(1)
        else:
            # Default: create tables and insert challenges
            await create_harmony_tables()
            await verify_harmony_tables()
            await insert_default_challenges()
    
    asyncio.run(main())


# Migration metadata
MIGRATION_NAME = "create_harmony_tables"
MIGRATION_VERSION = "002"
MIGRATION_DESCRIPTION = "Create tables for Harmony facial expression practice module"