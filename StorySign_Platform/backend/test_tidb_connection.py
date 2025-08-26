"""
Test script to verify TiDB connection and optionally create progress tracking tables
Can be used with provided TiDB credentials to test real database connectivity
"""

import asyncio
import logging
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Set up path for imports
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.base import Base
from models.progress import PracticeSession, SentenceAttempt, UserProgress

logger = logging.getLogger(__name__)


async def test_tidb_connection(
    host: str = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
    port: int = 4000,
    database: str = "storysign",
    username: str = "82FPCEB0",
    password: str = "f53544d9-be1d-4e57-8135-f23cdd513351",
    create_tables: bool = False
):
    """
    Test TiDB connection and optionally create progress tracking tables
    
    Args:
        host: TiDB host
        port: TiDB port
        database: Database name
        username: TiDB username (public key)
        password: TiDB password (private key)
        create_tables: Whether to create the progress tracking tables
    """
    
    # Build connection URL for TiDB (TiDB Cloud requires SSL)
    connection_url = f"mysql+asyncmy://{username}:{password}@{host}:{port}/{database}?ssl=true"
    
    try:
        logger.info(f"Testing TiDB connection to {host}:{port}/{database}")
        
        # Create async engine with SSL configuration for TiDB Cloud
        engine = create_async_engine(
            connection_url,
            echo=False,  # Set to True for SQL debugging
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            connect_args={
                "charset": "utf8mb4",
                "autocommit": False
            }
        )
        
        # Test basic connection
        async with engine.begin() as conn:
            # Test basic query
            result = await conn.execute(text("SELECT 1 as test, NOW() as current_time"))
            row = result.fetchone()
            
            if row:
                logger.info(f"✅ Connection successful! Test query returned: {row.test}, Time: {row.current_time}")
            else:
                logger.error("❌ Connection test failed - no result returned")
                return False
            
            # Check database info
            db_info_result = await conn.execute(text("SELECT VERSION() as version"))
            db_info = db_info_result.fetchone()
            logger.info(f"📊 Database version: {db_info.version}")
            
            # List existing tables
            tables_result = await conn.execute(text("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = :database_name
                ORDER BY table_name
            """), {"database_name": database})
            
            existing_tables = tables_result.fetchall()
            logger.info(f"📋 Existing tables in '{database}' database:")
            for table in existing_tables:
                logger.info(f"   - {table.table_name} ({table.table_type})")
            
            if not existing_tables:
                logger.info("   (No tables found)")
            
            # Create progress tracking tables if requested
            if create_tables:
                logger.info("🔨 Creating progress tracking tables...")
                
                try:
                    # Create all tables from models
                    await conn.run_sync(Base.metadata.create_all)
                    
                    logger.info("✅ Progress tracking tables created successfully:")
                    logger.info("   - practice_sessions")
                    logger.info("   - sentence_attempts")
                    logger.info("   - user_progress")
                    
                    # Verify tables were created
                    verify_result = await conn.execute(text("""
                        SELECT table_name, table_rows, data_length
                        FROM information_schema.tables 
                        WHERE table_schema = :database_name 
                        AND table_name IN ('practice_sessions', 'sentence_attempts', 'user_progress')
                        ORDER BY table_name
                    """), {"database_name": database})
                    
                    created_tables = verify_result.fetchall()
                    logger.info("📊 Table verification:")
                    for table in created_tables:
                        logger.info(f"   ✓ {table.table_name}: {table.table_rows} rows, {table.data_length} bytes")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to create tables: {e}")
                    return False
        
        # Close engine
        await engine.dispose()
        
        logger.info("🎉 TiDB connection test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ TiDB connection failed: {e}")
        return False


async def test_progress_tracking_operations(
    host: str = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
    port: int = 4000,
    database: str = "storysign",
    username: str = "82FPCEB0",
    password: str = "f53544d9-be1d-4e57-8135-f23cdd513351"
):
    """
    Test basic progress tracking operations on TiDB
    """
    from uuid import uuid4
    from datetime import datetime
    
    connection_url = f"mysql+asyncmy://{username}:{password}@{host}:{port}/{database}?ssl=true"
    
    try:
        logger.info("🧪 Testing progress tracking operations...")
        
        engine = create_async_engine(
            connection_url, 
            echo=False,
            connect_args={
                "charset": "utf8mb4",
                "autocommit": False
            }
        )
        
        async with engine.begin() as conn:
            # Test inserting a practice session
            user_id = str(uuid4())
            session_id = str(uuid4())
            
            insert_session = text("""
                INSERT INTO practice_sessions 
                (id, user_id, session_type, difficulty_level, total_sentences, status, created_at, updated_at)
                VALUES (:id, :user_id, :session_type, :difficulty_level, :total_sentences, :status, :created_at, :updated_at)
            """)
            
            await conn.execute(insert_session, {
                "id": session_id,
                "user_id": user_id,
                "session_type": "individual",
                "difficulty_level": "beginner",
                "total_sentences": 3,
                "status": "completed",
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })
            
            logger.info(f"✅ Inserted practice session: {session_id}")
            
            # Test inserting a sentence attempt
            attempt_id = str(uuid4())
            
            insert_attempt = text("""
                INSERT INTO sentence_attempts
                (id, session_id, sentence_index, target_sentence, confidence_score, accuracy_score, fluency_score, attempt_number, attempted_at)
                VALUES (:id, :session_id, :sentence_index, :target_sentence, :confidence_score, :accuracy_score, :fluency_score, :attempt_number, :attempted_at)
            """)
            
            await conn.execute(insert_attempt, {
                "id": attempt_id,
                "session_id": session_id,
                "sentence_index": 0,
                "target_sentence": "Hello, this is a test sentence.",
                "confidence_score": 0.85,
                "accuracy_score": 0.90,
                "fluency_score": 0.80,
                "attempt_number": 1,
                "attempted_at": datetime.now()
            })
            
            logger.info(f"✅ Inserted sentence attempt: {attempt_id}")
            
            # Test inserting user progress
            progress_id = str(uuid4())
            
            insert_progress = text("""
                INSERT INTO user_progress
                (id, user_id, skill_area, current_level, experience_points, total_sessions, total_attempts, successful_attempts, created_at, updated_at)
                VALUES (:id, :user_id, :skill_area, :current_level, :experience_points, :total_sessions, :total_attempts, :successful_attempts, :created_at, :updated_at)
            """)
            
            await conn.execute(insert_progress, {
                "id": progress_id,
                "user_id": user_id,
                "skill_area": "vocabulary",
                "current_level": 1.5,
                "experience_points": 75.0,
                "total_sessions": 1,
                "total_attempts": 1,
                "successful_attempts": 1,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })
            
            logger.info(f"✅ Inserted user progress: {progress_id}")
            
            # Test querying the data
            query_result = await conn.execute(text("""
                SELECT 
                    ps.id as session_id,
                    ps.session_type,
                    ps.difficulty_level,
                    sa.target_sentence,
                    sa.confidence_score,
                    up.skill_area,
                    up.current_level
                FROM practice_sessions ps
                JOIN sentence_attempts sa ON ps.id = sa.session_id
                JOIN user_progress up ON ps.user_id = up.user_id
                WHERE ps.user_id = :user_id
            """), {"user_id": user_id})
            
            results = query_result.fetchall()
            
            logger.info("📊 Query results:")
            for row in results:
                logger.info(f"   Session: {row.session_type} ({row.difficulty_level})")
                logger.info(f"   Sentence: {row.target_sentence}")
                logger.info(f"   Confidence: {row.confidence_score}")
                logger.info(f"   Skill: {row.skill_area} (Level {row.current_level})")
            
            # Clean up test data
            await conn.execute(text("DELETE FROM sentence_attempts WHERE session_id = :session_id"), {"session_id": session_id})
            await conn.execute(text("DELETE FROM user_progress WHERE id = :id"), {"id": progress_id})
            await conn.execute(text("DELETE FROM practice_sessions WHERE id = :id"), {"id": session_id})
            
            logger.info("🧹 Cleaned up test data")
        
        await engine.dispose()
        
        logger.info("🎉 Progress tracking operations test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Progress tracking operations test failed: {e}")
        return False


async def main():
    """Main test function"""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 TiDB Connection and Progress Tracking Test")
    print("=" * 60)
    
    # Test basic connection
    print("\n1. Testing basic TiDB connection...")
    connection_success = await test_tidb_connection(create_tables=False)
    
    if not connection_success:
        print("❌ Basic connection test failed. Exiting.")
        return
    
    # Ask user if they want to create tables
    print("\n2. Table creation test...")
    create_tables = input("Do you want to create progress tracking tables? (y/N): ").lower().startswith('y')
    
    if create_tables:
        table_success = await test_tidb_connection(create_tables=True)
        
        if table_success:
            # Test operations if tables were created successfully
            print("\n3. Testing progress tracking operations...")
            operations_success = await test_progress_tracking_operations()
            
            if operations_success:
                print("\n✅ All tests passed! Progress tracking system is ready for TiDB.")
            else:
                print("\n❌ Operations test failed.")
        else:
            print("\n❌ Table creation failed.")
    else:
        print("Skipping table creation and operations test.")
    
    print("\n" + "=" * 60)
    print("🎯 Test Summary:")
    print("• TiDB connection: ✅ Successful")
    if create_tables:
        print("• Table creation: ✅ Successful" if table_success else "• Table creation: ❌ Failed")
        if table_success:
            print("• Operations test: ✅ Successful" if operations_success else "• Operations test: ❌ Failed")
    else:
        print("• Table creation: ⏭️  Skipped")
        print("• Operations test: ⏭️  Skipped")


if __name__ == "__main__":
    asyncio.run(main())