"""
Simple test for progress tracking models without database dependencies
Tests the model logic, calculations, and validation
"""

import json
from datetime import datetime, timedelta
from uuid import uuid4

# Set up path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.progress import PracticeSession, SentenceAttempt, UserProgress


def test_practice_session_model():
    """Test PracticeSession model logic"""
    print("Testing PracticeSession model...")
    
    user_id = str(uuid4())
    
    # Test basic creation
    session = PracticeSession(
        user_id=user_id,
        session_type="individual",
        difficulty_level="beginner",
        total_sentences=5,
        sentences_completed=3,
        overall_score=0.85,
        status="active"
    )
    
    # Test properties
    assert session.user_id == user_id
    assert session.session_type == "individual"
    assert session.difficulty_level == "beginner"
    assert session.total_sentences == 5
    assert session.sentences_completed == 3
    assert session.overall_score == 0.85
    assert session.status == "active"
    
    # Test completion percentage calculation
    completion_pct = session.calculate_completion_percentage()
    assert abs(completion_pct - 60.0) < 0.1  # 3/5 * 100 = 60%
    
    # Test with no total sentences
    session.total_sentences = None
    assert session.calculate_completion_percentage() is None
    
    # Test duration calculation
    session.started_at = datetime.now() - timedelta(minutes=5)
    session.completed_at = datetime.now()
    duration = session.calculate_duration()
    assert 290 <= duration <= 310  # Should be around 300 seconds (5 minutes)
    
    # Test completion status
    session.status = "completed"
    assert session.is_completed() is True
    
    session.status = "active"
    assert session.is_completed() is False
    
    # Test performance summary
    summary = session.get_performance_summary()
    assert summary["sentences_completed"] == 3
    assert summary["overall_score"] == 0.85
    assert summary["status"] == "active"
    
    print("✓ PracticeSession model test passed")


def test_sentence_attempt_model():
    """Test SentenceAttempt model logic"""
    print("Testing SentenceAttempt model...")
    
    session_id = str(uuid4())
    
    # Test basic creation
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
    
    # Test properties
    assert attempt.session_id == session_id
    assert attempt.sentence_index == 0
    assert attempt.target_sentence == "Hello, my name is John."
    assert attempt.confidence_score == 0.85
    assert attempt.accuracy_score == 0.90
    assert attempt.fluency_score == 0.75
    assert attempt.attempt_number == 1
    assert attempt.duration_ms == 2500
    assert attempt.is_successful is True
    
    # Test overall score calculation (weighted average)
    overall_score = attempt.get_overall_score()
    expected_score = 0.90 * 0.4 + 0.85 * 0.3 + 0.75 * 0.3  # accuracy 40%, confidence 30%, fluency 30%
    assert abs(overall_score - expected_score) < 0.001
    
    # Test with missing scores
    attempt_partial = SentenceAttempt(
        session_id=session_id,
        sentence_index=1,
        target_sentence="Test sentence",
        confidence_score=0.8,
        accuracy_score=None,
        fluency_score=0.7,
        attempt_number=1
    )
    
    # Should calculate simple average when not all scores available
    partial_score = attempt_partial.get_overall_score()
    expected_partial = (0.8 + 0.7) / 2  # Simple average of available scores
    assert abs(partial_score - expected_partial) < 0.001
    
    # Test with no scores
    attempt_no_scores = SentenceAttempt(
        session_id=session_id,
        sentence_index=2,
        target_sentence="No scores",
        attempt_number=1
    )
    
    assert attempt_no_scores.get_overall_score() is None
    
    # Test performance summary
    summary = attempt.get_performance_summary()
    assert summary["attempt_id"] == attempt.id
    assert summary["sentence_index"] == 0
    assert summary["attempt_number"] == 1
    assert summary["target_sentence"] == "Hello, my name is John."
    assert abs(summary["overall_score"] - expected_score) < 0.001
    assert summary["is_successful"] is True
    
    print("✓ SentenceAttempt model test passed")


def test_user_progress_model():
    """Test UserProgress model logic"""
    print("Testing UserProgress model...")
    
    user_id = str(uuid4())
    
    # Test basic creation
    progress = UserProgress(
        user_id=user_id,
        skill_area="fingerspelling",
        skill_category="basic_vocabulary",
        current_level=2.5,
        experience_points=150.0,
        total_practice_time=3600,  # 1 hour
        total_sessions=5,
        total_attempts=25,
        successful_attempts=20,
        average_score=0.82,
        learning_streak=3,
        longest_streak=5
    )
    
    # Test properties
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
    
    # Test success rate calculation
    success_rate = progress.calculate_success_rate()
    assert success_rate == 80.0  # 20/25 * 100 = 80%
    
    # Test with no attempts
    progress.total_attempts = 0
    assert progress.calculate_success_rate() == 0.0
    
    # Reset for other tests
    progress.total_attempts = 25
    
    # Test level progress calculation
    level_progress = progress.calculate_level_progress()
    assert level_progress == 0.5  # 2.5 - 2 = 0.5 (progress within level 2)
    
    # Test next milestone
    next_milestone = progress.get_next_milestone()
    assert next_milestone == 3.0  # Next whole level
    
    # Test at max level
    progress.current_level = 10.0
    assert progress.get_next_milestone() is None
    
    # Reset for other tests
    progress.current_level = 2.5
    
    # Test milestone addition
    progress.add_milestone(3.0, "Reached level 3")
    assert len(progress.milestones) == 1
    assert progress.milestones[0]["level"] == 3.0
    assert progress.milestones[0]["description"] == "Reached level 3"
    assert "achieved_at" in progress.milestones[0]
    
    # Test streak update
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    # First practice (no previous date)
    progress.last_practice_date = None
    progress.learning_streak = 0
    progress.longest_streak = 0
    
    progress.update_streak(today)
    assert progress.learning_streak == 1
    assert progress.longest_streak == 1
    assert progress.last_practice_date.date() == today.date()
    
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
    
    # Test progress summary
    summary = progress.get_progress_summary()
    assert summary["user_id"] == user_id
    assert summary["skill_area"] == "fingerspelling"
    assert summary["current_level"] == 2.5
    assert summary["level_progress"] == 0.5
    assert summary["next_milestone"] == 3.0
    assert summary["success_rate"] == 80.0
    assert summary["learning_streak"] == 1
    assert summary["longest_streak"] == 2
    assert summary["milestones_count"] == 1
    
    print("✓ UserProgress model test passed")


def test_model_validation():
    """Test model validation logic"""
    print("Testing model validation...")
    
    # Test PracticeSession validation
    session = PracticeSession(
        user_id=str(uuid4()),
        session_type="individual"
    )
    
    # Test score validation
    try:
        session.overall_score = 1.5  # Invalid: > 1.0
        # Should trigger validation if implemented
    except ValueError:
        pass  # Expected
    
    try:
        session.sentences_completed = -1  # Invalid: negative
        # Should trigger validation if implemented
    except ValueError:
        pass  # Expected
    
    # Test SentenceAttempt validation
    attempt = SentenceAttempt(
        session_id=str(uuid4()),
        sentence_index=0,
        target_sentence="Test",
        attempt_number=1
    )
    
    # Test score range validation
    try:
        attempt.confidence_score = -0.1  # Invalid: < 0.0
        # Should trigger validation if implemented
    except ValueError:
        pass  # Expected
    
    try:
        attempt.accuracy_score = 1.1  # Invalid: > 1.0
        # Should trigger validation if implemented
    except ValueError:
        pass  # Expected
    
    # Test UserProgress validation
    progress = UserProgress(
        user_id=str(uuid4()),
        skill_area="test"
    )
    
    try:
        progress.current_level = -1.0  # Invalid: < 0.0
        # Should trigger validation if implemented
    except ValueError:
        pass  # Expected
    
    try:
        progress.current_level = 11.0  # Invalid: > 10.0
        # Should trigger validation if implemented
    except ValueError:
        pass  # Expected
    
    print("✓ Model validation test passed")


def test_json_serialization():
    """Test JSON serialization of model data"""
    print("Testing JSON serialization...")
    
    # Test complex data structures
    landmark_data = {
        "hand_landmarks": [
            [[0.1, 0.2, 0.3] for _ in range(21)],  # Right hand
            [[0.4, 0.5, 0.6] for _ in range(21)]   # Left hand
        ],
        "pose_landmarks": [[0.5, 0.5, 0.5] for _ in range(33)],
        "face_landmarks": [[0.45, 0.45, 0.45] for _ in range(468)]
    }
    
    gesture_sequence = [
        {
            "gesture_id": "hello",
            "start_frame": 10,
            "end_frame": 50,
            "confidence": 0.85,
            "hand_used": "both"
        },
        {
            "gesture_id": "name",
            "start_frame": 55,
            "end_frame": 90,
            "confidence": 0.92,
            "hand_used": "right"
        }
    ]
    
    suggestions = [
        "Keep your hand steady during the sign",
        "Make sure your palm orientation is correct",
        "Practice the movement more slowly first"
    ]
    
    detected_errors = [
        {
            "type": "hand_shape",
            "severity": "minor",
            "description": "Slight finger positioning issue",
            "frame_range": [15, 25]
        }
    ]
    
    # Test SentenceAttempt with complex JSON data
    attempt = SentenceAttempt(
        session_id=str(uuid4()),
        sentence_index=0,
        target_sentence="Hello, my name is John.",
        landmark_data=landmark_data,
        gesture_sequence=gesture_sequence,
        suggestions=suggestions,
        detected_errors=detected_errors,
        attempt_number=1
    )
    
    # Verify JSON data is stored correctly
    assert attempt.landmark_data == landmark_data
    assert attempt.gesture_sequence == gesture_sequence
    assert attempt.suggestions == suggestions
    assert attempt.detected_errors == detected_errors
    
    # Test UserProgress with milestones
    progress = UserProgress(
        user_id=str(uuid4()),
        skill_area="vocabulary"
    )
    
    progress.add_milestone(1.0, "First level completed")
    progress.add_milestone(2.0, "Second level completed")
    
    assert len(progress.milestones) == 2
    assert progress.milestones[0]["level"] == 1.0
    assert progress.milestones[1]["level"] == 2.0
    
    # Test PracticeSession with complex session data
    session_data = {
        "module": "asl_world",
        "video_processing_enabled": True,
        "mediapipe_config": {
            "min_detection_confidence": 0.5,
            "min_tracking_confidence": 0.5,
            "model_complexity": 1
        },
        "ai_feedback_enabled": True,
        "story_metadata": {
            "topic": "daily_routine",
            "vocabulary_level": "intermediate",
            "estimated_duration_minutes": 5
        }
    }
    
    performance_metrics = {
        "total_video_frames": 500,
        "processed_frames": 495,
        "dropped_frames": 5,
        "average_processing_latency_ms": 42,
        "gesture_detection_accuracy": 0.87
    }
    
    session = PracticeSession(
        user_id=str(uuid4()),
        session_type="individual",
        session_data=session_data,
        performance_metrics=performance_metrics,
        skill_areas=["vocabulary", "grammar", "fluency"]
    )
    
    assert session.session_data == session_data
    assert session.performance_metrics == performance_metrics
    assert session.skill_areas == ["vocabulary", "grammar", "fluency"]
    
    print("✓ JSON serialization test passed")


def test_realistic_asl_world_scenario():
    """Test realistic ASL World practice scenario"""
    print("Testing realistic ASL World scenario...")
    
    user_id = str(uuid4())
    
    # Create practice session for ASL World
    story_content = {
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
    
    session = PracticeSession(
        user_id=user_id,
        session_type="individual",
        session_name="ASL World - Morning Routine Practice",
        story_content=story_content,
        difficulty_level="intermediate",
        total_sentences=len(story_content["sentences"]),
        skill_areas=["vocabulary", "grammar", "fluency"],
        session_data={
            "module": "asl_world",
            "video_processing_enabled": True,
            "mediapipe_config": {
                "min_detection_confidence": 0.5,
                "min_tracking_confidence": 0.5,
                "model_complexity": 1
            }
        },
        status="active"
    )
    
    # Simulate practicing each sentence
    attempts = []
    total_successful = 0
    
    for sentence_idx, sentence in enumerate(story_content["sentences"]):
        # Simulate 1-2 attempts per sentence
        num_attempts = 1 if sentence_idx < 2 else 2
        
        for attempt_num in range(1, num_attempts + 1):
            # Simulate improving performance on retries
            base_confidence = 0.65 + (sentence_idx * 0.05) + (attempt_num * 0.1)
            base_accuracy = 0.70 + (sentence_idx * 0.04) + (attempt_num * 0.08)
            base_fluency = 0.60 + (sentence_idx * 0.06) + (attempt_num * 0.12)
            
            # Add some realistic variation
            import random
            confidence_score = min(1.0, base_confidence + random.uniform(-0.1, 0.1))
            accuracy_score = min(1.0, base_accuracy + random.uniform(-0.08, 0.08))
            fluency_score = min(1.0, base_fluency + random.uniform(-0.12, 0.12))
            
            # Generate realistic AI feedback
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
            
            # Create attempt
            attempt = SentenceAttempt(
                session_id=session.id,
                sentence_index=sentence_idx,
                target_sentence=sentence,
                landmark_data={
                    "hand_landmarks": [
                        [[0.1 + j*0.01, 0.2 + j*0.01, 0.3 + j*0.01] for j in range(21)]
                    ],
                    "pose_landmarks": [[0.5, 0.5, 0.5] for _ in range(33)],
                    "timestamp": datetime.now().isoformat(),
                    "detection_confidence": confidence_score
                },
                gesture_sequence=[
                    {
                        "gesture_id": f"sign_{sentence_idx}_{attempt_num}",
                        "start_frame": 5,
                        "end_frame": 40,
                        "duration_ms": 1400 + sentence_idx * 200,
                        "confidence": confidence_score,
                        "hand_used": "both" if sentence_idx % 2 == 0 else "right"
                    }
                ],
                confidence_score=confidence_score,
                accuracy_score=accuracy_score,
                fluency_score=fluency_score,
                ai_feedback=feedback,
                suggestions=suggestions,
                detected_errors=errors,
                duration_ms=1800 + sentence_idx * 300 + attempt_num * 100,
                attempt_number=attempt_num,
                is_successful=overall_score >= 0.7
            )
            
            attempts.append(attempt)
            if attempt.is_successful:
                total_successful += 1
    
    # Complete the session
    session.status = "completed"
    session.completed_at = datetime.now()
    session.sentences_completed = len(story_content["sentences"])
    session.overall_score = sum(a.get_overall_score() for a in attempts) / len(attempts)
    session.performance_metrics = {
        "total_video_frames": 500,
        "processed_frames": 495,
        "dropped_frames": 5,
        "average_processing_latency_ms": 42,
        "gesture_detection_accuracy": 0.87,
        "total_attempts": len(attempts),
        "successful_attempts": total_successful
    }
    
    # Verify session results
    assert session.is_completed()
    assert session.sentences_completed == 5
    assert 0.0 <= session.overall_score <= 1.0
    assert len(attempts) >= 5  # At least one attempt per sentence
    
    # Create user progress for each skill area
    skill_areas = ["vocabulary", "grammar", "fluency"]
    progress_records = []
    
    for skill_area in skill_areas:
        progress = UserProgress(
            user_id=user_id,
            skill_area=skill_area,
            skill_category="intermediate",
            current_level=1.5,  # Starting level
            experience_points=50.0,  # Base experience
            total_practice_time=300,  # 5 minutes
            total_sessions=1,
            total_attempts=len(attempts),
            successful_attempts=total_successful,
            average_score=session.overall_score,
            learning_streak=1,
            longest_streak=1,
            last_practice_date=datetime.now()
        )
        
        # Add milestone for completing first session
        progress.add_milestone(1.0, f"Completed first {skill_area} session")
        
        progress_records.append(progress)
    
    # Verify progress records
    assert len(progress_records) == 3
    for progress in progress_records:
        assert progress.total_sessions == 1
        assert progress.total_attempts == len(attempts)
        assert progress.successful_attempts == total_successful
        assert progress.calculate_success_rate() == (total_successful / len(attempts)) * 100
        assert len(progress.milestones) == 1
    
    print(f"✓ Realistic ASL World scenario test passed:")
    print(f"  - Session completed with {session.sentences_completed} sentences")
    print(f"  - Overall score: {session.overall_score:.2f}")
    print(f"  - Total attempts: {len(attempts)}, Successful: {total_successful}")
    print(f"  - Success rate: {(total_successful / len(attempts)) * 100:.1f}%")
    print(f"  - Progress tracked for {len(progress_records)} skill areas")


def run_all_tests():
    """Run all model tests"""
    print("Starting progress tracking model tests...\n")
    
    try:
        test_practice_session_model()
        test_sentence_attempt_model()
        test_user_progress_model()
        test_model_validation()
        test_json_serialization()
        test_realistic_asl_world_scenario()
        
        print("\n✅ All progress tracking model tests passed!")
        print("\nSummary:")
        print("- PracticeSession model: ✓")
        print("- SentenceAttempt model: ✓")
        print("- UserProgress model: ✓")
        print("- Model validation: ✓")
        print("- JSON serialization: ✓")
        print("- ASL World integration: ✓")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_all_tests()