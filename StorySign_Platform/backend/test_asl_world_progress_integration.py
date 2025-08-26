"""
Integration test for progress tracking with existing ASL World functionality
Tests the complete flow from video processing to progress tracking
"""

import asyncio
import json
import logging
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from config import get_config
from models.base import Base
from services.progress_service import ProgressService
from core.db import get_db_session

logger = logging.getLogger(__name__)


class TestASLWorldProgressIntegration:
    """Integration tests for ASL World and progress tracking"""
    
    @pytest.fixture(scope="class")
    async def setup_test_db(self):
        """Set up test database"""
        config = get_config()
        db_config = config.database
        
        # Create test database engine
        test_db_url = db_config.get_connection_url(async_driver=True).replace(
            f"/{db_config.database}", "/storysign_integration_test"
        )
        
        engine = create_async_engine(test_db_url, echo=False)
        
        # Create test database
        try:
            async with engine.begin() as conn:
                await conn.execute(text("CREATE DATABASE IF NOT EXISTS storysign_integration_test"))
        except Exception:
            pass
        
        # Recreate engine with test database
        engine = create_async_engine(
            db_config.get_connection_url(async_driver=True).replace(
                f"/{db_config.database}", "/storysign_integration_test"
            ),
            echo=False
        )
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        yield engine
        
        # Cleanup
        await engine.dispose()
    
    @pytest.fixture
    async def db_session(self, setup_test_db):
        """Create database session for tests"""
        async_session = async_sessionmaker(setup_test_db, class_=AsyncSession)
        
        async with async_session() as session:
            yield session
            await session.rollback()
    
    @pytest.fixture
    def sample_user_id(self):
        """Generate sample user ID"""
        return str(uuid4())
    
    @pytest.fixture
    def asl_world_story_data(self):
        """Sample ASL World story data"""
        return {
            "title": "Morning Routine",
            "sentences": [
                "Good morning, how are you?",
                "I brush my teeth every day.",
                "Then I eat breakfast.",
                "After that, I go to work.",
                "Have a great day!"
            ],
            "difficulty": "intermediate",
            "generated_by": "ai",
            "metadata": {
                "topic": "daily_routine",
                "vocabulary_level": "intermediate",
                "estimated_duration_minutes": 5
            }
        }
    
    @pytest.fixture
    def mediapipe_landmark_data(self):
        """Sample MediaPipe landmark data"""
        return {
            "hand_landmarks": [
                # Right hand landmarks (21 points)
                [[0.1 + i*0.01, 0.2 + i*0.01, 0.3 + i*0.01] for i in range(21)],
                # Left hand landmarks (21 points)
                [[0.4 + i*0.01, 0.5 + i*0.01, 0.6 + i*0.01] for i in range(21)]
            ],
            "pose_landmarks": [
                # Pose landmarks (33 points)
                [0.5 + i*0.005, 0.5 + i*0.005, 0.5 + i*0.005] for i in range(33)
            ],
            "face_landmarks": [
                # Face landmarks (468 points) - simplified for testing
                [0.45 + (i%10)*0.01, 0.45 + (i%10)*0.01, 0.45] for i in range(468)
            ]
        }
    
    async def test_complete_asl_world_session_flow(
        self, 
        db_session, 
        sample_user_id, 
        asl_world_story_data, 
        mediapipe_landmark_data
    ):
        """Test complete ASL World session with progress tracking"""
        service = ProgressService(db_session)
        
        # 1. Start ASL World practice session
        session_config = {
            "session_type": "individual",
            "session_name": "ASL World - Morning Routine Practice",
            "story_content": asl_world_story_data,
            "difficulty_level": asl_world_story_data["difficulty"],
            "total_sentences": len(asl_world_story_data["sentences"]),
            "skill_areas": ["vocabulary", "grammar", "fluency"],
            "session_data": {
                "module": "asl_world",
                "video_processing_enabled": True,
                "mediapipe_config": {
                    "min_detection_confidence": 0.5,
                    "min_tracking_confidence": 0.5,
                    "model_complexity": 1
                },
                "ai_feedback_enabled": True,
                "story_metadata": asl_world_story_data["metadata"]
            }
        }
        
        session = await service.start_practice_session(sample_user_id, session_config)
        
        assert session.id is not None
        assert session.user_id == sample_user_id
        assert session.session_type == "individual"
        assert session.status == "active"
        assert session.story_content == asl_world_story_data
        assert session.skill_areas == ["vocabulary", "grammar", "fluency"]
        
        logger.info(f"Started ASL World session {session.id}")
        
        # 2. Simulate practicing each sentence with realistic attempts
        total_attempts = 0
        successful_attempts = 0
        
        for sentence_idx, sentence in enumerate(asl_world_story_data["sentences"]):
            # Simulate 1-3 attempts per sentence (realistic user behavior)
            num_attempts = 1 if sentence_idx < 2 else 2  # More attempts for later sentences
            
            for attempt_num in range(1, num_attempts + 1):
                # Simulate gesture analysis results
                # First attempts typically have lower scores, improvements on retries
                base_confidence = 0.65 + (sentence_idx * 0.05) + (attempt_num * 0.1)
                base_accuracy = 0.70 + (sentence_idx * 0.04) + (attempt_num * 0.08)
                base_fluency = 0.60 + (sentence_idx * 0.06) + (attempt_num * 0.12)
                
                # Add some realistic variation
                import random
                confidence_score = min(1.0, base_confidence + random.uniform(-0.1, 0.1))
                accuracy_score = min(1.0, base_accuracy + random.uniform(-0.08, 0.08))
                fluency_score = min(1.0, base_fluency + random.uniform(-0.12, 0.12))
                
                # Generate AI feedback based on performance
                overall_score = (accuracy_score * 0.4 + confidence_score * 0.3 + fluency_score * 0.3)
                
                if overall_score >= 0.8:
                    feedback = "Excellent signing! Your hand shapes and movements are very clear."
                    suggestions = ["Keep up the great work!", "Try to maintain this consistency."]
                    errors = []
                elif overall_score >= 0.7:
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
                    "landmark_data": {
                        **mediapipe_landmark_data,
                        "timestamp": datetime.now().isoformat(),
                        "frame_count": 45 + sentence_idx * 10,
                        "detection_confidence": confidence_score
                    },
                    "gesture_sequence": [
                        {
                            "gesture_id": f"sign_{sentence_idx}_{attempt_num}",
                            "start_frame": 5,
                            "end_frame": 40,
                            "duration_ms": 1400 + sentence_idx * 200,
                            "confidence": confidence_score,
                            "hand_used": "both" if sentence_idx % 2 == 0 else "right"
                        }
                    ],
                    "confidence_score": confidence_score,
                    "accuracy_score": accuracy_score,
                    "fluency_score": fluency_score,
                    "ai_feedback": feedback,
                    "suggestions": suggestions,
                    "detected_errors": errors,
                    "duration_ms": 1800 + sentence_idx * 300 + attempt_num * 100,
                    "video_start_frame": sentence_idx * 100,
                    "video_end_frame": sentence_idx * 100 + 45
                }
                
                # Record the attempt
                attempt = await service.record_sentence_attempt(session.id, attempt_data)
                
                assert attempt.id is not None
                assert attempt.session_id == session.id
                assert attempt.sentence_index == sentence_idx
                assert attempt.attempt_number == attempt_num
                assert attempt.target_sentence == sentence
                assert attempt.landmark_data is not None
                assert attempt.gesture_sequence is not None
                assert attempt.ai_feedback == feedback
                assert len(attempt.suggestions) == len(suggestions)
                assert len(attempt.detected_errors) == len(errors)
                
                total_attempts += 1
                if attempt.is_successful:
                    successful_attempts += 1
                
                logger.info(
                    f"Recorded attempt {attempt_num} for sentence {sentence_idx}: "
                    f"score={overall_score:.2f}, successful={attempt.is_successful}"
                )
        
        # 3. Complete the session
        completion_data = {
            "performance_metrics": {
                "total_video_frames": 500,
                "processed_frames": 495,
                "dropped_frames": 5,
                "average_processing_latency_ms": 42,
                "gesture_detection_accuracy": 0.87,
                "mediapipe_processing_time_ms": 35,
                "ai_analysis_time_ms": 150,
                "total_processing_time_seconds": 25
            }
        }
        
        completed_session = await service.complete_practice_session(
            session.id, completion_data
        )
        
        assert completed_session.status == "completed"
        assert completed_session.completed_at is not None
        assert completed_session.sentences_completed == len(asl_world_story_data["sentences"])
        assert completed_session.overall_score > 0
        assert completed_session.performance_metrics["total_video_frames"] == 500
        
        logger.info(
            f"Completed session {session.id}: "
            f"score={completed_session.overall_score:.2f}, "
            f"sentences={completed_session.sentences_completed}"
        )
        
        # 4. Verify progress tracking was updated
        progress_summary = await service.get_user_progress_summary(sample_user_id)
        
        assert progress_summary["user_id"] == sample_user_id
        assert len(progress_summary["progress_records"]) == 3  # vocabulary, grammar, fluency
        
        # Check each skill area was updated
        skill_areas = {p["skill_area"] for p in progress_summary["progress_records"]}
        assert skill_areas == {"vocabulary", "grammar", "fluency"}
        
        # Verify analytics data
        analytics = progress_summary["performance_analytics"]
        assert analytics["session_analytics"]["total_sessions"] == 1
        assert analytics["session_analytics"]["completed_sessions"] == 1
        assert analytics["session_analytics"]["total_practice_time"] > 0
        assert analytics["attempt_analytics"]["total_attempts"] == total_attempts
        assert analytics["attempt_analytics"]["successful_attempts"] == successful_attempts
        
        # Check learning trends
        trends = progress_summary["learning_trends"]
        assert trends["total_active_days"] == 1
        assert len(trends["daily_activity"]) == 1
        assert trends["daily_activity"][0]["sessions"] == 1
        
        # Verify overall summary
        overall = progress_summary["overall_summary"]
        assert overall["total_skill_areas"] == 3
        assert overall["total_sessions"] == 1
        assert overall["proficiency_level"] in ["beginner", "intermediate", "advanced"]
        
        logger.info(f"Progress tracking verified: {overall}")
        
        return {
            "session": completed_session,
            "progress_summary": progress_summary,
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts
        }
    
    async def test_multiple_asl_world_sessions_progression(
        self, 
        db_session, 
        sample_user_id, 
        asl_world_story_data
    ):
        """Test user progression across multiple ASL World sessions"""
        service = ProgressService(db_session)
        
        # Simulate 3 practice sessions over time with improving performance
        session_results = []
        
        for session_num in range(1, 4):
            # Modify story difficulty and user performance over time
            story_data = {
                **asl_world_story_data,
                "title": f"Session {session_num} - {asl_world_story_data['title']}",
                "difficulty": ["beginner", "intermediate", "advanced"][session_num - 1]
            }
            
            session_config = {
                "session_type": "individual",
                "session_name": f"ASL World Session {session_num}",
                "story_content": story_data,
                "difficulty_level": story_data["difficulty"],
                "total_sentences": len(story_data["sentences"]),
                "skill_areas": ["vocabulary", "grammar", "fluency"]
            }
            
            session = await service.start_practice_session(sample_user_id, session_config)
            
            # Simulate improving performance over sessions
            base_performance = 0.6 + (session_num * 0.1)  # Improvement over time
            
            for sentence_idx, sentence in enumerate(story_data["sentences"]):
                # Fewer attempts needed as user improves
                num_attempts = max(1, 3 - session_num)
                
                for attempt_num in range(1, num_attempts + 1):
                    # Better performance in later sessions
                    confidence = min(1.0, base_performance + 0.1 + (attempt_num * 0.05))
                    accuracy = min(1.0, base_performance + 0.05 + (attempt_num * 0.08))
                    fluency = min(1.0, base_performance - 0.05 + (attempt_num * 0.1))
                    
                    attempt_data = {
                        "sentence_index": sentence_idx,
                        "target_sentence": sentence,
                        "confidence_score": confidence,
                        "accuracy_score": accuracy,
                        "fluency_score": fluency,
                        "ai_feedback": f"Session {session_num} feedback for attempt {attempt_num}",
                        "duration_ms": max(1000, 2000 - (session_num * 200))  # Faster over time
                    }
                    
                    await service.record_sentence_attempt(session.id, attempt_data)
            
            # Complete session
            completed_session = await service.complete_practice_session(session.id)
            session_results.append(completed_session)
            
            logger.info(
                f"Completed session {session_num}: "
                f"difficulty={story_data['difficulty']}, "
                f"score={completed_session.overall_score:.2f}"
            )
        
        # Verify progression over sessions
        assert len(session_results) == 3
        
        # Scores should generally improve (allowing for some variation)
        scores = [s.overall_score for s in session_results]
        assert scores[2] >= scores[0]  # Last session should be better than first
        
        # Get final progress summary
        final_progress = await service.get_user_progress_summary(sample_user_id)
        
        # Should show progression in all skill areas
        for progress_record in final_progress["progress_records"]:
            assert progress_record["total_sessions"] == 3
            assert progress_record["current_level"] > 0
            assert progress_record["experience_points"] > 0
        
        # Analytics should reflect multiple sessions
        analytics = final_progress["performance_analytics"]
        assert analytics["session_analytics"]["total_sessions"] == 3
        assert analytics["session_analytics"]["completed_sessions"] == 3
        
        # Learning trends should show consistency
        trends = final_progress["learning_trends"]
        assert trends["total_active_days"] >= 1
        
        logger.info(f"Final progression: {final_progress['overall_summary']}")
        
        return final_progress
    
    async def test_asl_world_error_recovery(self, db_session, sample_user_id):
        """Test error handling and recovery in ASL World integration"""
        service = ProgressService(db_session)
        
        # Start session
        session_config = {
            "session_type": "individual",
            "total_sentences": 2,
            "skill_areas": ["vocabulary"]
        }
        session = await service.start_practice_session(sample_user_id, session_config)
        
        # Test recording attempt with missing MediaPipe data
        attempt_data = {
            "sentence_index": 0,
            "target_sentence": "Test sentence",
            "landmark_data": None,  # Simulate MediaPipe failure
            "confidence_score": 0.0,  # Low confidence due to processing failure
            "accuracy_score": None,   # No accuracy data available
            "fluency_score": None,    # No fluency data available
            "ai_feedback": "Unable to analyze gesture due to processing error",
            "detected_errors": [
                {"type": "processing_error", "severity": "high", "description": "MediaPipe processing failed"}
            ]
        }
        
        # Should handle gracefully
        attempt = await service.record_sentence_attempt(session.id, attempt_data)
        assert attempt.id is not None
        assert attempt.landmark_data is None
        assert attempt.confidence_score == 0.0
        assert attempt.is_successful is False
        
        # Test recovery with successful attempt
        recovery_attempt_data = {
            "sentence_index": 0,
            "target_sentence": "Test sentence",
            "confidence_score": 0.8,
            "accuracy_score": 0.85,
            "fluency_score": 0.75,
            "ai_feedback": "Good recovery! Processing successful."
        }
        
        recovery_attempt = await service.record_sentence_attempt(session.id, recovery_attempt_data)
        assert recovery_attempt.is_successful is True
        assert recovery_attempt.attempt_number == 2
        
        # Complete session should handle mixed results
        completed_session = await service.complete_practice_session(session.id)
        assert completed_session.status == "completed"
        
        # Progress should still be updated despite errors
        progress_summary = await service.get_user_progress_summary(sample_user_id)
        assert len(progress_summary["progress_records"]) >= 1
    
    async def test_performance_with_large_dataset(self, db_session, sample_user_id):
        """Test performance with realistic large dataset"""
        service = ProgressService(db_session)
        
        # Create multiple sessions with many attempts
        import time
        start_time = time.time()
        
        num_sessions = 5
        sentences_per_session = 10
        attempts_per_sentence = 2
        
        for session_num in range(num_sessions):
            session_config = {
                "session_type": "individual",
                "total_sentences": sentences_per_session,
                "skill_areas": ["vocabulary", "grammar"]
            }
            session = await service.start_practice_session(sample_user_id, session_config)
            
            for sentence_idx in range(sentences_per_session):
                for attempt_num in range(attempts_per_sentence):
                    attempt_data = {
                        "sentence_index": sentence_idx,
                        "target_sentence": f"Session {session_num} sentence {sentence_idx}",
                        "confidence_score": 0.7 + (attempt_num * 0.1),
                        "accuracy_score": 0.75 + (attempt_num * 0.08),
                        "fluency_score": 0.65 + (attempt_num * 0.12),
                        "ai_feedback": f"Feedback for session {session_num}, sentence {sentence_idx}, attempt {attempt_num}"
                    }
                    await service.record_sentence_attempt(session.id, attempt_data)
            
            await service.complete_practice_session(session.id)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        total_attempts = num_sessions * sentences_per_session * attempts_per_sentence
        
        logger.info(
            f"Processed {total_attempts} attempts in {total_time:.2f} seconds "
            f"({total_attempts/total_time:.1f} attempts/second)"
        )
        
        # Should complete within reasonable time
        assert total_time < 30.0  # Should process 100 attempts in under 30 seconds
        
        # Verify all data was recorded correctly
        progress_summary = await service.get_user_progress_summary(sample_user_id)
        analytics = progress_summary["performance_analytics"]
        
        assert analytics["session_analytics"]["total_sessions"] == num_sessions
        assert analytics["attempt_analytics"]["total_attempts"] == total_attempts


# Run integration tests
if __name__ == "__main__":
    import sys
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run specific test or all tests
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        pytest.main(["-v", "-s", "-k", test_name, __file__])
    else:
        pytest.main(["-v", "-s", __file__])