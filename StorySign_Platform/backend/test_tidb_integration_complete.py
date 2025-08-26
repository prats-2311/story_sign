"""
Complete TiDB integration test for progress tracking
Tests the full progress tracking system with actual TiDB database
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Dict, Any

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

# Set up path for imports
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.base import Base
from models.progress import PracticeSession, SentenceAttempt, UserProgress
from repositories.progress_repository import ProgressRepository
from services.progress_service import ProgressService

logger = logging.getLogger(__name__)


class TiDBIntegrationTest:
    """Complete integration test with TiDB database"""
    
    def __init__(self):
        # TiDB connection parameters from provided credentials
        self.connection_params = {
            "host": "gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
            "port": 4000,
            "database": "test",  # Using test database
            "username": "28XbMEz3PD5h7d6.root",
            "password": None,  # Will be set from environment or prompt
            "ssl_mode": "VERIFY_IDENTITY",
            "ssl_ca": "/etc/ssl/cert.pem"
        }
        self.engine = None
        self.session_factory = None
    
    def get_connection_url(self, password: str) -> str:
        """Build TiDB connection URL"""
        return (
            f"mysql+asyncmy://{self.connection_params['username']}:{password}@"
            f"{self.connection_params['host']}:{self.connection_params['port']}/"
            f"{self.connection_params['database']}?ssl_mode={self.connection_params['ssl_mode']}"
        )
    
    async def setup_database(self, password: str):
        """Set up TiDB connection and create tables"""
        try:
            connection_url = self.get_connection_url(password)
            
            logger.info(f"Connecting to TiDB at {self.connection_params['host']}...")
            
            # Create async engine
            self.engine = create_async_engine(
                connection_url,
                echo=False,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1 as test, NOW() as current_time"))
                row = result.fetchone()
                logger.info(f"✅ TiDB connection successful! Time: {row.current_time}")
            
            # Create session factory
            self.session_factory = async_sessionmaker(self.engine, class_=AsyncSession)
            
            # Create tables
            await self.create_progress_tables()
            
            logger.info("✅ TiDB setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ TiDB setup failed: {e}")
            return False
    
    async def create_progress_tables(self):
        """Create progress tracking tables in TiDB"""
        try:
            async with self.engine.begin() as conn:
                # Drop existing tables if they exist (for clean test)
                await conn.execute(text("DROP TABLE IF EXISTS sentence_attempts"))
                await conn.execute(text("DROP TABLE IF EXISTS user_progress"))
                await conn.execute(text("DROP TABLE IF EXISTS practice_sessions"))
                
                # Create tables from models
                await conn.run_sync(Base.metadata.create_all)
                
                logger.info("✅ Progress tracking tables created in TiDB")
                
                # Verify tables were created
                result = await conn.execute(text("""
                    SELECT table_name, table_rows, data_length
                    FROM information_schema.tables 
                    WHERE table_schema = :database_name 
                    AND table_name IN ('practice_sessions', 'sentence_attempts', 'user_progress')
                    ORDER BY table_name
                """), {"database_name": self.connection_params["database"]})
                
                tables = result.fetchall()
                logger.info("📊 Created tables:")
                for table in tables:
                    logger.info(f"   ✓ {table.table_name}")
                
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")
            raise
    
    async def test_complete_asl_world_workflow(self):
        """Test complete ASL World workflow with TiDB"""
        logger.info("🧪 Testing complete ASL World workflow...")
        
        async with self.session_factory() as session:
            try:
                service = ProgressService(session)
                user_id = str(uuid4())
                
                # 1. Start ASL World practice session
                logger.info("1️⃣ Starting ASL World practice session...")
                
                asl_world_config = {
                    "session_type": "individual",
                    "session_name": "TiDB Integration Test - ASL World",
                    "difficulty_level": "intermediate",
                    "skill_areas": ["vocabulary", "grammar", "fluency"],
                    "story_content": {
                        "title": "TiDB Integration Story",
                        "sentences": [
                            "Welcome to StorySign ASL learning platform.",
                            "We are testing TiDB database integration.",
                            "This demonstrates real-time progress tracking.",
                            "Your learning journey is being recorded.",
                            "Great job practicing ASL with us!"
                        ],
                        "generated_by": "ai",
                        "difficulty": "intermediate",
                        "metadata": {
                            "topic": "platform_introduction",
                            "vocabulary_level": "intermediate",
                            "estimated_duration_minutes": 8
                        }
                    },
                    "total_sentences": 5,
                    "session_data": {
                        "module": "asl_world",
                        "video_processing_enabled": True,
                        "mediapipe_config": {
                            "min_detection_confidence": 0.5,
                            "min_tracking_confidence": 0.5,
                            "model_complexity": 1
                        },
                        "ai_feedback_enabled": True,
                        "tidb_integration_test": True
                    }
                }
                
                practice_session = await service.start_practice_session(user_id, asl_world_config)
                logger.info(f"✅ Session started: {practice_session.id}")
                
                # 2. Simulate realistic ASL practice with MediaPipe data
                logger.info("2️⃣ Simulating ASL practice with MediaPipe integration...")
                
                total_attempts = 0
                successful_attempts = 0
                
                for sentence_idx, sentence in enumerate(asl_world_config["story_content"]["sentences"]):
                    logger.info(f"   📝 Practicing sentence {sentence_idx + 1}: '{sentence[:30]}...'")
                    
                    # Simulate 1-3 attempts per sentence (realistic user behavior)
                    num_attempts = 1 if sentence_idx < 2 else 2
                    
                    for attempt_num in range(1, num_attempts + 1):
                        # Simulate realistic MediaPipe landmark data
                        landmark_data = {
                            "hand_landmarks": [
                                # Right hand (21 landmarks)
                                [[0.1 + i*0.01, 0.2 + i*0.01, 0.3 + i*0.01] for i in range(21)],
                                # Left hand (21 landmarks)
                                [[0.4 + i*0.01, 0.5 + i*0.01, 0.6 + i*0.01] for i in range(21)]
                            ],
                            "pose_landmarks": [[0.5, 0.5, 0.5] for _ in range(33)],
                            "face_landmarks": [[0.45, 0.45, 0.45] for _ in range(468)],
                            "timestamp": datetime.now().isoformat(),
                            "frame_count": 45 + sentence_idx * 10,
                            "detection_confidence": 0.85 + (attempt_num * 0.05)
                        }
                        
                        # Simulate gesture analysis with improving performance on retries
                        base_confidence = 0.70 + (sentence_idx * 0.04) + (attempt_num * 0.08)
                        base_accuracy = 0.75 + (sentence_idx * 0.03) + (attempt_num * 0.06)
                        base_fluency = 0.65 + (sentence_idx * 0.05) + (attempt_num * 0.10)
                        
                        # Add realistic variation
                        import random
                        confidence_score = min(1.0, base_confidence + random.uniform(-0.08, 0.08))
                        accuracy_score = min(1.0, base_accuracy + random.uniform(-0.06, 0.06))
                        fluency_score = min(1.0, base_fluency + random.uniform(-0.10, 0.10))
                        
                        # Generate AI feedback based on performance
                        overall_score = (accuracy_score * 0.4 + confidence_score * 0.3 + fluency_score * 0.3)
                        
                        if overall_score >= 0.85:
                            feedback = "Excellent signing! Your hand shapes and movements are very clear."
                            suggestions = ["Keep up the great work!", "Try to maintain this consistency."]
                            errors = []
                        elif overall_score >= 0.75:
                            feedback = "Good job! There are a few areas for improvement."
                            suggestions = [
                                "Focus on keeping your hand shapes distinct",
                                "Try to maintain steady movement speed"
                            ]
                            errors = [
                                {"type": "hand_shape", "severity": "minor", "description": "Slight finger positioning variation"}
                            ]
                        else:
                            feedback = "Keep practicing! Focus on the key elements of each sign."
                            suggestions = [
                                "Review the hand shape for this sign",
                                "Practice the movement more slowly first",
                                "Make sure your palm orientation is correct"
                            ]
                            errors = [
                                {"type": "hand_shape", "severity": "moderate", "description": "Hand shape needs adjustment"},
                                {"type": "movement", "severity": "minor", "description": "Movement could be more fluid"}
                            ]
                        
                        # Create attempt data
                        attempt_data = {
                            "sentence_index": sentence_idx,
                            "target_sentence": sentence,
                            "landmark_data": landmark_data,
                            "gesture_sequence": [
                                {
                                    "gesture_id": f"tidb_test_{sentence_idx}_{attempt_num}",
                                    "start_frame": 5,
                                    "end_frame": 40,
                                    "duration_ms": 1400 + sentence_idx * 200,
                                    "confidence": confidence_score,
                                    "hand_used": "both" if sentence_idx % 2 == 0 else "right",
                                    "movement_type": "compound" if len(sentence.split()) > 6 else "simple"
                                }
                            ],
                            "confidence_score": confidence_score,
                            "accuracy_score": accuracy_score,
                            "fluency_score": fluency_score,
                            "ai_feedback": feedback,
                            "suggestions": suggestions,
                            "detected_errors": errors,
                            "duration_ms": 2000 + sentence_idx * 300 + attempt_num * 100,
                            "video_start_frame": sentence_idx * 100,
                            "video_end_frame": sentence_idx * 100 + 45
                        }
                        
                        # Record attempt in TiDB
                        attempt = await service.record_sentence_attempt(practice_session.id, attempt_data)
                        
                        total_attempts += 1
                        if attempt.is_successful:
                            successful_attempts += 1
                        
                        logger.info(f"      ✅ Attempt {attempt_num}: Score {overall_score:.2f}, Success: {attempt.is_successful}")
                
                # 3. Complete session with performance metrics
                logger.info("3️⃣ Completing practice session...")
                
                completion_data = {
                    "performance_metrics": {
                        "total_video_frames": 650,
                        "processed_frames": 645,
                        "dropped_frames": 5,
                        "average_processing_latency_ms": 38,
                        "gesture_detection_accuracy": 0.89,
                        "mediapipe_processing_time_ms": 35,
                        "ai_analysis_time_ms": 150,
                        "total_processing_time_seconds": 28,
                        "tidb_integration_test": True
                    }
                }
                
                completed_session = await service.complete_practice_session(
                    practice_session.id, completion_data
                )
                
                logger.info(f"✅ Session completed: Score {completed_session.overall_score:.2f}")
                
                # 4. Verify progress tracking
                logger.info("4️⃣ Verifying progress tracking...")
                
                progress_summary = await service.get_user_progress_summary(user_id)
                
                # Verify data integrity
                assert len(progress_summary["progress_records"]) == 3  # vocabulary, grammar, fluency
                assert progress_summary["performance_analytics"]["session_analytics"]["total_sessions"] == 1
                assert progress_summary["performance_analytics"]["attempt_analytics"]["total_attempts"] == total_attempts
                
                logger.info("✅ Progress tracking verified:")
                logger.info(f"   - Skill areas tracked: {len(progress_summary['progress_records'])}")
                logger.info(f"   - Total attempts: {total_attempts}")
                logger.info(f"   - Success rate: {(successful_attempts/total_attempts)*100:.1f}%")
                
                # 5. Test analytics queries
                logger.info("5️⃣ Testing analytics queries...")
                
                repository = ProgressRepository(session)
                analytics = await repository.get_user_performance_analytics(user_id)
                
                logger.info("✅ Analytics queries successful:")
                logger.info(f"   - Sessions: {analytics['session_analytics']['total_sessions']}")
                logger.info(f"   - Practice time: {analytics['session_analytics']['total_practice_time']}s")
                logger.info(f"   - Average score: {analytics['session_analytics']['average_session_score']:.2f}")
                
                # Commit all changes
                await session.commit()
                
                logger.info("🎉 Complete ASL World workflow test PASSED!")
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Workflow test failed: {e}")
                raise
    
    async def test_performance_benchmarks(self):
        """Test performance benchmarks with TiDB"""
        logger.info("⚡ Testing performance benchmarks...")
        
        async with self.session_factory() as session:
            try:
                repository = ProgressRepository(session)
                user_id = str(uuid4())
                
                # Test session creation performance
                import time
                
                session_data = {
                    "user_id": user_id,
                    "session_type": "individual",
                    "difficulty_level": "intermediate",
                    "total_sentences": 10,
                    "skill_areas": ["vocabulary", "grammar", "fluency"]
                }
                
                start_time = time.time()
                practice_session = await repository.create_practice_session(session_data)
                session_creation_time = (time.time() - start_time) * 1000
                
                logger.info(f"✅ Session creation: {session_creation_time:.2f}ms")
                assert session_creation_time < 100, f"Session creation took {session_creation_time:.2f}ms (should be <100ms)"
                
                # Test attempt recording performance
                attempt_data = {
                    "session_id": practice_session.id,
                    "sentence_index": 0,
                    "target_sentence": "Performance test sentence with TiDB",
                    "landmark_data": {
                        "hand_landmarks": [[[0.1, 0.2, 0.3] for _ in range(21)] for _ in range(2)],
                        "pose_landmarks": [[0.5, 0.5, 0.5] for _ in range(33)],
                        "timestamp": datetime.now().isoformat()
                    },
                    "confidence_score": 0.85,
                    "accuracy_score": 0.90,
                    "fluency_score": 0.80,
                    "duration_ms": 2000
                }
                
                start_time = time.time()
                attempt = await repository.create_sentence_attempt(attempt_data)
                attempt_creation_time = (time.time() - start_time) * 1000
                
                logger.info(f"✅ Attempt recording: {attempt_creation_time:.2f}ms")
                assert attempt_creation_time < 100, f"Attempt recording took {attempt_creation_time:.2f}ms (should be <100ms)"
                
                # Test progress update performance
                start_time = time.time()
                progress = await repository.get_or_create_user_progress(user_id, "vocabulary")
                progress_update_time = (time.time() - start_time) * 1000
                
                logger.info(f"✅ Progress update: {progress_update_time:.2f}ms")
                assert progress_update_time < 100, f"Progress update took {progress_update_time:.2f}ms (should be <100ms)"
                
                # Test analytics query performance
                start_time = time.time()
                analytics = await repository.get_user_performance_analytics(user_id)
                analytics_query_time = (time.time() - start_time) * 1000
                
                logger.info(f"✅ Analytics query: {analytics_query_time:.2f}ms")
                assert analytics_query_time < 100, f"Analytics query took {analytics_query_time:.2f}ms (should be <100ms)"
                
                await session.commit()
                
                logger.info("🎉 All performance benchmarks PASSED!")
                return True
                
            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Performance test failed: {e}")
                raise
    
    async def cleanup(self):
        """Clean up test data and connections"""
        try:
            if self.engine:
                # Clean up test data
                async with self.engine.begin() as conn:
                    await conn.execute(text("DELETE FROM sentence_attempts WHERE target_sentence LIKE '%TiDB%' OR target_sentence LIKE '%Performance test%'"))
                    await conn.execute(text("DELETE FROM user_progress WHERE skill_area IN ('vocabulary', 'grammar', 'fluency')"))
                    await conn.execute(text("DELETE FROM practice_sessions WHERE session_name LIKE '%TiDB%'"))
                
                await self.engine.dispose()
                logger.info("✅ Cleanup completed")
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {e}")
    
    async def run_complete_test(self, password: str):
        """Run complete TiDB integration test"""
        try:
            logger.info("🚀 Starting TiDB Integration Test")
            logger.info("=" * 60)
            
            # Setup database
            if not await self.setup_database(password):
                return False
            
            # Run tests
            await self.test_complete_asl_world_workflow()
            await self.test_performance_benchmarks()
            
            logger.info("=" * 60)
            logger.info("🎉 TiDB Integration Test COMPLETED SUCCESSFULLY!")
            logger.info("✅ All tests passed")
            logger.info("✅ Performance requirements met")
            logger.info("✅ ASL World integration verified")
            logger.info("✅ Progress tracking system ready for production")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ TiDB Integration Test FAILED: {e}")
            return False
        
        finally:
            await self.cleanup()


async def main():
    """Main test execution"""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🔐 TiDB Integration Test")
    print("=" * 60)
    
    # Get password from user
    password = input("Enter TiDB password: ").strip()
    
    if not password:
        print("❌ Password required for TiDB connection")
        return
    
    # Run integration test
    test = TiDBIntegrationTest()
    success = await test.run_complete_test(password)
    
    if success:
        print("\n🎯 Integration Test Summary:")
        print("• TiDB connection: ✅ Successful")
        print("• Table creation: ✅ Successful")
        print("• ASL World workflow: ✅ Complete")
        print("• Performance benchmarks: ✅ All <100ms")
        print("• Progress tracking: ✅ Fully functional")
        print("\n🚀 Progress tracking system is production-ready!")
    else:
        print("\n❌ Integration test failed. Check logs for details.")


if __name__ == "__main__":
    asyncio.run(main())