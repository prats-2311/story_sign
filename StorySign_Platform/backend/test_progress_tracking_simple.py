"""
Simple test for learning progress tracking functionality using SQLite
Tests models, repository, service layer, and integration with existing ASL World
"""

import asyncio
import json
import logging
import tempfile
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


class TestProgressTrackingSimple:
    """Simple test suite for progress tracking functionality using SQLite"""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
    
    async def setup(self):
        """Set up test database"""
        # Create temporary SQLite database
        self.db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_file.close()
        
        # Create async engine for SQLite
        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{self.db_file.name}",
            echo=False
        )
        
        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Create session factory
        self.session_factory = async_sessionmaker(self.engine, class_=AsyncSession)
        
        logger.info(f"Test database created: {self.db_file.name}")
    
    async def cleanup(self):
        """Clean up test database"""
        if self.engine:
            await self.engine.dispose()
        
        if hasattr(self, 'db_file') and os.path.exists(self.db_file.name):
            os.unlink(self.db_file.name)
            logger.info("Test database cleaned up")
    
    def get_session(self):
        """Get database session"""
        return self.session_factory()
    
    async def test_practice_session_model(self):
        """Test PracticeSession model creation and validation"""
        print("Testing PracticeSession model...")
        
        async with self.get_session() as session:
            user_id = str(uuid4())
            
            session_data = {
                "user_id": user_id,
                "session_type": "individual",
                "difficulty_level": "beginner",
                "total_sentences": 3,
                "status": "active"
            }
            
            session_obj = PracticeSession(**session_data)
            session.add(session_obj)
            await session.commit()
            
            # Test model properties
            assert session_obj.id is not None
            assert session_obj.user_id == user_id
            assert session_obj.session_type == "individual"
            assert session_obj.status == "active"
            assert session_obj.created_at is not None
            
            # Test completion percentage calculation
            session_obj.sentences_completed = 2
            completion_pct = session_obj.calculate_completion_percentage()
            assert abs(completion_pct - 66.67) < 0.1
            
            # Test performance summary
            summary = session_obj.get_performance_summary()
            assert summary["session_id"] == session_obj.id
            assert summary["sentences_completed"] == 2
            assert summary["total_sentences"] == 3
            
            print("✓ PracticeSession model test passed")
    
    async def test_sentence_attempt_model(self):
        """Test SentenceAttempt model creation and validation"""
        print("Testing SentenceAttempt model...")
        
        async with self.get_session() as session:
            user_id = str(uuid4())
            
            # Create practice session first
            practice_session = PracticeSession(
                user_id=user_id,
                session_type="individual",
                status="active"
            )
            session.add(practice_session)
            await session.flush()
            
            # Create sentence attempt
            attempt_data = {
                "session_id": practice_session.id,
                "sentence_index": 0,
                "target_sentence": "Hello, my name is John.",
                "confidence_score": 0.85,
                "accuracy_score": 0.90,
                "fluency_score": 0.75,
                "attempt_number": 1
            }
            
            attempt = SentenceAttempt(**attempt_data)
            session.add(attempt)
            await session.commit()
            
            # Test model properties
            assert attempt.id is not None
            assert attempt.session_id == practice_session.id
            assert attempt.sentence_index == 0
            assert attempt.confidence_score == 0.85
            
            # Test overall score calculation
            overall_score = attempt.get_overall_score()
            expected_score = 0.90 * 0.4 + 0.85 * 0.3 + 0.75 * 0.3  # Weighted average
            assert abs(overall_score - expected_score) < 0.001
            
            # Test performance summary
            summary = attempt.get_performance_summary()
            assert summary["attempt_id"] == attempt.id
            assert abs(summary["overall_score"] - expected_score) < 0.001
            
            print("✓ SentenceAttempt model test passed")
    
    async def test_user_progress_model(self):
        """Test UserProgress model creation and validation"""
        print("Testing UserProgress model...")
        
        async with self.get_session() as session:
            user_id = str(uuid4())
            
            progress_data = {
                "user_id": user_id,
                "skill_area": "fingerspelling",
                "current_level": 2.5,
                "experience_points": 150.0,
                "total_practice_time": 3600,  # 1 hour
                "total_sessions": 5,
                "total_attempts": 25,
                "successful_attempts": 20
            }
            
            progress = UserProgress(**progress_data)
            session.add(progress)
            await session.commit()
            
            # Test model properties
            assert progress.id is not None
            assert progress.user_id == user_id
            assert progress.skill_area == "fingerspelling"
            assert progress.current_level == 2.5
            
            # Test success rate calculation
            success_rate = progress.calculate_success_rate()
            assert success_rate == 80.0  # 20/25 * 100
            
            # Test level progress calculation
            level_progress = progress.calculate_level_progress()
            assert level_progress == 0.5  # 2.5 - 2 = 0.5
            
            # Test milestone addition
            progress.add_milestone(3.0, "Reached level 3")
            assert len(progress.milestones) == 1
            assert progress.milestones[0]["level"] == 3.0
            
            # Test streak update
            progress.update_streak(datetime.now())
            assert progress.learning_streak == 1
            assert progress.longest_streak == 1
            
            print("✓ UserProgress model test passed")
    
    async def test_progress_repository(self):
        """Test progress repository operations"""
        print("Testing ProgressRepository...")
        
        async with self.get_session() as session:
            repository = ProgressRepository(session)
            user_id = str(uuid4())
            
            # Test creating practice session
            session_data = {
                "user_id": user_id,
                "session_type": "individual",
                "difficulty_level": "beginner",
                "total_sentences": 3,
                "skill_areas": ["vocabulary", "grammar"]
            }
            
            practice_session = await repository.create_practice_session(session_data)
            
            assert practice_session.id is not None
            assert practice_session.user_id == user_id
            assert practice_session.session_type == "individual"
            assert practice_session.skill_areas == ["vocabulary", "grammar"]
            
            # Test recording sentence attempts
            attempt_data = {
                "session_id": practice_session.id,
                "sentence_index": 0,
                "target_sentence": "Hello world",
                "confidence_score": 0.8,
                "accuracy_score": 0.9,
                "fluency_score": 0.7,
                "duration_ms": 2500
            }
            
            attempt = await repository.create_sentence_attempt(attempt_data)
            
            assert attempt.id is not None
            assert attempt.session_id == practice_session.id
            assert attempt.sentence_index == 0
            assert attempt.attempt_number == 1
            
            # Test user progress tracking
            skill_area = "vocabulary"
            progress = await repository.get_or_create_user_progress(
                user_id, skill_area, "basic_vocabulary"
            )
            
            assert progress.user_id == user_id
            assert progress.skill_area == skill_area
            assert progress.skill_category == "basic_vocabulary"
            assert progress.current_level == 0.0
            
            # Update progress with session data
            update_data = {
                "duration_seconds": 300,
                "total_attempts": 10,
                "successful_attempts": 8,
                "average_score": 0.85,
                "experience_gained": 25.0
            }
            
            updated_progress = await repository.update_user_progress(
                user_id, skill_area, update_data
            )
            
            assert updated_progress.total_sessions == 1
            assert updated_progress.total_practice_time == 300
            assert updated_progress.total_attempts == 10
            assert updated_progress.successful_attempts == 8
            assert updated_progress.experience_points == 25.0
            assert updated_progress.current_level > 0.0
            
            await session.commit()
            
            print("✓ ProgressRepository test passed")
    
    async def test_progress_service(self):
        """Test progress service operations"""
        print("Testing ProgressService...")
        
        async with self.get_session() as session:
            service = ProgressService(session)
            user_id = str(uuid4())
            
            # Test starting practice session
            story_data = {
                "title": "Test Story",
                "sentences": [
                    "Hello, my name is John.",
                    "I am learning ASL.",
                    "This is a practice session."
                ],
                "difficulty": "beginner"
            }
            
            session_config = {
                "session_type": "individual",
                "story_content": story_data,
                "difficulty_level": "beginner",
                "total_sentences": len(story_data["sentences"]),
                "skill_areas": ["vocabulary", "grammar"]
            }
            
            practice_session = await service.start_practice_session(user_id, session_config)
            
            assert practice_session.id is not None
            assert practice_session.user_id == user_id
            assert practice_session.status == "active"
            assert practice_session.story_content == story_data
            
            # Test recording sentence attempts
            for i, sentence in enumerate(story_data["sentences"]):
                attempt_data = {
                    "sentence_index": i,
                    "target_sentence": sentence,
                    "confidence_score": 0.8 + (i * 0.05),
                    "accuracy_score": 0.85 + (i * 0.03),
                    "fluency_score": 0.75 + (i * 0.04),
                    "ai_feedback": f"Good job on sentence {i+1}!",
                    "duration_ms": 2000
                }
                
                attempt = await service.record_sentence_attempt(
                    practice_session.id, attempt_data
                )
                
                assert attempt.id is not None
                assert attempt.sentence_index == i
                assert attempt.target_sentence == sentence
            
            # Test completing session
            completed_session = await service.complete_practice_session(practice_session.id)
            
            assert completed_session.status == "completed"
            assert completed_session.completed_at is not None
            assert completed_session.sentences_completed == 3
            assert completed_session.overall_score > 0
            
            # Test getting progress summary
            progress_summary = await service.get_user_progress_summary(user_id)
            
            assert progress_summary["user_id"] == user_id
            assert len(progress_summary["progress_records"]) == 2  # vocabulary, grammar
            assert progress_summary["performance_analytics"]["session_analytics"]["total_sessions"] == 1
            
            await session.commit()
            
            print("✓ ProgressService test passed")
    
    async def test_asl_world_integration(self):
        """Test integration with ASL World functionality"""
        print("Testing ASL World integration...")
        
        async with self.get_session() as session:
            service = ProgressService(session)
            user_id = str(uuid4())
            
            # Simulate ASL World practice session
            asl_world_config = {
                "session_type": "individual",
                "session_name": "ASL World Practice",
                "difficulty_level": "beginner",
                "skill_areas": ["fingerspelling", "basic_vocabulary"],
                "story_content": {
                    "title": "Daily Greetings",
                    "sentences": [
                        "Good morning",
                        "How are you?",
                        "Nice to meet you"
                    ],
                    "generated_by": "ai",
                    "difficulty": "beginner"
                },
                "total_sentences": 3,
                "session_data": {
                    "video_processing_enabled": True,
                    "mediapipe_config": {
                        "min_detection_confidence": 0.5,
                        "min_tracking_confidence": 0.5
                    }
                }
            }
            
            # Start session
            practice_session = await service.start_practice_session(user_id, asl_world_config)
            
            # Simulate MediaPipe gesture analysis results
            for i, sentence in enumerate(asl_world_config["story_content"]["sentences"]):
                # Simulate multiple attempts per sentence
                for attempt_num in range(1, 3):  # 2 attempts per sentence
                    attempt_data = {
                        "sentence_index": i,
                        "target_sentence": sentence,
                        "landmark_data": {
                            "hand_landmarks": [
                                [[0.1 + j*0.01, 0.2 + j*0.01, 0.3 + j*0.01] for j in range(21)]
                            ],
                            "pose_landmarks": [[0.5, 0.5, 0.5] for _ in range(33)]
                        },
                        "gesture_sequence": [
                            {
                                "gesture": f"sign_{i}_{attempt_num}",
                                "confidence": 0.8 + (attempt_num * 0.05),
                                "start_frame": 10,
                                "end_frame": 50,
                                "duration_ms": 1600
                            }
                        ],
                        "confidence_score": 0.75 + (attempt_num * 0.1),
                        "accuracy_score": 0.80 + (attempt_num * 0.05),
                        "fluency_score": 0.70 + (attempt_num * 0.08),
                        "ai_feedback": f"Attempt {attempt_num}: Good progress!",
                        "suggestions": [
                            "Keep your hand steady during the sign",
                            "Make sure your palm orientation is correct"
                        ],
                        "detected_errors": [] if attempt_num == 2 else [
                            {"type": "hand_shape", "severity": "minor", "description": "Slight finger positioning issue"}
                        ],
                        "duration_ms": 1800
                    }
                    
                    attempt = await service.record_sentence_attempt(
                        practice_session.id, attempt_data
                    )
                    assert attempt.landmark_data is not None
                    assert attempt.gesture_sequence is not None
                    assert len(attempt.suggestions) == 2
            
            # Complete session
            completion_data = {
                "performance_metrics": {
                    "total_video_frames": 300,
                    "processed_frames": 295,
                    "gesture_detection_accuracy": 0.85,
                    "average_processing_latency_ms": 45
                }
            }
            
            completed_session = await service.complete_practice_session(
                practice_session.id, completion_data
            )
            
            # Verify integration results
            assert completed_session.status == "completed"
            assert completed_session.sentences_completed == 3
            assert completed_session.performance_metrics["total_video_frames"] == 300
            
            # Check that user progress was updated
            progress_summary = await service.get_user_progress_summary(user_id)
            
            # Should have progress in both skill areas
            progress_records = progress_summary["progress_records"]
            skill_areas = {p["skill_area"] for p in progress_records}
            assert "fingerspelling" in skill_areas
            assert "basic_vocabulary" in skill_areas
            
            # Check analytics integration
            analytics = progress_summary["performance_analytics"]
            assert analytics["session_analytics"]["total_sessions"] == 1
            assert analytics["attempt_analytics"]["total_attempts"] == 6  # 3 sentences * 2 attempts
            
            await session.commit()
            
            print("✓ ASL World integration test passed")
    
    async def run_all_tests(self):
        """Run all tests"""
        print("Starting progress tracking tests...")
        
        try:
            await self.setup()
            
            await self.test_practice_session_model()
            await self.test_sentence_attempt_model()
            await self.test_user_progress_model()
            await self.test_progress_repository()
            await self.test_progress_service()
            await self.test_asl_world_integration()
            
            print("\n✅ All progress tracking tests passed!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        finally:
            await self.cleanup()


async def main():
    """Run the test suite"""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    test_suite = TestProgressTrackingSimple()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())