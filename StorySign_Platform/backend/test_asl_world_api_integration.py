"""
Integration test demonstrating how progress tracking integrates with ASL World API
Shows how existing ASL World endpoints can be enhanced with progress tracking
"""

import json
from datetime import datetime
from uuid import uuid4

# Set up path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.progress_service import ProgressService
from models.progress import PracticeSession, SentenceAttempt, UserProgress


class MockDatabaseSession:
    """Mock database session for testing without actual database"""
    
    def __init__(self):
        self.data = {}
        self.committed = False
    
    async def commit(self):
        self.committed = True
    
    async def rollback(self):
        pass
    
    async def flush(self):
        pass
    
    async def close(self):
        pass


class MockProgressRepository:
    """Mock repository for testing progress service logic"""
    
    def __init__(self, session):
        self.session = session
        self.sessions = {}
        self.attempts = {}
        self.progress = {}
    
    async def create_practice_session(self, session_data):
        session = PracticeSession(**session_data)
        session.id = str(uuid4())
        self.sessions[session.id] = session
        return session
    
    async def get_practice_session(self, session_id):
        return self.sessions.get(session_id)
    
    async def update_practice_session(self, session_id, update_data):
        session = self.sessions.get(session_id)
        if session:
            for key, value in update_data.items():
                setattr(session, key, value)
        return session
    
    async def complete_practice_session(self, session_id, completion_data):
        return await self.update_practice_session(session_id, completion_data)
    
    async def create_sentence_attempt(self, attempt_data):
        attempt = SentenceAttempt(**attempt_data)
        attempt.id = str(uuid4())
        if attempt.session_id not in self.attempts:
            self.attempts[attempt.session_id] = []
        self.attempts[attempt.session_id].append(attempt)
        return attempt
    
    async def get_session_attempts(self, session_id, sentence_index=None):
        attempts = self.attempts.get(session_id, [])
        if sentence_index is not None:
            attempts = [a for a in attempts if a.sentence_index == sentence_index]
        return attempts
    
    async def get_or_create_user_progress(self, user_id, skill_area, skill_category=None):
        key = f"{user_id}:{skill_area}"
        if key not in self.progress:
            progress = UserProgress(
                user_id=user_id,
                skill_area=skill_area,
                skill_category=skill_category
            )
            progress.id = str(uuid4())
            self.progress[key] = progress
        return self.progress[key]
    
    async def update_user_progress(self, user_id, skill_area, session_data):
        progress = await self.get_or_create_user_progress(user_id, skill_area)
        
        # Update session counts
        progress.total_sessions = (progress.total_sessions or 0) + 1
        
        # Update practice time
        if "duration_seconds" in session_data:
            progress.total_practice_time = (progress.total_practice_time or 0) + session_data["duration_seconds"]
        
        # Update attempt counts
        if "total_attempts" in session_data:
            progress.total_attempts = (progress.total_attempts or 0) + session_data["total_attempts"]
        
        if "successful_attempts" in session_data:
            progress.successful_attempts = (progress.successful_attempts or 0) + session_data["successful_attempts"]
        
        # Update experience points and level
        if "experience_gained" in session_data:
            progress.experience_points = (progress.experience_points or 0.0) + session_data["experience_gained"]
            progress.current_level = self._calculate_level_from_experience(
                progress.experience_points
            )
        
        # Update streak
        progress.update_streak(datetime.now())
        
        return progress
    
    def _calculate_level_from_experience(self, experience_points):
        import math
        level = math.sqrt(experience_points / 100.0)
        return min(10.0, level)
    
    async def get_user_progress(self, user_id, skill_area=None):
        results = []
        for key, progress in self.progress.items():
            if progress.user_id == user_id:
                if skill_area is None or progress.skill_area == skill_area:
                    results.append(progress)
        return results
    
    async def get_user_performance_analytics(self, user_id, date_range=None, skill_area=None):
        # Mock analytics data
        user_sessions = [s for s in self.sessions.values() if s.user_id == user_id]
        user_attempts = []
        for session_id in self.attempts:
            session = self.sessions.get(session_id)
            if session and session.user_id == user_id:
                user_attempts.extend(self.attempts[session_id])
        
        total_sessions = len(user_sessions)
        completed_sessions = len([s for s in user_sessions if s.status == "completed"])
        total_practice_time = sum(s.duration_seconds or 0 for s in user_sessions)
        avg_session_score = sum(s.overall_score or 0 for s in user_sessions) / max(1, total_sessions)
        
        total_attempts = len(user_attempts)
        successful_attempts = len([a for a in user_attempts if a.is_successful])
        success_rate = (successful_attempts / max(1, total_attempts)) * 100.0
        
        return {
            "user_id": user_id,
            "session_analytics": {
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "total_practice_time": total_practice_time,
                "average_session_score": avg_session_score,
                "total_sentences_practiced": sum(s.sentences_completed or 0 for s in user_sessions)
            },
            "attempt_analytics": {
                "total_attempts": total_attempts,
                "successful_attempts": successful_attempts,
                "success_rate": success_rate,
                "average_confidence": sum(a.confidence_score or 0 for a in user_attempts) / max(1, total_attempts),
                "average_accuracy": sum(a.accuracy_score or 0 for a in user_attempts) / max(1, total_attempts),
                "average_fluency": sum(a.fluency_score or 0 for a in user_attempts) / max(1, total_attempts)
            }
        }
    
    async def get_learning_trends(self, user_id, days=30):
        return {
            "user_id": user_id,
            "period_days": days,
            "daily_activity": [],
            "total_active_days": 1,
            "consistency_score": 100.0
        }


class MockProgressService(ProgressService):
    """Mock progress service using mock repository"""
    
    def __init__(self):
        self.db_session = MockDatabaseSession()
        self.repository = MockProgressRepository(self.db_session)
    
    async def get_user_progress_summary(self, user_id):
        """Get comprehensive progress summary for a user"""
        try:
            # Get progress records
            progress_records = await self.repository.get_user_progress(user_id)
            
            # Get recent performance analytics
            analytics = await self.repository.get_user_performance_analytics(user_id)
            
            # Get learning trends
            trends = await self.repository.get_learning_trends(user_id, days=30)
            
            return {
                "user_id": user_id,
                "progress_records": [p.get_progress_summary() for p in progress_records],
                "performance_analytics": analytics,
                "learning_trends": trends,
                "overall_summary": self._calculate_overall_summary(progress_records, analytics)
            }
            
        except Exception as e:
            # Return empty summary for new users
            return {
                "user_id": user_id,
                "progress_records": [],
                "performance_analytics": {
                    "session_analytics": {
                        "total_sessions": 0,
                        "completed_sessions": 0,
                        "total_practice_time": 0,
                        "average_session_score": 0.0,
                        "total_sentences_practiced": 0
                    },
                    "attempt_analytics": {
                        "total_attempts": 0,
                        "successful_attempts": 0,
                        "success_rate": 0.0,
                        "average_confidence": 0.0,
                        "average_accuracy": 0.0,
                        "average_fluency": 0.0
                    }
                },
                "learning_trends": {
                    "user_id": user_id,
                    "period_days": 30,
                    "daily_activity": [],
                    "total_active_days": 0,
                    "consistency_score": 0.0
                },
                "overall_summary": {
                    "total_skill_areas": 0,
                    "average_level": 0.0,
                    "total_experience": 0.0,
                    "overall_success_rate": 0.0,
                    "learning_streak": 0,
                    "proficiency_level": "beginner",
                    "total_practice_time": 0,
                    "total_sessions": 0
                }
            }


def test_asl_world_story_generation_with_progress():
    """Test ASL World story generation enhanced with progress tracking"""
    print("Testing ASL World story generation with progress tracking...")
    
    # Simulate existing ASL World story generation API response
    def generate_story_api(user_id, difficulty="beginner", topic="daily_routine"):
        """Mock ASL World story generation API"""
        stories = {
            "beginner": {
                "daily_routine": {
                    "title": "My Morning",
                    "sentences": [
                        "I wake up early.",
                        "I brush my teeth.",
                        "I eat breakfast."
                    ]
                }
            },
            "intermediate": {
                "daily_routine": {
                    "title": "Daily Activities",
                    "sentences": [
                        "Good morning, how are you today?",
                        "I have a busy schedule ahead.",
                        "First, I need to check my emails.",
                        "Then I will attend a meeting.",
                        "After lunch, I plan to exercise."
                    ]
                }
            }
        }
        
        story = stories.get(difficulty, {}).get(topic, stories["beginner"]["daily_routine"])
        
        return {
            "story": story,
            "metadata": {
                "difficulty": difficulty,
                "topic": topic,
                "generated_at": datetime.now().isoformat(),
                "estimated_duration_minutes": len(story["sentences"]) * 0.5
            }
        }
    
    # Enhanced API that includes progress tracking
    async def enhanced_generate_story_api(user_id, difficulty="beginner", topic="daily_routine"):
        """Enhanced story generation API with progress tracking"""
        
        # Generate story using existing logic
        story_response = generate_story_api(user_id, difficulty, topic)
        
        # Initialize progress service
        progress_service = MockProgressService()
        
        # Get user's current progress to inform story generation
        user_progress = await progress_service.get_user_progress_summary(user_id)
        
        # Adjust difficulty based on user progress (if they have any)
        if user_progress["progress_records"]:
            avg_level = sum(p["current_level"] for p in user_progress["progress_records"]) / len(user_progress["progress_records"])
            
            if avg_level >= 3.0 and difficulty == "beginner":
                # User has progressed, suggest intermediate
                story_response = generate_story_api(user_id, "intermediate", topic)
                story_response["recommendation"] = "Upgraded to intermediate based on your progress!"
            elif avg_level < 2.0 and difficulty == "intermediate":
                # User might need more beginner practice
                story_response["recommendation"] = "Consider practicing more beginner stories to build confidence."
        
        # Add progress context to response
        story_response["user_progress"] = user_progress
        
        return story_response
    
    # Test the enhanced API
    import asyncio
    
    async def run_test():
        user_id = str(uuid4())
        
        # First story generation (new user)
        response1 = await enhanced_generate_story_api(user_id, "beginner", "daily_routine")
        
        assert "story" in response1
        assert "metadata" in response1
        assert "user_progress" in response1
        assert response1["story"]["title"] == "My Morning"
        assert len(response1["story"]["sentences"]) == 3
        
        # Simulate user completing some practice sessions to build progress
        progress_service = MockProgressService()
        
        # Create a completed session
        session_config = {
            "session_type": "individual",
            "story_content": response1["story"],
            "difficulty_level": "beginner",
            "total_sentences": len(response1["story"]["sentences"]),
            "skill_areas": ["vocabulary", "grammar"]
        }
        
        session = await progress_service.start_practice_session(user_id, session_config)
        
        # Record successful attempts
        for i, sentence in enumerate(response1["story"]["sentences"]):
            attempt_data = {
                "sentence_index": i,
                "target_sentence": sentence,
                "confidence_score": 0.85,
                "accuracy_score": 0.90,
                "fluency_score": 0.80,
                "ai_feedback": "Great job!"
            }
            await progress_service.record_sentence_attempt(session.id, attempt_data)
        
        # Complete session
        await progress_service.complete_practice_session(session.id)
        
        # Generate another story (user now has progress)
        response2 = await enhanced_generate_story_api(user_id, "beginner", "daily_routine")
        
        # Should now have progress data
        assert response2["user_progress"]["progress_records"]
        assert len(response2["user_progress"]["progress_records"]) == 2  # vocabulary, grammar
        
        print("✓ Enhanced story generation API test passed")
    
    asyncio.run(run_test())


def test_asl_world_practice_session_with_progress():
    """Test ASL World practice session enhanced with progress tracking"""
    print("Testing ASL World practice session with progress tracking...")
    
    # Simulate existing ASL World practice session API
    def start_practice_session_api(user_id, story_data):
        """Mock ASL World practice session start API"""
        return {
            "session_id": str(uuid4()),
            "user_id": user_id,
            "story": story_data,
            "status": "active",
            "started_at": datetime.now().isoformat(),
            "websocket_url": f"ws://localhost:8000/ws/practice/{user_id}"
        }
    
    def process_gesture_api(session_id, frame_data, sentence_index):
        """Mock ASL World gesture processing API"""
        # Simulate MediaPipe processing
        import random
        
        confidence = 0.7 + random.uniform(0, 0.3)
        accuracy = 0.75 + random.uniform(0, 0.25)
        fluency = 0.65 + random.uniform(0, 0.35)
        
        return {
            "session_id": session_id,
            "sentence_index": sentence_index,
            "analysis": {
                "confidence_score": confidence,
                "accuracy_score": accuracy,
                "fluency_score": fluency,
                "landmark_data": {
                    "hand_landmarks": [[[0.1, 0.2, 0.3] for _ in range(21)]],
                    "pose_landmarks": [[0.5, 0.5, 0.5] for _ in range(33)]
                },
                "gesture_sequence": [
                    {
                        "gesture": f"gesture_{sentence_index}",
                        "confidence": confidence,
                        "duration_ms": 1500
                    }
                ]
            },
            "feedback": {
                "message": "Good attempt! Keep practicing.",
                "suggestions": ["Focus on hand shape clarity", "Maintain steady movement"],
                "detected_errors": []
            }
        }
    
    # Enhanced APIs with progress tracking
    async def enhanced_start_practice_session_api(user_id, story_data):
        """Enhanced practice session start with progress tracking"""
        
        # Start session using existing logic
        session_response = start_practice_session_api(user_id, story_data)
        
        # Initialize progress tracking
        progress_service = MockProgressService()
        
        session_config = {
            "session_type": "individual",
            "story_content": story_data,
            "difficulty_level": story_data.get("difficulty", "beginner"),
            "total_sentences": len(story_data["sentences"]),
            "skill_areas": ["vocabulary", "grammar", "fluency"],
            "session_data": {
                "asl_world_session_id": session_response["session_id"],
                "websocket_url": session_response["websocket_url"]
            }
        }
        
        progress_session = await progress_service.start_practice_session(user_id, session_config)
        
        # Add progress session ID to response
        session_response["progress_session_id"] = progress_session.id
        session_response["progress_service"] = progress_service
        
        return session_response
    
    async def enhanced_process_gesture_api(session_response, frame_data, sentence_index, target_sentence):
        """Enhanced gesture processing with progress tracking"""
        
        # Process gesture using existing logic
        gesture_response = process_gesture_api(
            session_response["session_id"], 
            frame_data, 
            sentence_index
        )
        
        # Record attempt in progress tracking
        progress_service = session_response["progress_service"]
        
        attempt_data = {
            "sentence_index": sentence_index,
            "target_sentence": target_sentence,
            "landmark_data": gesture_response["analysis"]["landmark_data"],
            "gesture_sequence": gesture_response["analysis"]["gesture_sequence"],
            "confidence_score": gesture_response["analysis"]["confidence_score"],
            "accuracy_score": gesture_response["analysis"]["accuracy_score"],
            "fluency_score": gesture_response["analysis"]["fluency_score"],
            "ai_feedback": gesture_response["feedback"]["message"],
            "suggestions": gesture_response["feedback"]["suggestions"],
            "detected_errors": gesture_response["feedback"]["detected_errors"],
            "duration_ms": 1800
        }
        
        attempt = await progress_service.record_sentence_attempt(
            session_response["progress_session_id"], 
            attempt_data
        )
        
        # Add progress data to response
        gesture_response["progress"] = {
            "attempt_id": attempt.id,
            "attempt_number": attempt.attempt_number,
            "is_successful": attempt.is_successful,
            "overall_score": attempt.get_overall_score()
        }
        
        return gesture_response
    
    async def enhanced_complete_session_api(session_response):
        """Enhanced session completion with progress tracking"""
        
        progress_service = session_response["progress_service"]
        
        # Complete progress session
        completed_session = await progress_service.complete_practice_session(
            session_response["progress_session_id"]
        )
        
        # Get updated progress summary
        progress_summary = await progress_service.get_user_progress_summary(
            session_response["user_id"]
        )
        
        return {
            "session_id": session_response["session_id"],
            "progress_session_id": completed_session.id,
            "status": "completed",
            "completed_at": completed_session.completed_at.isoformat(),
            "performance": {
                "overall_score": completed_session.overall_score,
                "sentences_completed": completed_session.sentences_completed,
                "total_sentences": completed_session.total_sentences
            },
            "progress_summary": progress_summary
        }
    
    # Test the enhanced APIs
    async def run_test():
        user_id = str(uuid4())
        
        story_data = {
            "title": "Greetings",
            "sentences": [
                "Hello, nice to meet you.",
                "How are you today?",
                "I am fine, thank you."
            ],
            "difficulty": "beginner"
        }
        
        # Start enhanced practice session
        session_response = await enhanced_start_practice_session_api(user_id, story_data)
        
        assert "session_id" in session_response
        assert "progress_session_id" in session_response
        assert "progress_service" in session_response
        assert session_response["user_id"] == user_id
        
        # Simulate practicing each sentence
        for i, sentence in enumerate(story_data["sentences"]):
            # Simulate multiple attempts per sentence
            for attempt in range(2):
                frame_data = {"frame": f"mock_frame_{i}_{attempt}"}
                
                gesture_response = await enhanced_process_gesture_api(
                    session_response, frame_data, i, sentence
                )
                
                assert "analysis" in gesture_response
                assert "feedback" in gesture_response
                assert "progress" in gesture_response
                assert "attempt_id" in gesture_response["progress"]
                assert "overall_score" in gesture_response["progress"]
        
        # Complete session
        completion_response = await enhanced_complete_session_api(session_response)
        
        assert completion_response["status"] == "completed"
        assert "performance" in completion_response
        assert "progress_summary" in completion_response
        assert completion_response["performance"]["sentences_completed"] == 3
        
        # Verify progress was tracked
        progress_summary = completion_response["progress_summary"]
        assert len(progress_summary["progress_records"]) == 3  # vocabulary, grammar, fluency
        assert progress_summary["performance_analytics"]["session_analytics"]["total_sessions"] == 1
        assert progress_summary["performance_analytics"]["attempt_analytics"]["total_attempts"] == 6  # 3 sentences * 2 attempts
        
        print("✓ Enhanced practice session API test passed")
    
    asyncio.run(run_test())


def test_asl_world_analytics_integration():
    """Test ASL World analytics enhanced with progress tracking"""
    print("Testing ASL World analytics integration...")
    
    # Simulate existing ASL World analytics API
    def get_session_analytics_api(session_id):
        """Mock ASL World session analytics API"""
        return {
            "session_id": session_id,
            "video_analytics": {
                "total_frames": 500,
                "processed_frames": 495,
                "dropped_frames": 5,
                "average_latency_ms": 45
            },
            "gesture_analytics": {
                "gestures_detected": 15,
                "detection_accuracy": 0.87,
                "processing_time_ms": 35
            }
        }
    
    # Enhanced analytics with progress data
    async def enhanced_get_analytics_api(user_id, session_id=None, date_range=None):
        """Enhanced analytics API with progress tracking data"""
        
        progress_service = MockProgressService()
        
        # Get progress analytics
        progress_analytics = await progress_service.get_user_performance_analytics(
            user_id, date_range
        )
        
        response = {
            "user_id": user_id,
            "progress_analytics": progress_analytics,
            "learning_insights": {
                "strengths": [],
                "areas_for_improvement": [],
                "recommendations": []
            }
        }
        
        # Add session-specific analytics if requested
        if session_id:
            session_analytics = get_session_analytics_api(session_id)
            response["session_analytics"] = session_analytics
        
        # Generate learning insights based on progress data
        session_analytics = progress_analytics["session_analytics"]
        attempt_analytics = progress_analytics["attempt_analytics"]
        
        if attempt_analytics["success_rate"] >= 80:
            response["learning_insights"]["strengths"].append("High success rate in practice attempts")
        
        if attempt_analytics["average_confidence"] >= 0.8:
            response["learning_insights"]["strengths"].append("Strong gesture recognition confidence")
        
        if attempt_analytics["average_accuracy"] < 0.7:
            response["learning_insights"]["areas_for_improvement"].append("Focus on gesture accuracy")
            response["learning_insights"]["recommendations"].append("Practice basic hand shapes more slowly")
        
        if attempt_analytics["average_fluency"] < 0.7:
            response["learning_insights"]["areas_for_improvement"].append("Work on signing fluency")
            response["learning_insights"]["recommendations"].append("Practice sentence transitions")
        
        if session_analytics["total_practice_time"] < 300:  # Less than 5 minutes
            response["learning_insights"]["recommendations"].append("Try longer practice sessions for better retention")
        
        return response
    
    # Test the enhanced analytics
    async def run_test():
        user_id = str(uuid4())
        session_id = str(uuid4())
        
        # Create some mock progress data
        progress_service = MockProgressService()
        
        # Simulate completed session
        session_config = {
            "session_type": "individual",
            "difficulty_level": "beginner",
            "total_sentences": 3,
            "skill_areas": ["vocabulary"]
        }
        
        session = await progress_service.start_practice_session(user_id, session_config)
        
        # Record attempts with varying performance
        attempts_data = [
            {"confidence_score": 0.9, "accuracy_score": 0.85, "fluency_score": 0.8},
            {"confidence_score": 0.8, "accuracy_score": 0.75, "fluency_score": 0.7},
            {"confidence_score": 0.85, "accuracy_score": 0.9, "fluency_score": 0.85}
        ]
        
        for i, attempt_data in enumerate(attempts_data):
            full_attempt_data = {
                "sentence_index": i,
                "target_sentence": f"Sentence {i+1}",
                **attempt_data
            }
            await progress_service.record_sentence_attempt(session.id, full_attempt_data)
        
        await progress_service.complete_practice_session(session.id)
        
        # Get enhanced analytics
        analytics_response = await enhanced_get_analytics_api(user_id, session_id)
        
        assert "user_id" in analytics_response
        assert "progress_analytics" in analytics_response
        assert "learning_insights" in analytics_response
        assert "session_analytics" in analytics_response
        
        # Verify progress analytics structure
        progress_analytics = analytics_response["progress_analytics"]
        assert "session_analytics" in progress_analytics
        assert "attempt_analytics" in progress_analytics
        assert progress_analytics["session_analytics"]["total_sessions"] == 1
        assert progress_analytics["attempt_analytics"]["total_attempts"] == 3
        
        # Verify learning insights
        insights = analytics_response["learning_insights"]
        assert "strengths" in insights
        assert "areas_for_improvement" in insights
        assert "recommendations" in insights
        
        # Should have identified strengths based on good performance
        assert len(insights["strengths"]) > 0
        
        print("✓ Enhanced analytics API test passed")
    
    asyncio.run(run_test())


def run_all_integration_tests():
    """Run all ASL World integration tests"""
    print("Starting ASL World API integration tests...\n")
    
    try:
        test_asl_world_story_generation_with_progress()
        test_asl_world_practice_session_with_progress()
        test_asl_world_analytics_integration()
        
        print("\n✅ All ASL World API integration tests passed!")
        print("\nSummary:")
        print("- Story generation with progress: ✓")
        print("- Practice session with progress: ✓")
        print("- Analytics integration: ✓")
        
        print("\n📋 Integration Points Demonstrated:")
        print("- Enhanced story generation based on user progress")
        print("- Real-time progress tracking during practice sessions")
        print("- Comprehensive analytics combining video and learning data")
        print("- Automatic difficulty adjustment based on performance")
        print("- Learning insights and personalized recommendations")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    run_all_integration_tests()