#!/usr/bin/env python3
"""
Database migration script for Reconnect module tables
Creates all necessary tables for therapeutic movement analysis and pose tracking
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from config import get_config

logger = logging.getLogger(__name__)

# SQL statements for creating Reconnect tables
RECONNECT_TABLES = {
    "therapy_sessions": """
        CREATE TABLE IF NOT EXISTS therapy_sessions (
            id CHAR(36) PRIMARY KEY COMMENT 'Primary key UUID',
            user_id CHAR(36) NULL COMMENT 'Foreign key to users table (optional)',
            session_token VARCHAR(255) NOT NULL UNIQUE COMMENT 'Unique session identifier',
            exercise_type VARCHAR(100) NOT NULL COMMENT 'Type of therapeutic exercise',
            difficulty_level VARCHAR(20) NOT NULL DEFAULT 'beginner' COMMENT 'Difficulty level: beginner, intermediate, advanced',
            session_duration INT NULL COMMENT 'Session duration in milliseconds',
            status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'Session status: active, completed, abandoned',
            target_areas JSON NULL COMMENT 'List of target body areas for therapy',
            total_movements INT DEFAULT 0 COMMENT 'Total number of movement detections',
            average_quality FLOAT DEFAULT 0.0 COMMENT 'Average movement quality score (0.0-1.0)',
            session_score INT DEFAULT 0 COMMENT 'Overall session score (0-100)',
            rom_statistics JSON NULL COMMENT 'Range of motion statistics for each joint',
            session_metadata JSON NULL COMMENT 'Additional session metadata and settings',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update timestamp',
            
            INDEX idx_therapy_sessions_user_id (user_id),
            INDEX idx_therapy_sessions_session_token (session_token),
            INDEX idx_therapy_sessions_exercise_type (exercise_type),
            INDEX idx_therapy_sessions_status (status),
            INDEX idx_therapy_sessions_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
        COMMENT='Therapeutic movement sessions';
    """,
    
    "movement_analyses": """
        CREATE TABLE IF NOT EXISTS movement_analyses (
            id CHAR(36) PRIMARY KEY COMMENT 'Primary key UUID',
            session_id CHAR(36) NOT NULL COMMENT 'Foreign key to therapy_sessions table',
            quality_score FLOAT NOT NULL COMMENT 'Overall movement quality score (0.0-1.0)',
            smoothness_score FLOAT NULL COMMENT 'Movement smoothness score (0.0-1.0)',
            symmetry_score FLOAT NULL COMMENT 'Left-right symmetry score (0.0-1.0)',
            range_score FLOAT NULL COMMENT 'Range of motion score (0.0-1.0)',
            stability_score FLOAT NULL COMMENT 'Pose stability score (0.0-1.0)',
            processing_time_ms INT NULL COMMENT 'Processing time in milliseconds',
            frame_timestamp TIMESTAMP NULL COMMENT 'Timestamp when frame was captured',
            analysis_metadata JSON NULL COMMENT 'Additional analysis metadata and detailed scores',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update timestamp',
            
            INDEX idx_movement_analyses_session_id (session_id),
            INDEX idx_movement_analyses_quality_score (quality_score),
            INDEX idx_movement_analyses_frame_timestamp (frame_timestamp),
            INDEX idx_movement_analyses_created_at (created_at),
            
            FOREIGN KEY (session_id) REFERENCES therapy_sessions(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
        COMMENT='Individual movement analysis results';
    """,
    
    "pose_landmarks": """
        CREATE TABLE IF NOT EXISTS pose_landmarks (
            id CHAR(36) PRIMARY KEY COMMENT 'Primary key UUID',
            session_id CHAR(36) NOT NULL COMMENT 'Foreign key to therapy_sessions table',
            analysis_id CHAR(36) NULL COMMENT 'Foreign key to movement_analyses table (optional)',
            landmarks_data JSON NOT NULL COMMENT 'MediaPipe pose landmarks data',
            num_landmarks INT NULL COMMENT 'Number of detected landmarks',
            pose_confidence FLOAT NULL COMMENT 'Pose detection confidence score',
            frame_width INT NULL COMMENT 'Original frame width in pixels',
            frame_height INT NULL COMMENT 'Original frame height in pixels',
            joint_angles JSON NULL COMMENT 'Calculated joint angles in degrees',
            range_of_motion JSON NULL COMMENT 'Range of motion measurements for each joint',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update timestamp',
            
            INDEX idx_pose_landmarks_session_id (session_id),
            INDEX idx_pose_landmarks_analysis_id (analysis_id),
            INDEX idx_pose_landmarks_pose_confidence (pose_confidence),
            INDEX idx_pose_landmarks_created_at (created_at),
            
            FOREIGN KEY (session_id) REFERENCES therapy_sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (analysis_id) REFERENCES movement_analyses(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
        COMMENT='Pose landmark data from MediaPipe';
    """,
    
    "therapy_progress": """
        CREATE TABLE IF NOT EXISTS therapy_progress (
            id CHAR(36) PRIMARY KEY COMMENT 'Primary key UUID',
            user_id CHAR(36) NOT NULL COMMENT 'Foreign key to users table',
            exercise_type VARCHAR(100) NOT NULL COMMENT 'Exercise type being tracked',
            body_area VARCHAR(50) NULL COMMENT 'Primary body area being treated',
            total_sessions INT DEFAULT 0 COMMENT 'Total number of therapy sessions',
            total_therapy_time INT DEFAULT 0 COMMENT 'Total therapy time in milliseconds',
            best_quality_score FLOAT DEFAULT 0.0 COMMENT 'Best quality score achieved (0.0-1.0)',
            average_quality_score FLOAT DEFAULT 0.0 COMMENT 'Average quality score across all sessions',
            initial_rom JSON NULL COMMENT 'Initial range of motion measurements',
            current_rom JSON NULL COMMENT 'Current range of motion measurements',
            best_rom JSON NULL COMMENT 'Best range of motion achieved',
            functional_level VARCHAR(20) DEFAULT 'limited' COMMENT 'Current functional level: limited, fair, good, excellent',
            improvement_percentage FLOAT DEFAULT 0.0 COMMENT 'Overall improvement percentage (0-100)',
            last_session_id CHAR(36) NULL COMMENT 'ID of the most recent session',
            last_session_score INT NULL COMMENT 'Score from the most recent session',
            last_practiced_at TIMESTAMP NULL COMMENT 'Timestamp of last therapy session',
            progress_metadata JSON NULL COMMENT 'Additional progress tracking metadata',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update timestamp',
            
            INDEX idx_therapy_progress_user_id (user_id),
            INDEX idx_therapy_progress_exercise_type (exercise_type),
            INDEX idx_therapy_progress_body_area (body_area),
            INDEX idx_therapy_progress_functional_level (functional_level),
            INDEX idx_therapy_progress_last_practiced_at (last_practiced_at),
            
            UNIQUE KEY unique_user_exercise (user_id, exercise_type)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
        COMMENT='User progress in therapeutic exercises over time';
    """,
    
    "exercise_goals": """
        CREATE TABLE IF NOT EXISTS exercise_goals (
            id CHAR(36) PRIMARY KEY COMMENT 'Primary key UUID',
            name VARCHAR(100) NOT NULL COMMENT 'Goal name',
            description TEXT NULL COMMENT 'Goal description',
            goal_type VARCHAR(50) NOT NULL COMMENT 'Type of goal: range_of_motion, quality, consistency, endurance',
            exercise_type VARCHAR(100) NULL COMMENT 'Target exercise type (null for general goals)',
            body_area VARCHAR(50) NULL COMMENT 'Target body area',
            target_rom FLOAT NULL COMMENT 'Target range of motion in degrees',
            target_quality FLOAT NULL COMMENT 'Target quality score (0.0-1.0)',
            target_sessions INT NULL COMMENT 'Target number of sessions',
            target_duration INT NULL COMMENT 'Target session duration in milliseconds',
            time_frame_days INT NULL COMMENT 'Time frame to achieve goal in days',
            difficulty_level VARCHAR(20) DEFAULT 'moderate' COMMENT 'Goal difficulty: easy, moderate, challenging, expert',
            points_reward INT DEFAULT 0 COMMENT 'Points awarded for completion',
            badge_icon VARCHAR(100) NULL COMMENT 'Icon or emoji for goal badge',
            is_active BOOLEAN DEFAULT TRUE COMMENT 'Whether goal is currently active',
            goal_metadata JSON NULL COMMENT 'Additional goal configuration',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update timestamp',
            
            INDEX idx_exercise_goals_goal_type (goal_type),
            INDEX idx_exercise_goals_exercise_type (exercise_type),
            INDEX idx_exercise_goals_body_area (body_area),
            INDEX idx_exercise_goals_difficulty_level (difficulty_level),
            INDEX idx_exercise_goals_is_active (is_active)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
        COMMENT='Therapeutic exercise goals and milestones';
    """,
    
    "user_goal_progress": """
        CREATE TABLE IF NOT EXISTS user_goal_progress (
            id CHAR(36) PRIMARY KEY COMMENT 'Primary key UUID',
            user_id CHAR(36) NOT NULL COMMENT 'Foreign key to users table',
            goal_id CHAR(36) NOT NULL COMMENT 'Foreign key to exercise_goals table',
            status VARCHAR(20) DEFAULT 'in_progress' COMMENT 'Goal status: in_progress, completed, paused, abandoned',
            progress_percentage FLOAT DEFAULT 0.0 COMMENT 'Progress percentage (0-100)',
            sessions_completed INT DEFAULT 0 COMMENT 'Number of sessions completed toward goal',
            current_rom FLOAT NULL COMMENT 'Current range of motion achievement',
            current_quality FLOAT NULL COMMENT 'Current quality score achievement',
            milestones_achieved JSON NULL COMMENT 'List of achieved milestones',
            completed_at TIMESTAMP NULL COMMENT 'Timestamp when goal was completed',
            completion_time_days INT NULL COMMENT 'Days taken to complete goal',
            progress_data JSON NULL COMMENT 'Detailed progress data and statistics',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update timestamp',
            
            INDEX idx_user_goal_progress_user_id (user_id),
            INDEX idx_user_goal_progress_goal_id (goal_id),
            INDEX idx_user_goal_progress_status (status),
            INDEX idx_user_goal_progress_progress_percentage (progress_percentage),
            INDEX idx_user_goal_progress_completed_at (completed_at),
            
            UNIQUE KEY unique_user_goal (user_id, goal_id),
            FOREIGN KEY (goal_id) REFERENCES exercise_goals(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
        COMMENT='User progress on therapeutic exercise goals';
    """,
    
    "joint_measurements": """
        CREATE TABLE IF NOT EXISTS joint_measurements (
            id CHAR(36) PRIMARY KEY COMMENT 'Primary key UUID',
            session_id CHAR(36) NOT NULL COMMENT 'Foreign key to therapy_sessions table',
            user_id CHAR(36) NOT NULL COMMENT 'Foreign key to users table',
            joint_name VARCHAR(50) NOT NULL COMMENT 'Name of the joint (e.g., left_shoulder, right_knee)',
            measurement_type VARCHAR(50) NOT NULL COMMENT 'Type of measurement: flexion, extension, abduction, rotation',
            angle_degrees FLOAT NOT NULL COMMENT 'Joint angle measurement in degrees',
            range_of_motion FLOAT NULL COMMENT 'Range of motion for this measurement session',
            measurement_quality FLOAT NULL COMMENT 'Quality/confidence of the measurement (0.0-1.0)',
            exercise_phase VARCHAR(50) NULL COMMENT 'Phase of exercise: starting, peak, ending',
            repetition_number INT NULL COMMENT 'Repetition number within the session',
            measurement_metadata JSON NULL COMMENT 'Additional measurement metadata',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update timestamp',
            
            INDEX idx_joint_measurements_session_id (session_id),
            INDEX idx_joint_measurements_user_id (user_id),
            INDEX idx_joint_measurements_joint_name (joint_name),
            INDEX idx_joint_measurements_measurement_type (measurement_type),
            INDEX idx_joint_measurements_angle_degrees (angle_degrees),
            INDEX idx_joint_measurements_created_at (created_at),
            
            FOREIGN KEY (session_id) REFERENCES therapy_sessions(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
        COMMENT='Detailed joint measurement data over time';
    """
}

# Default exercise goals to insert
DEFAULT_EXERCISE_GOALS = [
    {
        "id": "goal_shoulder_flexibility",
        "name": "Shoulder Flexibility Improvement",
        "description": "Improve shoulder range of motion through consistent practice",
        "goal_type": "range_of_motion",
        "exercise_type": "shoulder_flexion",
        "body_area": "shoulders",
        "target_rom": 150.0,
        "target_quality": None,
        "target_sessions": 20,
        "target_duration": None,
        "time_frame_days": 30,
        "difficulty_level": "moderate",
        "points_reward": 100,
        "badge_icon": "🤲",
        "goal_metadata": {
            "milestones": [
                {"rom": 90, "description": "Basic mobility restored"},
                {"rom": 120, "description": "Good progress achieved"},
                {"rom": 150, "description": "Full flexibility goal reached"}
            ]
        }
    },
    {
        "id": "goal_movement_quality",
        "name": "Movement Quality Master",
        "description": "Achieve consistent high-quality movement patterns",
        "goal_type": "quality",
        "exercise_type": None,
        "body_area": None,
        "target_rom": None,
        "target_quality": 0.8,
        "target_sessions": 15,
        "target_duration": None,
        "time_frame_days": 21,
        "difficulty_level": "challenging",
        "points_reward": 150,
        "badge_icon": "⭐",
        "goal_metadata": {
            "milestones": [
                {"quality": 0.6, "description": "Good form developing"},
                {"quality": 0.7, "description": "Consistent technique"},
                {"quality": 0.8, "description": "Master level achieved"}
            ]
        }
    },
    {
        "id": "goal_balance_training",
        "name": "Balance and Stability Champion",
        "description": "Master balance exercises for fall prevention",
        "goal_type": "consistency",
        "exercise_type": "balance_training",
        "body_area": "full_body",
        "target_rom": None,
        "target_quality": 0.75,
        "target_sessions": 25,
        "target_duration": None,
        "time_frame_days": 45,
        "difficulty_level": "expert",
        "points_reward": 200,
        "badge_icon": "⚖️",
        "goal_metadata": {
            "milestones": [
                {"sessions": 5, "description": "Balance basics learned"},
                {"sessions": 15, "description": "Stability improving"},
                {"sessions": 25, "description": "Balance champion achieved"}
            ]
        }
    }
]


async def create_reconnect_tables():
    """Create all Reconnect module tables"""
    logger.info("Creating Reconnect module tables...")
    
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
        
        async with engine.begin() as conn:
            # Create tables in order (respecting foreign key dependencies)
            table_order = [
                "therapy_sessions",
                "movement_analyses", 
                "pose_landmarks",
                "therapy_progress",
                "exercise_goals",
                "user_goal_progress",
                "joint_measurements"
            ]
            
            for table_name in table_order:
                if table_name in RECONNECT_TABLES:
                    logger.info(f"Creating table: {table_name}")
                    
                    # Execute table creation
                    await conn.execute(text(RECONNECT_TABLES[table_name]))
                    
                    logger.info(f"✅ Table {table_name} created successfully")
                else:
                    logger.warning(f"Table definition not found: {table_name}")
        
        await engine.dispose()
        
        logger.info("✅ All Reconnect tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating Reconnect tables: {e}")
        raise


async def insert_default_exercise_goals():
    """Insert default exercise goals"""
    logger.info("Inserting default exercise goals...")
    
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
        
        async with engine.begin() as conn:
            for goal_data in DEFAULT_EXERCISE_GOALS:
                # Check if goal already exists
                result = await conn.execute(text(
                    "SELECT id FROM exercise_goals WHERE id = :goal_id"
                ), {"goal_id": goal_data["id"]})
                existing_goal = result.fetchone()
                
                if existing_goal:
                    logger.info(f"Goal {goal_data['id']} already exists, skipping...")
                    continue
                
                # Insert goal
                insert_query = text("""
                    INSERT INTO exercise_goals (
                        id, name, description, goal_type, exercise_type, body_area,
                        target_rom, target_quality, target_sessions, target_duration,
                        time_frame_days, difficulty_level, points_reward, badge_icon,
                        is_active, goal_metadata, created_at, updated_at
                    ) VALUES (
                        :id, :name, :description, :goal_type, :exercise_type, :body_area,
                        :target_rom, :target_quality, :target_sessions, :target_duration,
                        :time_frame_days, :difficulty_level, :points_reward, :badge_icon,
                        :is_active, :goal_metadata, :created_at, :updated_at
                    )
                """)
                
                import json
                await conn.execute(insert_query, {
                    "id": goal_data["id"],
                    "name": goal_data["name"],
                    "description": goal_data["description"],
                    "goal_type": goal_data["goal_type"],
                    "exercise_type": goal_data["exercise_type"],
                    "body_area": goal_data["body_area"],
                    "target_rom": goal_data["target_rom"],
                    "target_quality": goal_data["target_quality"],
                    "target_sessions": goal_data["target_sessions"],
                    "target_duration": goal_data.get("target_duration"),
                    "time_frame_days": goal_data["time_frame_days"],
                    "difficulty_level": goal_data["difficulty_level"],
                    "points_reward": goal_data["points_reward"],
                    "badge_icon": goal_data["badge_icon"],
                    "is_active": True,
                    "goal_metadata": json.dumps(goal_data["goal_metadata"]),
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
                
                logger.info(f"✅ Inserted goal: {goal_data['name']}")
        
        await engine.dispose()
        
        logger.info("✅ Default exercise goals inserted successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error inserting default goals: {e}")
        raise


async def verify_reconnect_tables():
    """Verify that all Reconnect tables were created correctly"""
    logger.info("Verifying Reconnect tables...")
    
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
        
        async with engine.begin() as conn:
            # Check each table exists and has expected structure
            for table_name in RECONNECT_TABLES.keys():
                # Check table exists
                result = await conn.execute(text(
                    "SELECT COUNT(*) as count FROM information_schema.tables WHERE table_name = :table_name"
                ), {"table_name": table_name})
                table_check = result.fetchone()
                
                if not table_check or table_check[0] == 0:
                    logger.error(f"❌ Table {table_name} was not created")
                    await engine.dispose()
                    return False
                
                # Check table structure
                result = await conn.execute(text(
                    "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = :table_name"
                ), {"table_name": table_name})
                columns = result.fetchall()
                
                logger.info(f"✅ Table {table_name} verified ({len(columns)} columns)")
            
            # Check default goals were inserted
            result = await conn.execute(text("SELECT COUNT(*) as count FROM exercise_goals"))
            goals_count = result.fetchone()
            
            logger.info(f"✅ Exercise goals table has {goals_count[0]} records")
        
        await engine.dispose()
        
        logger.info("✅ All Reconnect tables verified successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verifying Reconnect tables: {e}")
        return False


async def drop_reconnect_tables():
    """Drop all Reconnect tables (for cleanup/testing)"""
    logger.warning("Dropping Reconnect tables...")
    
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
        
        async with engine.begin() as conn:
            # Drop tables in reverse order (respecting foreign key dependencies)
            drop_order = [
                "joint_measurements",
                "user_goal_progress",
                "exercise_goals", 
                "therapy_progress",
                "pose_landmarks",
                "movement_analyses",
                "therapy_sessions"
            ]
            
            for table_name in drop_order:
                try:
                    await conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
                    logger.info(f"✅ Dropped table: {table_name}")
                except Exception as e:
                    logger.warning(f"⚠️ Could not drop table {table_name}: {e}")
        
        await engine.dispose()
        
        logger.info("✅ Reconnect tables dropped")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error dropping Reconnect tables: {e}")
        return False


async def main():
    """Main migration function"""
    logger.info("🎯 Starting Reconnect Database Migration")
    logger.info("=" * 50)
    
    try:
        # Create tables
        await create_reconnect_tables()
        
        # Insert default data
        await insert_default_exercise_goals()
        
        # Verify everything was created correctly
        success = await verify_reconnect_tables()
        
        if success:
            logger.info("🎉 Reconnect database migration completed successfully!")
        else:
            logger.error("❌ Reconnect database migration failed verification")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Reconnect database migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run migration
    asyncio.run(main())