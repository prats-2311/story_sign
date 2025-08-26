"""
Progress tracking service for StorySign ASL Platform
Handles business logic for learning progress, session management, and analytics
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from models.progress import PracticeSession, SentenceAttempt, UserProgress
from repositories.progress_repository import ProgressRepository

logger = logging.getLogger(__name__)


class ProgressService:
    """
    Service for managing learning progress tracking
    Provides high-level business logic for practice sessions and user progress
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize progress service
        
        Args:
            db_session: Database session
        """
        self.db_session = db_session
        self.repository = ProgressRepository(db_session)
    
    # Practice Session Management
    
    async def start_practice_session(
        self,
        user_id: str,
        session_config: Dict[str, Any]
    ) -> PracticeSession:
        """
        Start a new practice session
        
        Args:
            user_id: ID of user starting the session
            session_config: Session configuration data
            
        Returns:
            Created PracticeSession instance
        """
        try:
            # Prepare session data
            session_data = {
                "user_id": user_id,
                "session_type": session_config.get("session_type", "individual"),
                "session_name": session_config.get("session_name"),
                "story_id": session_config.get("story_id"),
                "story_content": session_config.get("story_content"),
                "difficulty_level": session_config.get("difficulty_level", "beginner"),
                "skill_areas": session_config.get("skill_areas", []),
                "session_data": session_config.get("session_data", {}),
                "total_sentences": session_config.get("total_sentences"),
                "status": "active",
                "started_at": datetime.now()
            }
            
            session = await self.repository.create_practice_session(session_data)
            
            logger.info(f"Started practice session {session.id} for user {user_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to start practice session for user {user_id}: {e}")
            raise
    
    async def record_sentence_attempt(
        self,
        session_id: str,
        attempt_data: Dict[str, Any]
    ) -> SentenceAttempt:
        """
        Record a sentence attempt within a practice session
        
        Args:
            session_id: ID of the practice session
            attempt_data: Attempt data including scores and feedback
            
        Returns:
            Created SentenceAttempt instance
        """
        try:
            # Get current attempt number for this sentence
            existing_attempts = await self.repository.get_session_attempts(
                session_id, attempt_data.get("sentence_index")
            )
            
            attempt_number = len([
                a for a in existing_attempts 
                if a.sentence_index == attempt_data.get("sentence_index")
            ]) + 1
            
            # Prepare attempt data
            attempt_record = {
                "session_id": session_id,
                "sentence_index": attempt_data["sentence_index"],
                "target_sentence": attempt_data["target_sentence"],
                "landmark_data": attempt_data.get("landmark_data"),
                "gesture_sequence": attempt_data.get("gesture_sequence"),
                "confidence_score": attempt_data.get("confidence_score"),
                "accuracy_score": attempt_data.get("accuracy_score"),
                "fluency_score": attempt_data.get("fluency_score"),
                "ai_feedback": attempt_data.get("ai_feedback"),
                "suggestions": attempt_data.get("suggestions"),
                "detected_errors": attempt_data.get("detected_errors"),
                "duration_ms": attempt_data.get("duration_ms"),
                "attempt_number": attempt_number,
                "attempted_at": datetime.now()
            }
            
            # Determine if attempt was successful
            overall_score = self._calculate_attempt_score(attempt_record)
            attempt_record["is_successful"] = overall_score >= 0.7 if overall_score else False
            
            attempt = await self.repository.create_sentence_attempt(attempt_record)
            
            # Update session progress
            await self._update_session_progress(session_id, attempt)
            
            logger.debug(f"Recorded sentence attempt {attempt.id} for session {session_id}")
            return attempt
            
        except Exception as e:
            logger.error(f"Failed to record sentence attempt for session {session_id}: {e}")
            raise
    
    async def complete_practice_session(
        self,
        session_id: str,
        completion_data: Optional[Dict[str, Any]] = None
    ) -> PracticeSession:
        """
        Complete a practice session and update user progress
        
        Args:
            session_id: ID of the practice session
            completion_data: Optional additional completion data
            
        Returns:
            Updated PracticeSession instance
        """
        try:
            # Get session and attempts
            session = await self.repository.get_practice_session(session_id)
            if not session:
                raise ValueError(f"Practice session {session_id} not found")
            
            attempts = await self.repository.get_session_attempts(session_id)
            
            # Calculate final session metrics
            session_metrics = self._calculate_session_metrics(session, attempts)
            
            # Merge with provided completion data
            if completion_data:
                session_metrics.update(completion_data)
            
            # Complete the session
            completed_session = await self.repository.complete_practice_session(
                session_id, session_metrics
            )
            
            # Update user progress
            await self._update_user_progress_from_session(completed_session, attempts)
            
            logger.info(f"Completed practice session {session_id}")
            return completed_session
            
        except Exception as e:
            logger.error(f"Failed to complete practice session {session_id}: {e}")
            raise
    
    async def get_user_sessions(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[PracticeSession]:
        """
        Get practice sessions for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of sessions
            offset: Number of sessions to skip
            filters: Optional filters (status, type, date range)
            
        Returns:
            List of PracticeSession instances
        """
        try:
            filter_params = filters or {}
            
            sessions = await self.repository.get_user_practice_sessions(
                user_id=user_id,
                limit=limit,
                offset=offset,
                status=filter_params.get("status"),
                session_type=filter_params.get("session_type"),
                start_date=filter_params.get("start_date"),
                end_date=filter_params.get("end_date")
            )
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get sessions for user {user_id}: {e}")
            raise
    
    # Progress Analytics
    
    async def get_user_progress_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive progress summary for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary containing progress summary
        """
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
            logger.error(f"Failed to get progress summary for user {user_id}: {e}")
            raise
    
    async def get_skill_analytics(
        self,
        skill_area: str,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific skill area
        
        Args:
            skill_area: Skill area to analyze
            date_range: Optional date range filter
            
        Returns:
            Dictionary containing skill analytics
        """
        try:
            analytics = await self.repository.get_skill_area_analytics(
                skill_area, date_range
            )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get skill analytics for {skill_area}: {e}")
            raise
    
    async def get_user_performance_analytics(
        self,
        user_id: str,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        skill_area: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get detailed performance analytics for a user
        
        Args:
            user_id: User ID
            date_range: Optional date range filter
            skill_area: Optional skill area filter
            
        Returns:
            Dictionary containing performance analytics
        """
        try:
            analytics = await self.repository.get_user_performance_analytics(
                user_id, date_range, skill_area
            )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get performance analytics for user {user_id}: {e}")
            raise
    
    # Helper Methods
    
    def _calculate_attempt_score(self, attempt_data: Dict[str, Any]) -> Optional[float]:
        """
        Calculate overall score for a sentence attempt
        
        Args:
            attempt_data: Attempt data dictionary
            
        Returns:
            Overall score (0.0 to 1.0) or None
        """
        scores = []
        
        if attempt_data.get("confidence_score") is not None:
            scores.append(attempt_data["confidence_score"])
        
        if attempt_data.get("accuracy_score") is not None:
            scores.append(attempt_data["accuracy_score"])
        
        if attempt_data.get("fluency_score") is not None:
            scores.append(attempt_data["fluency_score"])
        
        if not scores:
            return None
        
        # Weighted average: accuracy (40%), confidence (30%), fluency (30%)
        if len(scores) == 3:
            return (
                attempt_data["accuracy_score"] * 0.4 +
                attempt_data["confidence_score"] * 0.3 +
                attempt_data["fluency_score"] * 0.3
            )
        else:
            return sum(scores) / len(scores)
    
    def _calculate_session_metrics(
        self,
        session: PracticeSession,
        attempts: List[SentenceAttempt]
    ) -> Dict[str, Any]:
        """
        Calculate final metrics for a completed session
        
        Args:
            session: PracticeSession instance
            attempts: List of sentence attempts
            
        Returns:
            Dictionary containing session metrics
        """
        if not attempts:
            return {
                "overall_score": 0.0,
                "sentences_completed": 0,
                "performance_metrics": {
                    "total_attempts": 0,
                    "successful_attempts": 0,
                    "average_confidence": 0.0,
                    "average_accuracy": 0.0,
                    "average_fluency": 0.0
                }
            }
        
        # Calculate attempt statistics
        total_attempts = len(attempts)
        successful_attempts = sum(1 for a in attempts if a.is_successful)
        
        # Calculate average scores
        confidence_scores = [a.confidence_score for a in attempts if a.confidence_score is not None]
        accuracy_scores = [a.accuracy_score for a in attempts if a.accuracy_score is not None]
        fluency_scores = [a.fluency_score for a in attempts if a.fluency_score is not None]
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        avg_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.0
        avg_fluency = sum(fluency_scores) / len(fluency_scores) if fluency_scores else 0.0
        
        # Calculate overall session score
        overall_score = (avg_accuracy * 0.4 + avg_confidence * 0.3 + avg_fluency * 0.3)
        
        # Count unique sentences completed
        unique_sentences = len(set(a.sentence_index for a in attempts))
        
        return {
            "overall_score": overall_score,
            "sentences_completed": unique_sentences,
            "performance_metrics": {
                "total_attempts": total_attempts,
                "successful_attempts": successful_attempts,
                "success_rate": (successful_attempts / total_attempts) * 100.0,
                "average_confidence": avg_confidence,
                "average_accuracy": avg_accuracy,
                "average_fluency": avg_fluency,
                "attempts_per_sentence": total_attempts / unique_sentences if unique_sentences > 0 else 0
            }
        }
    
    async def _update_session_progress(
        self,
        session_id: str,
        attempt: SentenceAttempt
    ) -> None:
        """
        Update session progress after a sentence attempt
        
        Args:
            session_id: Session ID
            attempt: Sentence attempt that was just recorded
        """
        try:
            # Get all attempts for this session
            attempts = await self.repository.get_session_attempts(session_id)
            
            # Count unique sentences attempted
            unique_sentences = len(set(a.sentence_index for a in attempts))
            
            # Calculate current session metrics
            successful_attempts = sum(1 for a in attempts if a.is_successful)
            
            # Update session
            update_data = {
                "sentences_completed": unique_sentences,
                "performance_metrics": {
                    "current_attempts": len(attempts),
                    "current_successful": successful_attempts,
                    "last_attempt_at": attempt.attempted_at.isoformat()
                }
            }
            
            await self.repository.update_practice_session(session_id, update_data)
            
        except Exception as e:
            logger.error(f"Failed to update session progress for {session_id}: {e}")
            # Don't raise - this is a background update
    
    async def _update_user_progress_from_session(
        self,
        session: PracticeSession,
        attempts: List[SentenceAttempt]
    ) -> None:
        """
        Update user progress based on completed session
        
        Args:
            session: Completed practice session
            attempts: List of sentence attempts from the session
        """
        try:
            # Determine skill areas to update
            skill_areas = session.skill_areas or ["general_asl"]
            
            # Calculate session performance data
            session_metrics = self._calculate_session_metrics(session, attempts)
            
            # Calculate experience gained based on performance
            experience_gained = self._calculate_experience_gained(session, session_metrics)
            
            # Update progress for each skill area
            for skill_area in skill_areas:
                progress_data = {
                    "duration_seconds": session.duration_seconds or 0,
                    "total_attempts": session_metrics["performance_metrics"]["total_attempts"],
                    "successful_attempts": session_metrics["performance_metrics"]["successful_attempts"],
                    "average_score": session.overall_score,
                    "average_confidence": session_metrics["performance_metrics"]["average_confidence"],
                    "average_accuracy": session_metrics["performance_metrics"]["average_accuracy"],
                    "average_fluency": session_metrics["performance_metrics"]["average_fluency"],
                    "experience_gained": experience_gained
                }
                
                await self.repository.update_user_progress(
                    session.user_id, skill_area, progress_data
                )
            
            logger.debug(f"Updated user progress for session {session.id}")
            
        except Exception as e:
            logger.error(f"Failed to update user progress from session {session.id}: {e}")
            # Don't raise - this is a background update
    
    def _calculate_experience_gained(
        self,
        session: PracticeSession,
        session_metrics: Dict[str, Any]
    ) -> float:
        """
        Calculate experience points gained from a session
        
        Args:
            session: Practice session
            session_metrics: Session performance metrics
            
        Returns:
            Experience points gained
        """
        base_experience = 10.0  # Base experience per session
        
        # Bonus for completion
        completion_bonus = 5.0 if session.status == "completed" else 0.0
        
        # Performance bonus based on overall score
        performance_bonus = (session.overall_score or 0.0) * 20.0
        
        # Time bonus (up to 10 points for longer sessions)
        time_bonus = min(10.0, (session.duration_seconds or 0) / 60.0 * 0.5)
        
        # Difficulty bonus
        difficulty_multiplier = {
            "beginner": 1.0,
            "intermediate": 1.5,
            "advanced": 2.0
        }.get(session.difficulty_level, 1.0)
        
        total_experience = (base_experience + completion_bonus + performance_bonus + time_bonus) * difficulty_multiplier
        
        return round(total_experience, 2)
    
    def _calculate_overall_summary(
        self,
        progress_records: List[UserProgress],
        analytics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate overall progress summary
        
        Args:
            progress_records: List of user progress records
            analytics: Performance analytics data
            
        Returns:
            Overall summary dictionary
        """
        if not progress_records:
            return {
                "total_skill_areas": 0,
                "average_level": 0.0,
                "total_experience": 0.0,
                "overall_success_rate": 0.0,
                "learning_streak": 0,
                "proficiency_level": "beginner"
            }
        
        # Calculate aggregates
        total_experience = sum(p.experience_points for p in progress_records)
        average_level = sum(p.current_level for p in progress_records) / len(progress_records)
        max_streak = max(p.learning_streak for p in progress_records)
        
        # Determine overall proficiency
        if average_level < 3.0:
            proficiency = "beginner"
        elif average_level < 6.0:
            proficiency = "intermediate"
        else:
            proficiency = "advanced"
        
        return {
            "total_skill_areas": len(progress_records),
            "average_level": round(average_level, 2),
            "total_experience": total_experience,
            "overall_success_rate": analytics["attempt_analytics"]["success_rate"],
            "learning_streak": max_streak,
            "proficiency_level": proficiency,
            "total_practice_time": analytics["session_analytics"]["total_practice_time"],
            "total_sessions": analytics["session_analytics"]["total_sessions"]
        }