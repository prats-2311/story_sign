"""
Comprehensive tests for learning progress tracking functionality
Tests models, repository, service layer, and integration with existing ASL World
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Dict, Any

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from config import get_config
from models.base import Base
from models.progress import PracticeSession, SentenceAttempt, UserProgress
from repositories.progress_repository import ProgressRepository
from services.progress_service import ProgressService


class TestProgressTracking:
    """Test suite for progress tracking functionality"""
    
    @pytest.fixture(scope="class")
    async def engine(self):
        """Create test database engine"""
        config = get_config()
        db_config = config.database
        
        # Use test database
        test_db_url = db_config.get_connection_url(async_driver=True).replace(
            f"/{db_config.database}", "/storysign_test"
        )
        
        engine = create_async_engine(test_db_url, echo=False)
        
        # Create test database if it doesn't exist
        try:
            async with engine.begin() as conn:
                await conn.execute(text("CREATE DATABASE IF NOT EXISTS storysign_test"))
        except Exception:
            pass  # Database might already exist
        
        # Recreate engine with test database
        engine = create_async_engine(
            db_config.get_connection_url(async_driver=True).replace(
                f"/{db_config.database}", "/storysign_test"
            ),
            echo=False
        )
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        yield engine
        
        # Cleanup
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        await engine.dispose()
    
    @pytest.fixture
    async def session(self, engine):
        """Create test database session"""
        async_session = async_sessionmaker(engine, class_=AsyncSession)
        
        async with async_session() as session:
            yield session
            await session.rollback()
    
    @pytest.fixture
    async def repository(self, session):
        """Create progress repository"""
        return ProgressRepository(session)
    
    @pytest.fixture
    async def service(self, session):
        """Create progress service"""
        return ProgressService(session)
    
    @pytest.fixture
    def sample_user_id(self):
        """Generate sample user ID"""
        return str(uuid4())
    
    @pytest.fixture
    def sample_story_data(self):
        """Sample story data for testing"""
        return {
            "title": "Test Story",
            "sentences": [
                "Hello, my name is John.",
                "I am learning ASL.",
                "This is a practice session."
            ],
            "difficulty": "beginner"
        }
    
    # Model Tests
    
    async def test_practice_session_model(self, session, sample_user_id):
        """Test PracticeSession model creation and validation"""
        session_data = {
            "user_id": sample_user_id,
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
        assert session_obj.user_id == sample_user_id
        assert session_obj.session_type == "individual"
        assert session_obj.status == "active"
        assert session_obj.created_at is not None
        
        # Test completion percentage calculation
        session_obj.sentences_completed = 2
        assert session_obj.calculate_completion_percentage() == pytest.approx(66.67, rel=1e-2)
        
        # Test performance summary
        summary = session_obj.get_performance_summary()
        assert summary["session_id"] == session_obj.id
        assert summary["sentences_completed"] == 2
        assert summary["total_sentences"] == 3
    
    async def test_sentence_attempt_model(self, session, sample_user_id):
        """Test SentenceAttempt model creation and validation"""
        # Create practice session first
        practice_session = PracticeSession(
            user_id=sample_user_id,
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
        assert overall_score == pytest.approx(expected_score, rel=1e-3)
        
        # Test performance summary
        summary = attempt.get_performance_summary()
        assert summary["attempt_id"] == attempt.id
        assert summary["overall_score"] == pytest.approx(expected_score, rel=1e-3)
    
    async def test_user_progress_model(self, session, sample_user_id):
        """Test UserProgress model creation and validation"""
        progress_data = {
            "user_id": sample_user_id,
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
        assert progress.user_id == sample_user_id
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
    
    # Repository Tests
    
    async def test_create_practice_session(self, repository, sample_user_id, sample_story_data):
        """Test creating practice session through repository"""
        session_data = {
            "user_id": sample_user_id,
            "session_type": "individual",
            "story_content": sample_story_data,
            "difficulty_level": "beginner",
            "total_sentences": len(sample_story_data["sentences"]),
            "skill_areas": ["vocabulary", "grammar"]
        }
        
        session = await repository.create_practice_session(session_data)
        
        assert session.id is not None
        assert session.user_id == sample_user_id
        assert session.session_type == "individual"
        assert session.difficulty_level == "beginner"
        assert session.total_sentences == 3
        assert session.skill_areas == ["vocabulary", "grammar"]
    
    async def test_record_sentence_attempts(self, repository, sample_user_id):
        """Test recording sentence attempts"""
        # Create session
        session_data = {
            "user_id": sample_user_id,
            "session_type": "individual",
            "total_sentences": 2
        }
        session = await repository.create_practice_session(session_data)
        
        # Record first attempt
        attempt_data = {
            "session_id": session.id,
            "sentence_index": 0,
            "target_sentence": "Hello world",
            "confidence_score": 0.8,
            "accuracy_score": 0.9,
            "fluency_score": 0.7,
            "duration_ms": 2500
        }
        
        attempt = await repository.create_sentence_attempt(attempt_data)
        
        assert attempt.id is not None
        assert attempt.session_id == session.id
        assert attempt.sentence_index == 0
        assert attempt.attempt_number == 1
        
        # Record second attempt for same sentence
        attempt_data["attempt_number"] = 2
        attempt_data["confidence_score"] = 0.85
        
        attempt2 = await repository.create_sentence_attempt(attempt_data)
        assert attempt2.attempt_number == 2
        
        # Get all attempts for session
        attempts = await repository.get_session_attempts(session.id)
        assert len(attempts) == 2
    
    async def test_user_progress_tracking(self, repository, sample_user_id):
        """Test user progress creation and updates"""
        skill_area = "vocabulary"
        
        # Get or create progress
        progress = await repository.get_or_create_user_progress(
            sample_user_id, skill_area, "basic_vocabulary"
        )
        
        assert progress.user_id == sample_user_id
        assert progress.skill_area == skill_area
        assert progress.skill_category == "basic_vocabulary"
        assert progress.current_level == 0.0
        
        # Update progress with session data
        session_data = {
            "duration_seconds": 300,
            "total_attempts": 10,
            "successful_attempts": 8,
            "average_score": 0.85,
            "average_confidence": 0.80,
            "experience_gained": 25.0
        }
        
        updated_progress = await repository.update_user_progress(
            sample_user_id, skill_area, session_data
        )
        
        assert updated_progress.total_sessions == 1
        assert updated_progress.total_practice_time == 300
        assert updated_progress.total_attempts == 10
        assert updated_progress.successful_attempts == 8
        assert updated_progress.experience_points == 25.0
        assert updated_progress.current_level > 0.0  # Should increase with experience
    
    async def test_performance_analytics(self, repository, sample_user_id):
        """Test performance analytics queries"""
        # Create test data
        session_data = {
            "user_id": sample_user_id,
            "session_type": "individual",
            "overall_score": 0.85,
            "sentences_completed": 3,
            "duration_seconds": 600,
            "status": "completed"
        }
        session = await repository.create_practice_session(session_data)
        
        # Add some attempts
        for i in range(3):
            attempt_data = {
                "session_id": session.id,
                "sentence_index": i,
                "target_sentence": f"Sentence {i+1}",
                "confidence_score": 0.8 + (i * 0.05),
                "accuracy_score": 0.85 + (i * 0.03),
                "fluency_score": 0.75 + (i * 0.04),
                "is_successful": True
            }
            await repository.create_sentence_attempt(attempt_data)
        
        # Get analytics
        analytics = await repository.get_user_performance_analytics(sample_user_id)
        
        assert analytics["user_id"] == sample_user_id
        assert analytics["session_analytics"]["total_sessions"] == 1
        assert analytics["session_analytics"]["completed_sessions"] == 1
        assert analytics["session_analytics"]["total_practice_time"] == 600
        assert analytics["attempt_analytics"]["total_attempts"] == 3
        assert analytics["attempt_analytics"]["successful_attempts"] == 3
        assert analytics["attempt_analytics"]["success_rate"] == 100.0
    
    # Service Layer Tests
    
    async def test_start_practice_session(self, service, sample_user_id, sample_story_data):
        """Test starting practice session through service"""
        session_config = {
            "session_type": "individual",
            "story_content": sample_story_data,
            "difficulty_level": "beginner",
            "total_sentences": len(sample_story_data["sentences"]),
            "skill_areas": ["vocabulary", "grammar"]
        }
        
        session = await service.start_practice_session(sample_user_id, session_config)
        
        assert session.id is not None
        assert session.user_id == sample_user_id
        assert session.status == "active"
        assert session.started_at is not None
        assert session.story_content == sample_story_data
    
    async def test_record_sentence_attempt_with_service(self, service, sample_user_id):
        """Test recording sentence attempt through service"""
        # Start session
        session_config = {
            "session_type": "individual",
            "total_sentences": 1
        }
        session = await service.start_practice_session(sample_user_id, session_config)
        
        # Record attempt
        attempt_data = {
            "sentence_index": 0,
            "target_sentence": "Hello world",
            "landmark_data": {"hand_landmarks": [[0.1, 0.2, 0.3]]},
            "confidence_score": 0.85,
            "accuracy_score": 0.90,
            "fluency_score": 0.80,
            "ai_feedback": "Good job! Try to keep your hand steady.",
            "duration_ms": 2000
        }
        
        attempt = await service.record_sentence_attempt(session.id, attempt_data)
        
        assert attempt.id is not None
        assert attempt.session_id == session.id
        assert attempt.sentence_index == 0
        assert attempt.attempt_number == 1
        assert attempt.is_successful is True  # Score > 0.7
        assert attempt.ai_feedback == "Good job! Try to keep your hand steady."
    
    async def test_complete_practice_session(self, service, sample_user_id):
        """Test completing practice session and updating progress"""
        # Start session
        session_config = {
            "session_type": "individual",
            "difficulty_level": "intermediate",
            "total_sentences": 2,
            "skill_areas": ["vocabulary"]
        }
        session = await service.start_practice_session(sample_user_id, session_config)
        
        # Record some attempts
        for i in range(2):
            attempt_data = {
                "sentence_index": i,
                "target_sentence": f"Test sentence {i+1}",
                "confidence_score": 0.8,
                "accuracy_score": 0.85,
                "fluency_score": 0.75,
                "duration_ms": 2000
            }
            await service.record_sentence_attempt(session.id, attempt_data)
        
        # Complete session
        completed_session = await service.complete_practice_session(session.id)
        
        assert completed_session.status == "completed"
        assert completed_session.completed_at is not None
        assert completed_session.overall_score > 0
        assert completed_session.sentences_completed == 2
    
    async def test_user_progress_summary(self, service, sample_user_id):
        """Test getting comprehensive user progress summary"""
        # Create some practice data
        session_config = {
            "session_type": "individual",
            "difficulty_level": "beginner",
            "total_sentences": 1,
            "skill_areas": ["vocabulary"]
        }
        session = await service.start_practice_session(sample_user_id, session_config)
        
        attempt_data = {
            "sentence_index": 0,
            "target_sentence": "Test sentence",
            "confidence_score": 0.8,
            "accuracy_score": 0.85,
            "fluency_score": 0.75
        }
        await service.record_sentence_attempt(session.id, attempt_data)
        await service.complete_practice_session(session.id)
        
        # Get progress summary
        summary = await service.get_user_progress_summary(sample_user_id)
        
        assert summary["user_id"] == sample_user_id
        assert "progress_records" in summary
        assert "performance_analytics" in summary
        assert "learning_trends" in summary
        assert "overall_summary" in summary
        
        # Check overall summary
        overall = summary["overall_summary"]
        assert overall["total_skill_areas"] >= 1
        assert overall["total_sessions"] >= 1
        assert overall["proficiency_level"] in ["beginner", "intermediate", "advanced"]
    
    # Integration Tests with ASL World
    
    async def test_asl_world_integration(self, service, sample_user_id):
        """Test integration with existing ASL World functionality"""
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
        session = await service.start_practice_session(sample_user_id, asl_world_config)
        
        # Simulate MediaPipe gesture analysis results
        for i, sentence in enumerate(asl_world_config["story_content"]["sentences"]):
            # Simulate multiple attempts per sentence (realistic scenario)
            for attempt_num in range(1, 3):  # 2 attempts per sentence
                attempt_data = {
                    "sentence_index": i,
                    "target_sentence": sentence,
                    "landmark_data": {
                        "hand_landmarks": [
                            [[0.1 + j*0.01, 0.2 + j*0.01, 0.3 + j*0.01] for j in range(21)]
                        ],
                        "pose_landmarks": [[0.5, 0.5, 0.5] for _ in range(33)],
                        "face_landmarks": [[0.4, 0.4, 0.4] for _ in range(468)]
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
                    "ai_feedback": f"Attempt {attempt_num}: Good progress! Focus on hand shape clarity.",
                    "suggestions": [
                        "Keep your hand steady during the sign",
                        "Make sure your palm orientation is correct"
                    ],
                    "detected_errors": [] if attempt_num == 2 else [
                        {"type": "hand_shape", "severity": "minor", "description": "Slight finger positioning issue"}
                    ],
                    "duration_ms": 1800,
                    "video_start_frame": 10 + (i * 100),
                    "video_end_frame": 60 + (i * 100)
                }
                
                attempt = await service.record_sentence_attempt(session.id, attempt_data)
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
            session.id, completion_data
        )
        
        # Verify integration results
        assert completed_session.status == "completed"
        assert completed_session.sentences_completed == 3
        assert completed_session.performance_metrics["total_video_frames"] == 300
        
        # Check that user progress was updated
        progress_summary = await service.get_user_progress_summary(sample_user_id)
        
        # Should have progress in both skill areas
        progress_records = progress_summary["progress_records"]
        skill_areas = {p["skill_area"] for p in progress_records}
        assert "fingerspelling" in skill_areas
        assert "basic_vocabulary" in skill_areas
        
        # Check analytics integration
        analytics = progress_summary["performance_analytics"]
        assert analytics["session_analytics"]["total_sessions"] == 1
        assert analytics["attempt_analytics"]["total_attempts"] == 6  # 3 sentences * 2 attempts
        
        # Verify learning trends
        trends = progress_summary["learning_trends"]
        assert trends["total_active_days"] >= 1
        assert len(trends["daily_activity"]) >= 1
    
    # Performance and Edge Case Tests
    
    async def test_large_session_performance(self, service, sample_user_id):
        """Test performance with large number of attempts"""
        # Create session with many sentences
        session_config = {
            "session_type": "individual",
            "total_sentences": 50,
            "skill_areas": ["vocabulary"]
        }
        session = await service.start_practice_session(sample_user_id, session_config)
        
        # Record many attempts
        import time
        start_time = time.time()
        
        for i in range(50):
            attempt_data = {
                "sentence_index": i,
                "target_sentence": f"Sentence {i+1}",
                "confidence_score": 0.7 + (i % 10) * 0.02,
                "accuracy_score": 0.75 + (i % 10) * 0.015,
                "fluency_score": 0.65 + (i % 10) * 0.025
            }
            await service.record_sentence_attempt(session.id, attempt_data)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete within reasonable time (< 5 seconds for 50 attempts)
        assert processing_time < 5.0
        
        # Complete session
        completed_session = await service.complete_practice_session(session.id)
        assert completed_session.sentences_completed == 50
    
    async def test_concurrent_sessions(self, service):
        """Test handling multiple concurrent sessions"""
        user_ids = [str(uuid4()) for _ in range(3)]
        sessions = []
        
        # Start multiple sessions concurrently
        for user_id in user_ids:
            session_config = {
                "session_type": "individual",
                "total_sentences": 2,
                "skill_areas": ["vocabulary"]
            }
            session = await service.start_practice_session(user_id, session_config)
            sessions.append((user_id, session))
        
        # Record attempts for all sessions
        for user_id, session in sessions:
            for i in range(2):
                attempt_data = {
                    "sentence_index": i,
                    "target_sentence": f"User {user_id[:8]} sentence {i+1}",
                    "confidence_score": 0.8,
                    "accuracy_score": 0.85,
                    "fluency_score": 0.75
                }
                await service.record_sentence_attempt(session.id, attempt_data)
        
        # Complete all sessions
        for user_id, session in sessions:
            completed_session = await service.complete_practice_session(session.id)
            assert completed_session.status == "completed"
            assert completed_session.user_id == user_id
    
    async def test_error_handling(self, service, sample_user_id):
        """Test error handling and edge cases"""
        # Test invalid session ID
        with pytest.raises(ValueError):
            await service.complete_practice_session("invalid-session-id")
        
        # Test invalid attempt data
        session_config = {"session_type": "individual", "total_sentences": 1}
        session = await service.start_practice_session(sample_user_id, session_config)
        
        # Missing required fields should raise error
        with pytest.raises(Exception):
            await service.record_sentence_attempt(session.id, {})
        
        # Invalid score ranges should be handled
        attempt_data = {
            "sentence_index": 0,
            "target_sentence": "Test",
            "confidence_score": 1.5,  # Invalid: > 1.0
            "accuracy_score": -0.1,   # Invalid: < 0.0
            "fluency_score": 0.8
        }
        
        # Should either raise validation error or clamp values
        try:
            attempt = await service.record_sentence_attempt(session.id, attempt_data)
            # If no error, values should be clamped
            assert 0.0 <= attempt.confidence_score <= 1.0
            assert 0.0 <= attempt.accuracy_score <= 1.0
        except ValueError:
            # Validation error is acceptable
            pass


# Run tests
if __name__ == "__main__":
    import sys
    import logging
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run specific test or all tests
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        pytest.main([f"-v", f"-k", test_name, __file__])
    else:
        pytest.main(["-v", __file__])