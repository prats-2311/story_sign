"""
Repository for Harmony module data access operations
Handles database operations for emotion sessions, detections, and progress tracking
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import select, update, delete, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.base_repository import BaseRepository
from models.harmony import (
    EmotionSession, EmotionDetection, FacialLandmarks, 
    EmotionProgress, EmotionChallenge, UserChallengeProgress
)


class HarmonyRepository(BaseRepository):
    """
    Repository for Harmony module database operations
    """
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.logger = logging.getLogger(__name__)
    
    # Emotion Session Operations
    
    async def create_emotion_session(self, session_data: Dict[str, Any]) -> EmotionSession:
        """
        Create a new emotion practice session
        
        Args:
            session_data: Session data dictionary
            
        Returns:
            Created EmotionSession instance
        """
        session = EmotionSession(**session_data)
        self.db_session.add(session)
        await self.db_session.commit()
        await self.db_session.refresh(session)
        
        self.logger.info(f"Created emotion session: {session.id}")
        return session
    
    async def get_emotion_session(self, session_id: str) -> Optional[EmotionSession]:
        """
        Get emotion session by ID
        
        Args:
            session_id: Session ID
            
        Returns:
            EmotionSession instance or None
        """
        query = select(EmotionSession).where(EmotionSession.id == session_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_emotion_session_by_token(self, session_token: str) -> Optional[EmotionSession]:
        """
        Get emotion session by token
        
        Args:
            session_token: Session token
            
        Returns:
            EmotionSession instance or None
        """
        query = select(EmotionSession).where(EmotionSession.session_token == session_token)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
    
    async def update_emotion_session(self, session_id: str, update_data: Dict[str, Any]) -> Optional[EmotionSession]:
        """
        Update emotion session
        
        Args:
            session_id: Session ID
            update_data: Data to update
            
        Returns:
            Updated EmotionSession instance or None
        """
        query = (
            update(EmotionSession)
            .where(EmotionSession.id == session_id)
            .values(**update_data)
            .returning(EmotionSession)
        )
        
        result = await self.db_session.execute(query)
        await self.db_session.commit()
        
        updated_session = result.scalar_one_or_none()
        if updated_session:
            await self.db_session.refresh(updated_session)
        
        return updated_session
    
    async def delete_emotion_session(self, session_id: str) -> bool:
        """
        Delete emotion session
        
        Args:
            session_id: Session ID
            
        Returns:
            True if deleted, False if not found
        """
        query = delete(EmotionSession).where(EmotionSession.id == session_id)
        result = await self.db_session.execute(query)
        await self.db_session.commit()
        
        return result.rowcount > 0
    
    async def get_user_sessions(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[EmotionSession]:
        """
        Get user's emotion sessions
        
        Args:
            user_id: User ID
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            status: Optional status filter
            
        Returns:
            List of EmotionSession instances
        """
        query = select(EmotionSession).where(EmotionSession.user_id == user_id)
        
        if status:
            query = query.where(EmotionSession.status == status)
        
        query = query.order_by(desc(EmotionSession.created_at)).limit(limit).offset(offset)
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    # Emotion Detection Operations
    
    async def create_emotion_detection(self, detection_data: Dict[str, Any]) -> EmotionDetection:
        """
        Create a new emotion detection
        
        Args:
            detection_data: Detection data dictionary
            
        Returns:
            Created EmotionDetection instance
        """
        detection = EmotionDetection(**detection_data)
        self.db_session.add(detection)
        await self.db_session.commit()
        await self.db_session.refresh(detection)
        
        return detection
    
    async def get_session_detections(self, session_id: str) -> List[EmotionDetection]:
        """
        Get all detections for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of EmotionDetection instances
        """
        query = (
            select(EmotionDetection)
            .where(EmotionDetection.session_id == session_id)
            .order_by(EmotionDetection.created_at)
        )
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def get_detection_statistics(self, session_id: str) -> Dict[str, Any]:
        """
        Get detection statistics for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            Statistics dictionary
        """
        query = select(
            func.count(EmotionDetection.id).label('total_detections'),
            func.sum(EmotionDetection.is_target_match.cast('int')).label('target_matches'),
            func.avg(EmotionDetection.confidence_score).label('average_confidence'),
            func.max(EmotionDetection.confidence_score).label('max_confidence'),
            func.min(EmotionDetection.confidence_score).label('min_confidence')
        ).where(EmotionDetection.session_id == session_id)
        
        result = await self.db_session.execute(query)
        stats = result.first()
        
        if not stats or stats.total_detections == 0:
            return {
                'total_detections': 0,
                'target_matches': 0,
                'accuracy_percentage': 0.0,
                'average_confidence': 0.0,
                'max_confidence': 0.0,
                'min_confidence': 0.0
            }
        
        accuracy = (stats.target_matches / stats.total_detections) * 100 if stats.total_detections > 0 else 0.0
        
        return {
            'total_detections': stats.total_detections,
            'target_matches': stats.target_matches or 0,
            'accuracy_percentage': round(accuracy, 2),
            'average_confidence': round(float(stats.average_confidence or 0), 3),
            'max_confidence': round(float(stats.max_confidence or 0), 3),
            'min_confidence': round(float(stats.min_confidence or 0), 3)
        }
    
    # Facial Landmarks Operations
    
    async def create_facial_landmarks(self, landmarks_data: Dict[str, Any]) -> FacialLandmarks:
        """
        Create facial landmarks record
        
        Args:
            landmarks_data: Landmarks data dictionary
            
        Returns:
            Created FacialLandmarks instance
        """
        landmarks = FacialLandmarks(**landmarks_data)
        self.db_session.add(landmarks)
        await self.db_session.commit()
        await self.db_session.refresh(landmarks)
        
        return landmarks
    
    async def get_session_landmarks(self, session_id: str) -> List[FacialLandmarks]:
        """
        Get all landmarks for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of FacialLandmarks instances
        """
        query = (
            select(FacialLandmarks)
            .where(FacialLandmarks.session_id == session_id)
            .order_by(FacialLandmarks.created_at)
        )
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    # Emotion Progress Operations
    
    async def get_user_emotion_progress(self, user_id: str, emotion: str) -> Optional[EmotionProgress]:
        """
        Get user's progress for a specific emotion
        
        Args:
            user_id: User ID
            emotion: Emotion name
            
        Returns:
            EmotionProgress instance or None
        """
        query = select(EmotionProgress).where(
            and_(EmotionProgress.user_id == user_id, EmotionProgress.emotion == emotion)
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
    
    async def create_or_update_emotion_progress(
        self, 
        user_id: str, 
        emotion: str, 
        session_data: Dict[str, Any]
    ) -> EmotionProgress:
        """
        Create or update user's emotion progress
        
        Args:
            user_id: User ID
            emotion: Emotion name
            session_data: Session data for progress calculation
            
        Returns:
            EmotionProgress instance
        """
        # Get existing progress
        progress = await self.get_user_emotion_progress(user_id, emotion)
        
        if not progress:
            # Create new progress record
            progress_data = {
                'user_id': user_id,
                'emotion': emotion,
                'total_sessions': 1,
                'total_practice_time': session_data.get('session_duration', 0),
                'best_accuracy': session_data.get('accuracy', 0.0),
                'average_accuracy': session_data.get('accuracy', 0.0),
                'best_confidence': session_data.get('confidence', 0.0),
                'average_confidence': session_data.get('confidence', 0.0),
                'last_session_id': session_data.get('session_id'),
                'last_session_score': session_data.get('session_score', 0),
                'last_practiced_at': datetime.utcnow()
            }
            
            progress = EmotionProgress(**progress_data)
            self.db_session.add(progress)
        else:
            # Update existing progress
            new_total_sessions = progress.total_sessions + 1
            new_total_time = progress.total_practice_time + session_data.get('session_duration', 0)
            
            # Calculate new averages
            current_accuracy = session_data.get('accuracy', 0.0)
            current_confidence = session_data.get('confidence', 0.0)
            
            new_avg_accuracy = (
                (progress.average_accuracy * progress.total_sessions + current_accuracy) / 
                new_total_sessions
            )
            new_avg_confidence = (
                (progress.average_confidence * progress.total_sessions + current_confidence) / 
                new_total_sessions
            )
            
            # Update progress
            progress.total_sessions = new_total_sessions
            progress.total_practice_time = new_total_time
            progress.best_accuracy = max(progress.best_accuracy, current_accuracy)
            progress.average_accuracy = new_avg_accuracy
            progress.best_confidence = max(progress.best_confidence, current_confidence)
            progress.average_confidence = new_avg_confidence
            progress.last_session_id = session_data.get('session_id')
            progress.last_session_score = session_data.get('session_score', 0)
            progress.last_practiced_at = datetime.utcnow()
            
            # Calculate mastery percentage and skill level
            progress.mastery_percentage = self._calculate_mastery_percentage(progress)
            progress.skill_level = self._calculate_skill_level(progress)
        
        await self.db_session.commit()
        await self.db_session.refresh(progress)
        
        return progress
    
    async def get_user_all_progress(self, user_id: str) -> List[EmotionProgress]:
        """
        Get user's progress for all emotions
        
        Args:
            user_id: User ID
            
        Returns:
            List of EmotionProgress instances
        """
        query = (
            select(EmotionProgress)
            .where(EmotionProgress.user_id == user_id)
            .order_by(desc(EmotionProgress.mastery_percentage))
        )
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    # Challenge Operations
    
    async def get_active_challenges(self) -> List[EmotionChallenge]:
        """
        Get all active challenges
        
        Returns:
            List of active EmotionChallenge instances
        """
        query = select(EmotionChallenge).where(EmotionChallenge.is_active == True)
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    async def get_challenge(self, challenge_id: str) -> Optional[EmotionChallenge]:
        """
        Get challenge by ID
        
        Args:
            challenge_id: Challenge ID
            
        Returns:
            EmotionChallenge instance or None
        """
        query = select(EmotionChallenge).where(EmotionChallenge.id == challenge_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_challenge_progress(
        self, 
        user_id: str, 
        challenge_id: str
    ) -> Optional[UserChallengeProgress]:
        """
        Get user's progress on a specific challenge
        
        Args:
            user_id: User ID
            challenge_id: Challenge ID
            
        Returns:
            UserChallengeProgress instance or None
        """
        query = select(UserChallengeProgress).where(
            and_(
                UserChallengeProgress.user_id == user_id,
                UserChallengeProgress.challenge_id == challenge_id
            )
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
    
    async def create_or_update_challenge_progress(
        self,
        user_id: str,
        challenge_id: str,
        progress_data: Dict[str, Any]
    ) -> UserChallengeProgress:
        """
        Create or update user's challenge progress
        
        Args:
            user_id: User ID
            challenge_id: Challenge ID
            progress_data: Progress data
            
        Returns:
            UserChallengeProgress instance
        """
        progress = await self.get_user_challenge_progress(user_id, challenge_id)
        
        if not progress:
            # Create new progress
            progress_data.update({
                'user_id': user_id,
                'challenge_id': challenge_id
            })
            progress = UserChallengeProgress(**progress_data)
            self.db_session.add(progress)
        else:
            # Update existing progress
            for key, value in progress_data.items():
                if hasattr(progress, key):
                    setattr(progress, key, value)
        
        await self.db_session.commit()
        await self.db_session.refresh(progress)
        
        return progress
    
    async def get_user_completed_challenges(self, user_id: str) -> List[UserChallengeProgress]:
        """
        Get user's completed challenges
        
        Args:
            user_id: User ID
            
        Returns:
            List of completed UserChallengeProgress instances
        """
        query = (
            select(UserChallengeProgress)
            .where(
                and_(
                    UserChallengeProgress.user_id == user_id,
                    UserChallengeProgress.status == 'completed'
                )
            )
            .order_by(desc(UserChallengeProgress.completed_at))
        )
        
        result = await self.db_session.execute(query)
        return result.scalars().all()
    
    # Analytics and Statistics
    
    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive user statistics
        
        Args:
            user_id: User ID
            
        Returns:
            Statistics dictionary
        """
        # Get session statistics
        session_stats_query = select(
            func.count(EmotionSession.id).label('total_sessions'),
            func.sum(EmotionSession.session_duration).label('total_practice_time'),
            func.avg(EmotionSession.session_score).label('average_score'),
            func.max(EmotionSession.session_score).label('best_score')
        ).where(
            and_(
                EmotionSession.user_id == user_id,
                EmotionSession.status == 'completed'
            )
        )
        
        session_result = await self.db_session.execute(session_stats_query)
        session_stats = session_result.first()
        
        # Get emotion breakdown
        emotion_stats_query = select(
            EmotionSession.target_emotion,
            func.count(EmotionSession.id).label('session_count'),
            func.avg(EmotionSession.session_score).label('avg_score')
        ).where(
            and_(
                EmotionSession.user_id == user_id,
                EmotionSession.status == 'completed'
            )
        ).group_by(EmotionSession.target_emotion)
        
        emotion_result = await self.db_session.execute(emotion_stats_query)
        emotion_breakdown = [
            {
                'emotion': row.target_emotion,
                'session_count': row.session_count,
                'average_score': round(float(row.avg_score or 0), 1)
            }
            for row in emotion_result
        ]
        
        # Get recent sessions
        recent_sessions_query = (
            select(EmotionSession)
            .where(
                and_(
                    EmotionSession.user_id == user_id,
                    EmotionSession.status == 'completed'
                )
            )
            .order_by(desc(EmotionSession.created_at))
            .limit(10)
        )
        
        recent_result = await self.db_session.execute(recent_sessions_query)
        recent_sessions = [
            {
                'session_id': session.id,
                'target_emotion': session.target_emotion,
                'session_score': session.session_score,
                'accuracy': session.calculate_accuracy(),
                'created_at': session.created_at.isoformat()
            }
            for session in recent_result.scalars()
        ]
        
        return {
            'total_sessions': session_stats.total_sessions or 0,
            'total_practice_time': session_stats.total_practice_time or 0,
            'average_score': round(float(session_stats.average_score or 0), 1),
            'best_score': session_stats.best_score or 0,
            'emotion_breakdown': emotion_breakdown,
            'recent_sessions': recent_sessions
        }
    
    def _calculate_mastery_percentage(self, progress: EmotionProgress) -> float:
        """
        Calculate mastery percentage based on progress metrics
        
        Args:
            progress: EmotionProgress instance
            
        Returns:
            Mastery percentage (0-100)
        """
        # Weight different factors
        accuracy_weight = 0.4
        confidence_weight = 0.3
        consistency_weight = 0.2
        experience_weight = 0.1
        
        # Normalize accuracy (0-100 to 0-1)
        accuracy_score = min(progress.average_accuracy / 100, 1.0)
        
        # Confidence is already 0-1
        confidence_score = progress.average_confidence
        
        # Consistency based on difference between best and average
        consistency_score = 1.0 - min(
            abs(progress.best_accuracy - progress.average_accuracy) / 100, 1.0
        )
        
        # Experience based on number of sessions (logarithmic scale)
        import math
        experience_score = min(math.log(progress.total_sessions + 1) / math.log(50), 1.0)
        
        # Calculate weighted mastery
        mastery = (
            accuracy_score * accuracy_weight +
            confidence_score * confidence_weight +
            consistency_score * consistency_weight +
            experience_score * experience_weight
        ) * 100
        
        return round(mastery, 1)
    
    def _calculate_skill_level(self, progress: EmotionProgress) -> str:
        """
        Calculate skill level based on progress metrics
        
        Args:
            progress: EmotionProgress instance
            
        Returns:
            Skill level string
        """
        mastery = progress.mastery_percentage
        accuracy = progress.average_accuracy
        sessions = progress.total_sessions
        
        if mastery >= 90 and accuracy >= 85 and sessions >= 20:
            return "expert"
        elif mastery >= 70 and accuracy >= 70 and sessions >= 10:
            return "advanced"
        elif mastery >= 40 and accuracy >= 50 and sessions >= 5:
            return "intermediate"
        else:
            return "beginner"