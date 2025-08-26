"""
Repository for learning progress tracking operations
Provides data access layer for practice sessions, attempts, and user progress
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import and_, or_, func, desc, asc, text, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select

from models.progress import PracticeSession, SentenceAttempt, UserProgress


class ProgressRepository:
    """
    Repository for learning progress tracking operations
    Handles CRUD operations and analytics queries for progress data
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session
        
        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
    
    # Practice Session Operations
    
    async def create_practice_session(self, session_data: Dict[str, Any]) -> PracticeSession:
        """
        Create a new practice session
        
        Args:
            session_data: Dictionary containing session data
            
        Returns:
            Created PracticeSession instance
        """
        session = PracticeSession(**session_data)
        self.session.add(session)
        await self.session.flush()
        return session
    
    async def get_practice_session(self, session_id: str) -> Optional[PracticeSession]:
        """
        Get practice session by ID
        
        Args:
            session_id: Session ID
            
        Returns:
            PracticeSession instance or None
        """
        result = await self.session.execute(
            select(PracticeSession).where(PracticeSession.id == session_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_practice_sessions(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
        session_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[PracticeSession]:
        """
        Get practice sessions for a user with filtering
        
        Args:
            user_id: User ID
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            status: Filter by session status
            session_type: Filter by session type
            start_date: Filter sessions after this date
            end_date: Filter sessions before this date
            
        Returns:
            List of PracticeSession instances
        """
        query = select(PracticeSession).where(PracticeSession.user_id == user_id)
        
        # Apply filters
        if status:
            query = query.where(PracticeSession.status == status)
        
        if session_type:
            query = query.where(PracticeSession.session_type == session_type)
        
        if start_date:
            query = query.where(PracticeSession.created_at >= start_date)
        
        if end_date:
            query = query.where(PracticeSession.created_at <= end_date)
        
        # Order by creation date (newest first) and apply pagination
        query = query.order_by(desc(PracticeSession.created_at)).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update_practice_session(
        self,
        session_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[PracticeSession]:
        """
        Update practice session
        
        Args:
            session_id: Session ID
            update_data: Dictionary containing fields to update
            
        Returns:
            Updated PracticeSession instance or None
        """
        session = await self.get_practice_session(session_id)
        if not session:
            return None
        
        for key, value in update_data.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        await self.session.flush()
        return session
    
    async def complete_practice_session(
        self,
        session_id: str,
        completion_data: Dict[str, Any]
    ) -> Optional[PracticeSession]:
        """
        Mark practice session as completed with final metrics
        
        Args:
            session_id: Session ID
            completion_data: Final session metrics and data
            
        Returns:
            Updated PracticeSession instance or None
        """
        completion_data.update({
            "status": "completed",
            "completed_at": datetime.now()
        })
        
        # Calculate duration if not provided
        session = await self.get_practice_session(session_id)
        if session and "duration_seconds" not in completion_data:
            if session.started_at:
                duration = datetime.now() - session.started_at
                completion_data["duration_seconds"] = int(duration.total_seconds())
        
        return await self.update_practice_session(session_id, completion_data)
    
    # Sentence Attempt Operations
    
    async def create_sentence_attempt(self, attempt_data: Dict[str, Any]) -> SentenceAttempt:
        """
        Create a new sentence attempt
        
        Args:
            attempt_data: Dictionary containing attempt data
            
        Returns:
            Created SentenceAttempt instance
        """
        attempt = SentenceAttempt(**attempt_data)
        self.session.add(attempt)
        await self.session.flush()
        return attempt
    
    async def get_sentence_attempt(self, attempt_id: str) -> Optional[SentenceAttempt]:
        """
        Get sentence attempt by ID
        
        Args:
            attempt_id: Attempt ID
            
        Returns:
            SentenceAttempt instance or None
        """
        result = await self.session.execute(
            select(SentenceAttempt).where(SentenceAttempt.id == attempt_id)
        )
        return result.scalar_one_or_none()
    
    async def get_session_attempts(
        self,
        session_id: str,
        sentence_index: Optional[int] = None
    ) -> List[SentenceAttempt]:
        """
        Get all attempts for a practice session
        
        Args:
            session_id: Practice session ID
            sentence_index: Optional filter by sentence index
            
        Returns:
            List of SentenceAttempt instances
        """
        query = select(SentenceAttempt).where(SentenceAttempt.session_id == session_id)
        
        if sentence_index is not None:
            query = query.where(SentenceAttempt.sentence_index == sentence_index)
        
        query = query.order_by(SentenceAttempt.sentence_index, SentenceAttempt.attempt_number)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_user_attempts(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[SentenceAttempt]:
        """
        Get sentence attempts for a user across all sessions
        
        Args:
            user_id: User ID
            limit: Maximum number of attempts to return
            offset: Number of attempts to skip
            start_date: Filter attempts after this date
            end_date: Filter attempts before this date
            
        Returns:
            List of SentenceAttempt instances
        """
        query = (
            select(SentenceAttempt)
            .join(PracticeSession)
            .where(PracticeSession.user_id == user_id)
        )
        
        if start_date:
            query = query.where(SentenceAttempt.attempted_at >= start_date)
        
        if end_date:
            query = query.where(SentenceAttempt.attempted_at <= end_date)
        
        query = query.order_by(desc(SentenceAttempt.attempted_at)).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    # User Progress Operations
    
    async def get_user_progress(
        self,
        user_id: str,
        skill_area: Optional[str] = None
    ) -> List[UserProgress]:
        """
        Get user progress records
        
        Args:
            user_id: User ID
            skill_area: Optional filter by specific skill area
            
        Returns:
            List of UserProgress instances
        """
        query = select(UserProgress).where(UserProgress.user_id == user_id)
        
        if skill_area:
            query = query.where(UserProgress.skill_area == skill_area)
        
        query = query.order_by(UserProgress.skill_area)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_or_create_user_progress(
        self,
        user_id: str,
        skill_area: str,
        skill_category: Optional[str] = None
    ) -> UserProgress:
        """
        Get existing user progress or create new one
        
        Args:
            user_id: User ID
            skill_area: Skill area name
            skill_category: Optional skill category
            
        Returns:
            UserProgress instance
        """
        result = await self.session.execute(
            select(UserProgress).where(
                and_(
                    UserProgress.user_id == user_id,
                    UserProgress.skill_area == skill_area
                )
            )
        )
        
        progress = result.scalar_one_or_none()
        
        if not progress:
            progress = UserProgress(
                user_id=user_id,
                skill_area=skill_area,
                skill_category=skill_category
            )
            self.session.add(progress)
            await self.session.flush()
        
        return progress
    
    async def update_user_progress(
        self,
        user_id: str,
        skill_area: str,
        session_data: Dict[str, Any]
    ) -> UserProgress:
        """
        Update user progress based on session performance
        
        Args:
            user_id: User ID
            skill_area: Skill area to update
            session_data: Session performance data
            
        Returns:
            Updated UserProgress instance
        """
        progress = await self.get_or_create_user_progress(user_id, skill_area)
        
        # Update session counts
        progress.total_sessions += 1
        
        # Update practice time
        if "duration_seconds" in session_data:
            progress.total_practice_time += session_data["duration_seconds"]
        
        # Update attempt counts
        if "total_attempts" in session_data:
            progress.total_attempts += session_data["total_attempts"]
        
        if "successful_attempts" in session_data:
            progress.successful_attempts += session_data["successful_attempts"]
        
        # Update average scores
        if "average_score" in session_data:
            self._update_running_average(
                progress, "average_score", session_data["average_score"]
            )
        
        if "average_confidence" in session_data:
            self._update_running_average(
                progress, "average_confidence", session_data["average_confidence"]
            )
        
        if "average_accuracy" in session_data:
            self._update_running_average(
                progress, "average_accuracy", session_data["average_accuracy"]
            )
        
        if "average_fluency" in session_data:
            self._update_running_average(
                progress, "average_fluency", session_data["average_fluency"]
            )
        
        # Update experience points and level
        if "experience_gained" in session_data:
            progress.experience_points += session_data["experience_gained"]
            progress.current_level = self._calculate_level_from_experience(
                progress.experience_points
            )
        
        # Update streak
        progress.update_streak(datetime.now())
        
        await self.session.flush()
        return progress
    
    def _update_running_average(
        self,
        progress: UserProgress,
        field_name: str,
        new_value: float
    ) -> None:
        """
        Update running average for a progress field
        
        Args:
            progress: UserProgress instance
            field_name: Name of the field to update
            new_value: New value to incorporate into average
        """
        current_avg = getattr(progress, field_name)
        
        if current_avg is None:
            setattr(progress, field_name, new_value)
        else:
            # Simple running average based on session count
            sessions = progress.total_sessions
            new_avg = ((current_avg * (sessions - 1)) + new_value) / sessions
            setattr(progress, field_name, new_avg)
    
    def _calculate_level_from_experience(self, experience_points: float) -> float:
        """
        Calculate skill level from experience points
        Uses exponential curve: level = sqrt(experience / 100)
        
        Args:
            experience_points: Total experience points
            
        Returns:
            Skill level (0.0 to 10.0)
        """
        import math
        level = math.sqrt(experience_points / 100.0)
        return min(10.0, level)
    
    # Analytics Queries
    
    async def get_user_performance_analytics(
        self,
        user_id: str,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        skill_area: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive performance analytics for a user
        
        Args:
            user_id: User ID
            date_range: Optional tuple of (start_date, end_date)
            skill_area: Optional filter by skill area
            
        Returns:
            Dictionary containing analytics data
        """
        # Base query for sessions
        session_query = select(PracticeSession).where(PracticeSession.user_id == user_id)
        
        if date_range:
            start_date, end_date = date_range
            session_query = session_query.where(
                and_(
                    PracticeSession.created_at >= start_date,
                    PracticeSession.created_at <= end_date
                )
            )
        
        # Get session statistics
        session_stats_query = select(
            func.count(PracticeSession.id).label("total_sessions"),
            func.sum(PracticeSession.duration_seconds).label("total_practice_time"),
            func.avg(PracticeSession.overall_score).label("avg_session_score"),
            func.sum(PracticeSession.sentences_completed).label("total_sentences"),
            func.count(
                case((PracticeSession.status == "completed", 1))
            ).label("completed_sessions")
        ).where(PracticeSession.user_id == user_id)
        
        if date_range:
            start_date, end_date = date_range
            session_stats_query = session_stats_query.where(
                and_(
                    PracticeSession.created_at >= start_date,
                    PracticeSession.created_at <= end_date
                )
            )
        
        session_stats_result = await self.session.execute(session_stats_query)
        session_stats = session_stats_result.first()
        
        # Get attempt statistics
        attempt_stats_query = select(
            func.count(SentenceAttempt.id).label("total_attempts"),
            func.avg(SentenceAttempt.confidence_score).label("avg_confidence"),
            func.avg(SentenceAttempt.accuracy_score).label("avg_accuracy"),
            func.avg(SentenceAttempt.fluency_score).label("avg_fluency"),
            func.count(
                case((SentenceAttempt.is_successful == True, 1))
            ).label("successful_attempts")
        ).join(PracticeSession).where(PracticeSession.user_id == user_id)
        
        if date_range:
            start_date, end_date = date_range
            attempt_stats_query = attempt_stats_query.where(
                and_(
                    SentenceAttempt.attempted_at >= start_date,
                    SentenceAttempt.attempted_at <= end_date
                )
            )
        
        attempt_stats_result = await self.session.execute(attempt_stats_query)
        attempt_stats = attempt_stats_result.first()
        
        # Get progress data
        progress_data = await self.get_user_progress(user_id, skill_area)
        
        # Calculate success rate
        success_rate = 0.0
        if attempt_stats.total_attempts and attempt_stats.total_attempts > 0:
            success_rate = (attempt_stats.successful_attempts / attempt_stats.total_attempts) * 100.0
        
        return {
            "user_id": user_id,
            "date_range": {
                "start": date_range[0].isoformat() if date_range else None,
                "end": date_range[1].isoformat() if date_range else None
            },
            "session_analytics": {
                "total_sessions": session_stats.total_sessions or 0,
                "completed_sessions": session_stats.completed_sessions or 0,
                "total_practice_time": session_stats.total_practice_time or 0,
                "average_session_score": float(session_stats.avg_session_score) if session_stats.avg_session_score else 0.0,
                "total_sentences_practiced": session_stats.total_sentences or 0
            },
            "attempt_analytics": {
                "total_attempts": attempt_stats.total_attempts or 0,
                "successful_attempts": attempt_stats.successful_attempts or 0,
                "success_rate": success_rate,
                "average_confidence": float(attempt_stats.avg_confidence) if attempt_stats.avg_confidence else 0.0,
                "average_accuracy": float(attempt_stats.avg_accuracy) if attempt_stats.avg_accuracy else 0.0,
                "average_fluency": float(attempt_stats.avg_fluency) if attempt_stats.avg_fluency else 0.0
            },
            "progress_summary": [progress.get_progress_summary() for progress in progress_data]
        }
    
    async def get_skill_area_analytics(
        self,
        skill_area: str,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific skill area across all users
        
        Args:
            skill_area: Skill area to analyze
            date_range: Optional date range filter
            limit: Maximum number of users to include
            
        Returns:
            Dictionary containing skill area analytics
        """
        # Get progress data for skill area
        progress_query = select(UserProgress).where(UserProgress.skill_area == skill_area)
        
        if date_range:
            start_date, end_date = date_range
            progress_query = progress_query.where(
                and_(
                    UserProgress.last_practice_date >= start_date,
                    UserProgress.last_practice_date <= end_date
                )
            )
        
        progress_query = progress_query.order_by(desc(UserProgress.current_level)).limit(limit)
        
        progress_result = await self.session.execute(progress_query)
        progress_data = progress_result.scalars().all()
        
        # Calculate aggregate statistics
        if progress_data:
            levels = [p.current_level for p in progress_data]
            practice_times = [p.total_practice_time for p in progress_data]
            success_rates = [p.calculate_success_rate() for p in progress_data]
            
            analytics = {
                "skill_area": skill_area,
                "total_learners": len(progress_data),
                "average_level": sum(levels) / len(levels),
                "max_level": max(levels),
                "min_level": min(levels),
                "total_practice_time": sum(practice_times),
                "average_practice_time": sum(practice_times) / len(practice_times),
                "average_success_rate": sum(success_rates) / len(success_rates),
                "level_distribution": self._calculate_level_distribution(levels),
                "top_performers": [
                    {
                        "user_id": p.user_id,
                        "level": p.current_level,
                        "success_rate": p.calculate_success_rate(),
                        "practice_time": p.total_practice_time
                    }
                    for p in progress_data[:10]  # Top 10
                ]
            }
        else:
            analytics = {
                "skill_area": skill_area,
                "total_learners": 0,
                "message": "No data available for this skill area"
            }
        
        return analytics
    
    def _calculate_level_distribution(self, levels: List[float]) -> Dict[str, int]:
        """
        Calculate distribution of levels across difficulty ranges
        
        Args:
            levels: List of skill levels
            
        Returns:
            Dictionary with level distribution
        """
        distribution = {
            "beginner": 0,      # 0.0 - 3.0
            "intermediate": 0,  # 3.0 - 6.0
            "advanced": 0       # 6.0 - 10.0
        }
        
        for level in levels:
            if level < 3.0:
                distribution["beginner"] += 1
            elif level < 6.0:
                distribution["intermediate"] += 1
            else:
                distribution["advanced"] += 1
        
        return distribution
    
    async def get_learning_trends(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get learning trends for a user over specified period
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            Dictionary containing trend data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get daily session counts
        daily_sessions_query = select(
            func.date(PracticeSession.created_at).label("practice_date"),
            func.count(PracticeSession.id).label("session_count"),
            func.sum(PracticeSession.duration_seconds).label("total_time"),
            func.avg(PracticeSession.overall_score).label("avg_score")
        ).where(
            and_(
                PracticeSession.user_id == user_id,
                PracticeSession.created_at >= start_date,
                PracticeSession.created_at <= end_date
            )
        ).group_by(func.date(PracticeSession.created_at)).order_by(func.date(PracticeSession.created_at))
        
        daily_result = await self.session.execute(daily_sessions_query)
        daily_data = daily_result.all()
        
        # Get skill progression
        skill_progress = await self.get_user_progress(user_id)
        
        return {
            "user_id": user_id,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily_activity": [
                {
                    "date": str(row.practice_date),
                    "sessions": row.session_count,
                    "practice_time": row.total_time or 0,
                    "average_score": float(row.avg_score) if row.avg_score else 0.0
                }
                for row in daily_data
            ],
            "skill_progress": [progress.get_progress_summary() for progress in skill_progress],
            "total_active_days": len(daily_data),
            "consistency_score": (len(daily_data) / days) * 100.0
        }