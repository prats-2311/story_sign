"""
Migration script to create learning progress tracking tables
Creates practice_sessions, sentence_attempts, and user_progress tables
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
from models.base import Base
from models.progress import PracticeSession, SentenceAttempt, UserProgress

logger = logging.getLogger(__name__)


async def create_progress_tables():
    """
    Create all progress tracking tables in the database
    """
    try:
        # Get database configuration
        config = get_config()
        db_config = config.database
        
        # Create async engine
        engine = create_async_engine(
            db_config.get_connection_url(async_driver=True),
            echo=db_config.echo_queries
        )
        
        logger.info("Creating progress tracking tables...")
        
        # Create all tables
        async with engine.begin() as conn:
            # Create tables from models
            await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Successfully created progress tracking tables:")
            logger.info("- practice_sessions")
            logger.info("- sentence_attempts") 
            logger.info("- user_progress")
        
        # Close engine
        await engine.dispose()
        
        logger.info("Progress tracking schema migration completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to create progress tracking tables: {e}")
        raise


async def drop_progress_tables():
    """
    Drop all progress tracking tables (for rollback)
    """
    try:
        # Get database configuration
        config = get_config()
        db_config = config.database
        
        # Create async engine
        engine = create_async_engine(
            db_config.get_connection_url(async_driver=True),
            echo=db_config.echo_queries
        )
        
        logger.warning("Dropping progress tracking tables...")
        
        async with engine.begin() as conn:
            # Drop tables in reverse dependency order
            await conn.execute(text("DROP TABLE IF EXISTS sentence_attempts"))
            await conn.execute(text("DROP TABLE IF EXISTS user_progress"))
            await conn.execute(text("DROP TABLE IF EXISTS practice_sessions"))
            
            logger.warning("Dropped all progress tracking tables")
        
        # Close engine
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"Failed to drop progress tracking tables: {e}")
        raise


async def verify_tables():
    """
    Verify that all tables were created successfully
    """
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
                AND table_name IN ('practice_sessions', 'sentence_attempts', 'user_progress')
                ORDER BY table_name
            """)
            
            result = await conn.execute(tables_query, {"database_name": db_config.database})
            tables = result.fetchall()
            
            expected_tables = {"practice_sessions", "sentence_attempts", "user_progress"}
            found_tables = {row[0] for row in tables}
            
            if found_tables == expected_tables:
                logger.info("✓ All progress tracking tables verified successfully")
                
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
        logger.error(f"Failed to verify tables: {e}")
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
                await create_progress_tables()
            elif command == "drop":
                await drop_progress_tables()
            elif command == "verify":
                success = await verify_tables()
                sys.exit(0 if success else 1)
            else:
                print("Usage: python create_progress_tables.py [create|drop|verify]")
                sys.exit(1)
        else:
            # Default: create tables
            await create_progress_tables()
            await verify_tables()
    
    asyncio.run(main())