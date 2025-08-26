"""
Pytest-based tests for learning progress tracking functionality
Follows StorySign testing standards with proper mocking and performance benchmarks
"""

import pytest
import asyncio
import time
import tempfile
import os
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

# Set up path for imports
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.base import Base
from models.progress import PracticeSession, SentenceAttempt, UserProgress
from repositories.progress_repository import ProgressRepository
from services.progress_service import ProgressService


class TestProgressTrackingModels:
    """Unit tests for progress tracking models"""
    
    def test_practice_session_creation(self):
        """Test PracticeSession model creation and validation"""
        user_id = str(uuid4())
        
        session = PracticeSession(
            user_id=user_id,
            session_type="individual",
            difficulty_level="beginner",
            total_sentences=5,
            sentences_completed=3,
            overall_score=0.85,
            status="active"
        )
        
        assert session.user_id == user_id
        assert session.session_type == "individual"
        assert session.difficulty_level == "beginner"
        assert session.total_sentences == 5
        assert session.sentences_completed == 3
        assert session.overall_score == 0.85
        assert session.status == "active"
    
    def test_practice_session_completion_percentage(self):
        """Test completion percentage calculation"""
        session = PracticeSession(
            user_id=str(uuid4()),
            total_sentences=10,
            sentences_completed=7
        )
        
        completion_pct = session.calculate_completion_percentage()
        assert completion_pct == 70.0
        
        # Test with no total sentences
        session.total_sentences = None
        assert session.calculate_completion_percentage() is None
    
    def test_practice_session_duration_calculation(self):
        """Test duration calculation"""
        session = PracticeSession(user_id=str(uuid4()))
        
        # Test with both timestamps
        session.started_at = datetime.now() - timedelta(minutes=5)
        session.completed_at = datetime.now()
        
        duration = session.calculate_duration()
        assert 290 <= duration <= 310  # ~300 seconds with some tolerance
        
        # Test with missing completed_at
        session.completed_at = None
        assert session.calculate_duration() is None
    
    def test_practice_session_performance_summary(self):
        """Test performance summary generation"""
        session_id = str(uuid4())
        session = PracticeSession(
            id=session_id,
            user_id=str(uuid4()),
            sentences_completed=3,
            total_sentences=5,
            overall_score=0.85,
            status="completed",
            difficulty_level="intermediate",
            skill_areas=["vocabulary", "grammar"]
        )
        
        summary = session.get_performance_summary()
        
        assert summary["session_id"] == session_id
        assert summary["sentences_completed"] == 3
        assert summary["total_sentences"] == 5
        assert summary["overall_score"] == 0.85
        assert summary["status"] == "completed"
        assert summary["difficulty_level"] == "intermediate"
        assert summary["skill_areas"] == ["vocabulary", "grammar"]
    
    def test_sentence_attempt_creation(self):
        """Test SentenceAttempt model creation"""
        session_id = str(uuid4())
        
        attempt = SentenceAttempt(
            session_id=session_id,
            sentence_index=0,
            target_sentence="Hello, my name is John.",
            confidence_score=0.85,
            accuracy_score=0.90,
            fluency_score=0.75,
            attempt_number=1,
            duration_ms=2500,
            is_successful=True
        )
        
        assert attempt.session_id == session_id
        assert attempt.sentence_index == 0
        assert attempt.target_sentence == "Hello, my name is John."
        assert attempt.confidence_score == 0.85
        assert attempt.accuracy_score == 0.90
        assert attempt.fluency_score == 0.75
        assert attempt.attempt_number == 1
        assert attempt.duration_ms == 2500
        assert attempt.is_successful is True
    
    def test_sentence_attempt_overall_score_calculation(self):
        """Test overall score calculation with weighted average"""
        attempt = SentenceAttempt(
            session_id=str(uuid4()),
            sentence_index=0,
            target_sentence="Test sentence",
            confidence_score=0.85,
            accuracy_score=0.90,
            fluency_score=0.75,
            attempt_number=1
        )
        
        overall_score = attempt.get_overall_score()
        expected_score = 0.90 * 0.4 + 0.85 * 0.3 + 0.75 * 0.3  # Weighted average
        assert abs(overall_score - expected_score) < 0.001
        
        # Test with missing scores
        attempt_partial = SentenceAttempt(
            session_id=str(uuid4()),
            sentence_index=1,
            target_sentence="Test sentence",
            confidence_score=0.8,
            accuracy_score=None,
            fluency_score=0.7,
            attempt_number=1
        )
        
        partial_score = attempt_partial.get_overall_score()
        expected_partial = (0.8 + 0.7) / 2  # Simple average
        assert abs(partial_score - expected_partial) < 0.001
        
        # Test with no scores
        attempt_no_scores = SentenceAttempt(
            session_id=str(uuid4()),
            sentence_index=2,
            target_sentence="No scores",
            attempt_number=1
        )
        
        assert attempt_no_scores.get_overall_score() is None
    
    def test_user_progress_creation(self):
        """Test UserProgress model creation"""
        user_id = str(uuid4())
        
        progress = UserProgress(
            user_id=user_id,
            skill_area="fingerspelling",
            skill_category="basic_vocabulary",
            current_level=2.5,
            experience_points=150.0,
            total_practice_time=3600,
            total_sessions=5,
            total_attempts=25,
            successful_attempts=20,
            average_score=0.82,
            learning_streak=3,
            longest_streak=5
        )
        
        assert progress.user_id == user_id
        assert progress.skill_area == "fingerspelling"
        assert progress.skill_category == "basic_vocabulary"
        assert progress.current_level == 2.5
        assert progress.experience_points == 150.0
        assert progress.total_practice_time == 3600
        assert progress.total_sessions == 5
        assert progress.total_attempts == 25
        assert progress.successful_attempts == 20
        assert progress.average_score == 0.82
        assert progress.learning_streak == 3
        assert progress.longest_streak == 5
    
    def test_user_progress_calculations(self):
        """Test UserProgress calculation methods"""
        progress = UserProgress(
            user_id=str(uuid4()),
            skill_area="vocabulary",
            current_level=2.7,
            total_attempts=50,
            successful_attempts=40
        )
        
        # Test success rate calculation
        success_rate = progress.calculate_success_rate()
        assert success_rate == 80.0  # 40/50 * 100
        
        # Test level progress calculation
        level_progress = progress.calculate_level_progress()
        assert abs(level_progress - 0.7) < 0.001  # 2.7 - 2 = 0.7 (with floating point tolerance)
        
        # Test next milestone
        next_milestone = progress.get_next_milestone()
        assert next_milestone == 3.0
        
        # Test at max level
        progress.current_level = 10.0
        assert progress.get_next_milestone() is None
    
    def test_user_progress_milestone_management(self):
        """Test milestone addition and management"""
        progress = UserProgress(
            user_id=str(uuid4()),
            skill_area="grammar"
        )
        
        # Add milestone
        progress.add_milestone(1.0, "First milestone")
        assert len(progress.milestones) == 1
        assert progress.milestones[0]["level"] == 1.0
        assert progress.milestones[0]["description"] == "First milestone"
        assert "achieved_at" in progress.milestones[0]
        
        # Add another milestone
        progress.add_milestone(2.0, "Second milestone")
        assert len(progress.milestones) == 2
    
    def test_user_progress_streak_management(self):
        """Test learning streak updates"""
        progress = UserProgress(
            user_id=str(uuid4()),
            skill_area="fluency",
            learning_streak=0,
            longest_streak=0
        )
        
        today = datetime.now()
        
        # First practice (no previous date)
        progress.update_streak(today)
        assert progress.learning_streak == 1
        assert progress.longest_streak == 1
        
        # Consecutive day practice
        tomorrow = today + timedelta(days=1)
        progress.update_streak(tomorrow)
        assert progress.learning_streak == 2
        assert progress.longest_streak == 2
        
        # Skip a day (streak broken)
        day_after_tomorrow = tomorrow + timedelta(days=2)
        progress.update_streak(day_after_tomorrow)
        assert progress.learning_streak == 1  # Reset to 1
        assert progress.longest_streak == 2   # Keeps previous max
        
        # Same day practice (no change)
        progress.update_streak(day_after_tomorrow)
        assert progress.learning_streak == 1  # No change
        assert progress.longest_streak == 2   # No change


@pytest_asyncio.fixture
async def test_db_engine():
    """Create test database engine using SQLite"""
    # Create temporary SQLite database
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_file.close()
    
    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_file.name}",
        echo=False
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    await engine.dispose()
    os.unlink(db_file.name)


@pytest_asyncio.fixture
async def test_db_session(test_db_engine):
    """Create test database session"""
    async_session = async_sessionmaker(test_db_engine, class_=AsyncSession)
    
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest.fixture
def mock_mediapipe_data():
    """Mock MediaPipe landmark data"""
    return {
        "hand_landmarks": [
            [[0.1 + i*0.01, 0.2 + i*0.01, 0.3 + i*0.01] for i in range(21)],  # Right hand
            [[0.4 + i*0.01, 0.5 + i*0.01, 0.6 + i*0.01] for i in range(21)]   # Left hand
        ],
        "pose_landmarks": [[0.5, 0.5, 0.5] for _ in range(33)],
        "face_landmarks": [[0.45, 0.45, 0.45] for _ in range(468)],
        "timestamp": datetime.now().isoformat(),
        "detection_confidence": 0.85
    }


@pytest.fixture
def mock_ollama_service():
    """Mock Ollama service for story generation"""
    # Since OllamaService is not imported in progress_service, we'll skip this mock
    # The progress service doesn't directly depend on Ollama
    return Mock()


class TestProgressRepository:
    """Integration tests for ProgressRepository"""
    
    @pytest.mark.asyncio
    async def test_create_practice_session(self, test_db_session):
        """Test creating practice session through repository"""
        repository = ProgressRepository(test_db_session)
        user_id = str(uuid4())
        
        session_data = {
            "user_id": user_id,
            "session_type": "individual",
            "difficulty_level": "beginner",
            "total_sentences": 3,
            "skill_areas": ["vocabulary", "grammar"]
        }
        
        session = await repository.create_practice_session(session_data)
        
        assert session.id is not None
        assert session.user_id == user_id
        assert session.session_type == "individual"
        assert session.difficulty_level == "beginner"
        assert session.total_sentences == 3
        assert session.skill_areas == ["vocabulary", "grammar"]
    
    @pytest.mark.asyncio
    async def test_create_sentence_attempt(self, test_db_session):
        """Test creating sentence attempt through repository"""
        repository = ProgressRepository(test_db_session)
        user_id = str(uuid4())
        
        # Create session first
        session_data = {
            "user_id": user_id,
            "session_type": "individual",
            "total_sentences": 1
        }
        session = await repository.create_practice_session(session_data)
        
        # Create attempt
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
        assert attempt.confidence_score == 0.8
        assert attempt.accuracy_score == 0.9
        assert attempt.fluency_score == 0.7
        assert attempt.duration_ms == 2500
    
    @pytest.mark.asyncio
    async def test_user_progress_operations(self, test_db_session):
        """Test user progress creation and updates"""
        repository = ProgressRepository(test_db_session)
        user_id = str(uuid4())
        skill_area = "vocabulary"
        
        # Get or create progress
        progress = await repository.get_or_create_user_progress(
            user_id, skill_area, "basic_vocabulary"
        )
        
        assert progress.user_id == user_id
        assert progress.skill_area == skill_area
        assert progress.skill_category == "basic_vocabulary"
        assert progress.current_level == 0.0
        
        # Update progress
        session_data = {
            "duration_seconds": 300,
            "total_attempts": 10,
            "successful_attempts": 8,
            "average_score": 0.85,
            "experience_gained": 25.0
        }
        
        updated_progress = await repository.update_user_progress(
            user_id, skill_area, session_data
        )
        
        assert updated_progress.total_sessions == 1
        assert updated_progress.total_practice_time == 300
        assert updated_progress.total_attempts == 10
        assert updated_progress.successful_attempts == 8
        assert updated_progress.experience_points == 25.0
        assert updated_progress.current_level > 0.0


class TestProgressService:
    """Integration tests for ProgressService"""
    
    @pytest.mark.asyncio
    async def test_start_practice_session(self, test_db_session, mock_ollama_service):
        """Test starting practice session through service"""
        service = ProgressService(test_db_session)
        user_id = str(uuid4())
        
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
        
        session = await service.start_practice_session(user_id, session_config)
        
        assert session.id is not None
        assert session.user_id == user_id
        assert session.status == "active"
        assert session.story_content == story_data
        assert session.skill_areas == ["vocabulary", "grammar"]
    
    @pytest.mark.asyncio
    async def test_record_sentence_attempt(self, test_db_session, mock_mediapipe_data):
        """Test recording sentence attempt through service"""
        service = ProgressService(test_db_session)
        user_id = str(uuid4())
        
        # Start session
        session_config = {
            "session_type": "individual",
            "total_sentences": 1,
            "skill_areas": ["vocabulary"]
        }
        session = await service.start_practice_session(user_id, session_config)
        
        # Record attempt
        attempt_data = {
            "sentence_index": 0,
            "target_sentence": "Hello world",
            "landmark_data": mock_mediapipe_data,
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
        assert attempt.landmark_data == mock_mediapipe_data
    
    @pytest.mark.asyncio
    async def test_complete_practice_session(self, test_db_session):
        """Test completing practice session and updating progress"""
        service = ProgressService(test_db_session)
        user_id = str(uuid4())
        
        # Start session
        session_config = {
            "session_type": "individual",
            "difficulty_level": "intermediate",
            "total_sentences": 2,
            "skill_areas": ["vocabulary"]
        }
        session = await service.start_practice_session(user_id, session_config)
        
        # Record attempts
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


class TestPerformanceRequirements:
    """Performance tests to verify <100ms latency requirements"""
    
    @pytest.mark.asyncio
    async def test_session_creation_performance(self, test_db_session):
        """Test session creation meets performance requirements"""
        repository = ProgressRepository(test_db_session)
        user_id = str(uuid4())
        
        session_data = {
            "user_id": user_id,
            "session_type": "individual",
            "difficulty_level": "beginner",
            "total_sentences": 5,
            "skill_areas": ["vocabulary", "grammar"]
        }
        
        start_time = time.time()
        session = await repository.create_practice_session(session_data)
        end_time = time.time()
        
        latency_ms = (end_time - start_time) * 1000
        
        assert session.id is not None
        assert latency_ms < 100, f"Session creation took {latency_ms:.2f}ms, should be <100ms"
    
    @pytest.mark.asyncio
    async def test_attempt_recording_performance(self, test_db_session, mock_mediapipe_data):
        """Test sentence attempt recording meets performance requirements"""
        repository = ProgressRepository(test_db_session)
        user_id = str(uuid4())
        
        # Create session first
        session_data = {
            "user_id": user_id,
            "session_type": "individual",
            "total_sentences": 1
        }
        session = await repository.create_practice_session(session_data)
        
        # Test attempt recording performance
        attempt_data = {
            "session_id": session.id,
            "sentence_index": 0,
            "target_sentence": "Performance test sentence",
            "landmark_data": mock_mediapipe_data,
            "confidence_score": 0.8,
            "accuracy_score": 0.9,
            "fluency_score": 0.7,
            "duration_ms": 2500
        }
        
        start_time = time.time()
        attempt = await repository.create_sentence_attempt(attempt_data)
        end_time = time.time()
        
        latency_ms = (end_time - start_time) * 1000
        
        assert attempt.id is not None
        assert latency_ms < 100, f"Attempt recording took {latency_ms:.2f}ms, should be <100ms"
    
    @pytest.mark.asyncio
    async def test_progress_update_performance(self, test_db_session):
        """Test progress update meets performance requirements"""
        repository = ProgressRepository(test_db_session)
        user_id = str(uuid4())
        skill_area = "vocabulary"
        
        # Create initial progress
        await repository.get_or_create_user_progress(user_id, skill_area)
        
        # Test progress update performance
        session_data = {
            "duration_seconds": 300,
            "total_attempts": 10,
            "successful_attempts": 8,
            "average_score": 0.85,
            "experience_gained": 25.0
        }
        
        start_time = time.time()
        updated_progress = await repository.update_user_progress(
            user_id, skill_area, session_data
        )
        end_time = time.time()
        
        latency_ms = (end_time - start_time) * 1000
        
        assert updated_progress.total_sessions == 1
        assert latency_ms < 100, f"Progress update took {latency_ms:.2f}ms, should be <100ms"
    
    @pytest.mark.asyncio
    async def test_analytics_query_performance(self, test_db_session):
        """Test analytics queries meet performance requirements"""
        repository = ProgressRepository(test_db_session)
        user_id = str(uuid4())
        
        # Create some test data
        session_data = {
            "user_id": user_id,
            "session_type": "individual",
            "overall_score": 0.85,
            "sentences_completed": 3,
            "duration_seconds": 300,
            "status": "completed"
        }
        session = await repository.create_practice_session(session_data)
        
        # Add attempt
        attempt_data = {
            "session_id": session.id,
            "sentence_index": 0,
            "target_sentence": "Analytics test",
            "confidence_score": 0.8,
            "accuracy_score": 0.85,
            "fluency_score": 0.75,
            "is_successful": True
        }
        await repository.create_sentence_attempt(attempt_data)
        
        # Test analytics query performance
        start_time = time.time()
        analytics = await repository.get_user_performance_analytics(user_id)
        end_time = time.time()
        
        latency_ms = (end_time - start_time) * 1000
        
        assert analytics["user_id"] == user_id
        assert analytics["session_analytics"]["total_sessions"] == 1
        assert latency_ms < 100, f"Analytics query took {latency_ms:.2f}ms, should be <100ms"


class TestASLWorldIntegration:
    """End-to-end tests for ASL World integration"""
    
    @pytest.mark.asyncio
    async def test_complete_asl_world_workflow(self, test_db_session, mock_mediapipe_data, mock_ollama_service):
        """Test complete ASL World practice workflow with progress tracking"""
        service = ProgressService(test_db_session)
        user_id = str(uuid4())
        
        # Simulate ASL World session configuration
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
        session = await service.start_practice_session(user_id, asl_world_config)
        
        # Simulate practicing each sentence
        for i, sentence in enumerate(asl_world_config["story_content"]["sentences"]):
            # Simulate multiple attempts per sentence
            for attempt_num in range(1, 3):  # 2 attempts per sentence
                attempt_data = {
                    "sentence_index": i,
                    "target_sentence": sentence,
                    "landmark_data": mock_mediapipe_data,
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


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main(["-v", __file__])