"""
Database migration for social learning features
Creates friendships, community_feedback, community_ratings, progress_shares, and social_interactions tables
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


async def create_social_tables():
    """Create all social learning tables"""
    
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
        
        logger.info("Creating social learning tables...")
        
        async with engine.begin() as conn:
            # Create friendships table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS friendships (
                    id CHAR(36) PRIMARY KEY,
                    requester_id CHAR(36) NOT NULL,
                    addressee_id CHAR(36) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'pending',
                    requested_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    responded_at DATETIME(6),
                    allow_progress_sharing BOOLEAN NOT NULL DEFAULT TRUE,
                    allow_session_invites BOOLEAN NOT NULL DEFAULT TRUE,
                    allow_feedback BOOLEAN NOT NULL DEFAULT TRUE,
                    last_interaction DATETIME(6),
                    interaction_count INT NOT NULL DEFAULT 0,
                    requester_notes TEXT,
                    addressee_notes TEXT,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    UNIQUE KEY uq_friendship_pair (requester_id, addressee_id),
                    INDEX idx_friendships_requester_status (requester_id, status),
                    INDEX idx_friendships_addressee_status (addressee_id, status),
                    INDEX idx_friendships_status (status),
                    INDEX idx_friendships_requested_at (requested_at),
                    
                    CONSTRAINT check_no_self_friendship CHECK (requester_id != addressee_id),
                    CONSTRAINT check_valid_friendship_status CHECK (status IN ('pending', 'accepted', 'blocked', 'declined')),
                    CONSTRAINT check_interaction_count_positive CHECK (interaction_count >= 0),
                    
                    FOREIGN KEY (requester_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (addressee_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # Create community_feedback table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS community_feedback (
                    id CHAR(36) PRIMARY KEY,
                    giver_id CHAR(36) NOT NULL,
                    receiver_id CHAR(36) NOT NULL,
                    session_id CHAR(36),
                    story_id CHAR(36),
                    sentence_index INT,
                    feedback_type VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    is_public BOOLEAN NOT NULL DEFAULT FALSE,
                    is_anonymous BOOLEAN NOT NULL DEFAULT FALSE,
                    helpfulness_score FLOAT,
                    helpfulness_votes INT NOT NULL DEFAULT 0,
                    is_flagged BOOLEAN NOT NULL DEFAULT FALSE,
                    is_moderated BOOLEAN NOT NULL DEFAULT FALSE,
                    moderated_by CHAR(36),
                    moderated_at DATETIME(6),
                    response_to CHAR(36),
                    response_count INT NOT NULL DEFAULT 0,
                    tags JSON,
                    skill_areas JSON,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    INDEX idx_community_feedback_giver_type (giver_id, feedback_type),
                    INDEX idx_community_feedback_receiver_session (receiver_id, session_id),
                    INDEX idx_community_feedback_session (session_id),
                    INDEX idx_community_feedback_story (story_id),
                    INDEX idx_community_feedback_public (is_public),
                    INDEX idx_community_feedback_flagged (is_flagged),
                    INDEX idx_community_feedback_response_to (response_to),
                    
                    CONSTRAINT check_no_self_feedback CHECK (giver_id != receiver_id),
                    CONSTRAINT check_valid_feedback_type CHECK (feedback_type IN ('encouragement', 'suggestion', 'correction', 'question', 'praise')),
                    CONSTRAINT check_helpfulness_score_range CHECK (helpfulness_score IS NULL OR (helpfulness_score >= 0 AND helpfulness_score <= 5)),
                    CONSTRAINT check_helpfulness_votes_positive CHECK (helpfulness_votes >= 0),
                    CONSTRAINT check_response_count_positive CHECK (response_count >= 0),
                    
                    FOREIGN KEY (giver_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES practice_sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (moderated_by) REFERENCES users(id),
                    FOREIGN KEY (response_to) REFERENCES community_feedback(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # Create community_ratings table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS community_ratings (
                    id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36) NOT NULL,
                    rating_type VARCHAR(20) NOT NULL,
                    target_id CHAR(36) NOT NULL,
                    rating_value FLOAT NOT NULL,
                    review_text TEXT,
                    difficulty_rating FLOAT,
                    clarity_rating FLOAT,
                    engagement_rating FLOAT,
                    educational_value_rating FLOAT,
                    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
                    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
                    helpful_votes INT NOT NULL DEFAULT 0,
                    unhelpful_votes INT NOT NULL DEFAULT 0,
                    is_flagged BOOLEAN NOT NULL DEFAULT FALSE,
                    is_approved BOOLEAN NOT NULL DEFAULT TRUE,
                    user_experience_level VARCHAR(20),
                    completion_percentage FLOAT,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    UNIQUE KEY uq_user_rating (user_id, rating_type, target_id),
                    INDEX idx_community_ratings_type_target (rating_type, target_id),
                    INDEX idx_community_ratings_value (rating_value),
                    INDEX idx_community_ratings_approved (is_approved),
                    INDEX idx_community_ratings_featured (is_featured),
                    
                    CONSTRAINT check_valid_rating_type CHECK (rating_type IN ('story', 'session', 'feedback', 'user_content')),
                    CONSTRAINT check_rating_value_range CHECK (rating_value >= 1 AND rating_value <= 5),
                    CONSTRAINT check_difficulty_rating_range CHECK (difficulty_rating IS NULL OR (difficulty_rating >= 1 AND difficulty_rating <= 5)),
                    CONSTRAINT check_clarity_rating_range CHECK (clarity_rating IS NULL OR (clarity_rating >= 1 AND clarity_rating <= 5)),
                    CONSTRAINT check_engagement_rating_range CHECK (engagement_rating IS NULL OR (engagement_rating >= 1 AND engagement_rating <= 5)),
                    CONSTRAINT check_educational_value_rating_range CHECK (educational_value_rating IS NULL OR (educational_value_rating >= 1 AND educational_value_rating <= 5)),
                    CONSTRAINT check_helpful_votes_positive CHECK (helpful_votes >= 0),
                    CONSTRAINT check_unhelpful_votes_positive CHECK (unhelpful_votes >= 0),
                    CONSTRAINT check_completion_percentage_range CHECK (completion_percentage IS NULL OR (completion_percentage >= 0 AND completion_percentage <= 100)),
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # Create progress_shares table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS progress_shares (
                    id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36) NOT NULL,
                    session_id CHAR(36),
                    share_type VARCHAR(20) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    progress_data JSON,
                    achievement_type VARCHAR(50),
                    privacy_level VARCHAR(20) NOT NULL DEFAULT 'friends',
                    visible_to_groups JSON,
                    visible_to_friends JSON,
                    view_count INT NOT NULL DEFAULT 0,
                    like_count INT NOT NULL DEFAULT 0,
                    comment_count INT NOT NULL DEFAULT 0,
                    allow_comments BOOLEAN NOT NULL DEFAULT TRUE,
                    allow_reactions BOOLEAN NOT NULL DEFAULT TRUE,
                    is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
                    expires_at DATETIME(6),
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    INDEX idx_progress_shares_user_privacy (user_id, privacy_level),
                    INDEX idx_progress_shares_type (share_type),
                    INDEX idx_progress_shares_achievement (achievement_type),
                    INDEX idx_progress_shares_active (is_active),
                    INDEX idx_progress_shares_pinned (is_pinned),
                    INDEX idx_progress_shares_expires (expires_at),
                    
                    CONSTRAINT check_valid_privacy_level CHECK (privacy_level IN ('public', 'friends', 'groups', 'private')),
                    CONSTRAINT check_view_count_positive CHECK (view_count >= 0),
                    CONSTRAINT check_like_count_positive CHECK (like_count >= 0),
                    CONSTRAINT check_comment_count_positive CHECK (comment_count >= 0),
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES practice_sessions(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            # Create social_interactions table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS social_interactions (
                    id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36) NOT NULL,
                    target_type VARCHAR(20) NOT NULL,
                    target_id CHAR(36) NOT NULL,
                    interaction_type VARCHAR(20) NOT NULL,
                    content TEXT,
                    reaction_emoji VARCHAR(10),
                    is_anonymous BOOLEAN NOT NULL DEFAULT FALSE,
                    is_public BOOLEAN NOT NULL DEFAULT TRUE,
                    response_to CHAR(36),
                    response_count INT NOT NULL DEFAULT 0,
                    is_flagged BOOLEAN NOT NULL DEFAULT FALSE,
                    is_approved BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                    
                    UNIQUE KEY uq_user_interaction (user_id, target_type, target_id, interaction_type),
                    INDEX idx_social_interactions_target (target_type, target_id),
                    INDEX idx_social_interactions_type (interaction_type),
                    INDEX idx_social_interactions_user_type (user_id, interaction_type),
                    INDEX idx_social_interactions_public (is_public),
                    INDEX idx_social_interactions_response_to (response_to),
                    
                    CONSTRAINT check_valid_target_type CHECK (target_type IN ('progress_share', 'feedback', 'rating', 'session')),
                    CONSTRAINT check_valid_interaction_type CHECK (interaction_type IN ('like', 'comment', 'reaction', 'view', 'share')),
                    CONSTRAINT check_response_count_positive CHECK (response_count >= 0),
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (response_to) REFERENCES social_interactions(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            logger.info("Successfully created social learning tables:")
            logger.info("- friendships")
            logger.info("- community_feedback")
            logger.info("- community_ratings")
            logger.info("- progress_shares")
            logger.info("- social_interactions")
        
        # Close engine
        await engine.dispose()
        
        logger.info("Social learning schema migration completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to create social learning tables: {e}")
        raise


async def drop_social_tables():
    """Drop all social learning tables (for rollback)"""
    
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
        
        logger.warning("Dropping social learning tables...")
        
        async with engine.begin() as conn:
            # Drop tables in reverse dependency order
            tables = [
                "social_interactions",
                "progress_shares", 
                "community_ratings",
                "community_feedback",
                "friendships"
            ]
            
            for table in tables:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                logger.warning(f"Dropped table: {table}")
        
        # Close engine
        await engine.dispose()
        
        logger.warning("All social learning tables dropped")
        
    except Exception as e:
        logger.error(f"Failed to drop social learning tables: {e}")
        raise


async def verify_social_tables():
    """Verify that all social tables were created successfully"""
    
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
                AND table_name IN ('friendships', 'community_feedback', 'community_ratings', 'progress_shares', 'social_interactions')
                ORDER BY table_name
            """)
            
            result = await conn.execute(tables_query, {"database_name": db_config.database})
            tables = result.fetchall()
            
            expected_tables = {
                "friendships", "community_feedback", "community_ratings", 
                "progress_shares", "social_interactions"
            }
            found_tables = {row[0] for row in tables}
            
            if found_tables == expected_tables:
                logger.info("✓ All social learning tables verified successfully")
                
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
        logger.error(f"Failed to verify social tables: {e}")
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
                await create_social_tables()
            elif command == "drop":
                await drop_social_tables()
            elif command == "verify":
                success = await verify_social_tables()
                sys.exit(0 if success else 1)
            else:
                print("Usage: python create_social_tables.py [create|drop|verify]")
                sys.exit(1)
        else:
            # Default: create tables
            await create_social_tables()
            await verify_social_tables()
    
    asyncio.run(main())


# Migration metadata
MIGRATION_NAME = "create_social_tables"
MIGRATION_VERSION = "005"
MIGRATION_DESCRIPTION = "Create tables for social learning features"