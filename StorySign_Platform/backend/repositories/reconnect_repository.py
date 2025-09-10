"""
Repository for Reconnect module data access operations
Handles database operations for therapeutic movement analysis
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from repositories.base_repository import BaseRepository
from models.reconnect import (
    TherapySession, MovementAnalysis, PoseLandmarks, 
    TherapyProgress, ExerciseGoal, UserGoalProgress, JointMeasurement
)

logger = logging.getLogger(__name__)


class ReconnectRepository(BaseRepository):
    """
    Repository for Reconnect module database operations
    """
    
    def __init__(self, db_service):
        super().__init__(db_service)
        self.logger = logger
    
    # Therapy Session Operations
    
    async def create_therapy_session(
        self,
        session_token: str,
        exercise_type: str,
        difficulty_level: str = "beginner",
        user_id: Optional[str] = None,
        target_areas: Optional[List[str]] = None,
        session_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new therapy session
        
        Args:
            session_token: Unique session identifier
            exercise_type: Type of therapeutic exercise
            difficulty_level: Difficulty level
            user_id: User ID (optional)
            target_areas: Target body areas
            session_metadata: Additional metadata
            
        Returns:
            Created session data
        """
        try:
            session_id = str(uuid.uuid4())
            
            query = """
                INSERT INTO therapy_sessions (
                    id, user_id, session_token, exercise_type, difficulty_level,
                    target_areas, session_metadata, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            await self.db_service.execute_query(
                query,
                (
                    session_id,
                    user_id,
                    session_token,
                    exercise_type,
                    difficulty_level,
                    target_areas or [],
                    session_metadata or {},
                    datetime.utcnow(),
                    datetime.utcnow()
                )
            )
            
            # Retrieve the created session
            return await self.get_therapy_session(session_id)
            
        except Exception as e:
            self.logger.error(f"Error creating therapy session: {e}")
            raise
    
    async def get_therapy_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get therapy session by ID
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found
        """
        try:
            query = "SELECT * FROM therapy_sessions WHERE id = %s"
            result = await self.db_service.fetch_one(query, (session_id,))
            return dict(result) if result else None
            
        except Exception as e:
            self.logger.error(f"Error getting therapy session {session_id}: {e}")
            raise
    
    async def get_therapy_session_by_token(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Get therapy session by token
        
        Args:
            session_token: Session token
            
        Returns:
            Session data or None if not found
        """
        try:
            query = "SELECT * FROM therapy_sessions WHERE session_token = %s"
            result = await self.db_service.fetch_one(query, (session_token,))
            return dict(result) if result else None
            
        except Exception as e:
            self.logger.error(f"Error getting therapy session by token {session_token}: {e}")
            raise
    
    async def update_therapy_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update therapy session
        
        Args:
            session_id: Session ID
            updates: Fields to update
            
        Returns:
            True if successful
        """
        try:
            if not updates:
                return True
            
            # Build dynamic update query
            set_clauses = []
            values = []
            
            for field, value in updates.items():
                if field in ['session_duration', 'status', 'total_movements', 
                           'average_quality', 'session_score', 'rom_statistics', 'session_metadata']:
                    set_clauses.append(f"{field} = %s")
                    values.append(value)
            
            if not set_clauses:
                return True
            
            set_clauses.append("updated_at = %s")
            values.append(datetime.utcnow())
            values.append(session_id)
            
            query = f"UPDATE therapy_sessions SET {', '.join(set_clauses)} WHERE id = %s"
            
            await self.db_service.execute_query(query, values)
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating therapy session {session_id}: {e}")
            raise
    
    async def delete_therapy_session(self, session_id: str) -> bool:
        """
        Delete therapy session
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successful
        """
        try:
            query = "DELETE FROM therapy_sessions WHERE id = %s"
            await self.db_service.execute_query(query, (session_id,))
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting therapy session {session_id}: {e}")
            raise
    
    # Movement Analysis Operations
    
    async def create_movement_analysis(
        self,
        session_id: str,
        quality_score: float,
        smoothness_score: Optional[float] = None,
        symmetry_score: Optional[float] = None,
        range_score: Optional[float] = None,
        stability_score: Optional[float] = None,
        processing_time_ms: Optional[int] = None,
        frame_timestamp: Optional[datetime] = None,
        analysis_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create movement analysis record
        
        Args:
            session_id: Session ID
            quality_score: Overall quality score
            smoothness_score: Smoothness score
            symmetry_score: Symmetry score
            range_score: Range score
            stability_score: Stability score
            processing_time_ms: Processing time
            frame_timestamp: Frame timestamp
            analysis_metadata: Additional metadata
            
        Returns:
            Analysis ID
        """
        try:
            analysis_id = str(uuid.uuid4())
            
            query = """
                INSERT INTO movement_analyses (
                    id, session_id, quality_score, smoothness_score, symmetry_score,
                    range_score, stability_score, processing_time_ms, frame_timestamp,
                    analysis_metadata, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            await self.db_service.execute_query(
                query,
                (
                    analysis_id,
                    session_id,
                    quality_score,
                    smoothness_score,
                    symmetry_score,
                    range_score,
                    stability_score,
                    processing_time_ms,
                    frame_timestamp,
                    analysis_metadata or {},
                    datetime.utcnow(),
                    datetime.utcnow()
                )
            )
            
            return analysis_id
            
        except Exception as e:
            self.logger.error(f"Error creating movement analysis: {e}")
            raise
    
    async def get_session_analyses(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all movement analyses for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of analysis records
        """
        try:
            query = """
                SELECT * FROM movement_analyses 
                WHERE session_id = %s 
                ORDER BY created_at ASC
            """
            results = await self.db_service.fetch_all(query, (session_id,))
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Error getting session analyses for {session_id}: {e}")
            raise
    
    # Pose Landmarks Operations
    
    async def create_pose_landmarks(
        self,
        session_id: str,
        landmarks_data: List[Dict[str, Any]],
        analysis_id: Optional[str] = None,
        num_landmarks: Optional[int] = None,
        pose_confidence: Optional[float] = None,
        frame_width: Optional[int] = None,
        frame_height: Optional[int] = None,
        joint_angles: Optional[Dict[str, float]] = None,
        range_of_motion: Optional[Dict[str, float]] = None
    ) -> str:
        """
        Create pose landmarks record
        
        Args:
            session_id: Session ID
            landmarks_data: MediaPipe landmarks data
            analysis_id: Analysis ID (optional)
            num_landmarks: Number of landmarks
            pose_confidence: Pose confidence
            frame_width: Frame width
            frame_height: Frame height
            joint_angles: Joint angles
            range_of_motion: Range of motion data
            
        Returns:
            Landmarks ID
        """
        try:
            landmarks_id = str(uuid.uuid4())
            
            query = """
                INSERT INTO pose_landmarks (
                    id, session_id, analysis_id, landmarks_data, num_landmarks,
                    pose_confidence, frame_width, frame_height, joint_angles,
                    range_of_motion, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            await self.db_service.execute_query(
                query,
                (
                    landmarks_id,
                    session_id,
                    analysis_id,
                    landmarks_data,
                    num_landmarks or len(landmarks_data),
                    pose_confidence,
                    frame_width,
                    frame_height,
                    joint_angles or {},
                    range_of_motion or {},
                    datetime.utcnow(),
                    datetime.utcnow()
                )
            )
            
            return landmarks_id
            
        except Exception as e:
            self.logger.error(f"Error creating pose landmarks: {e}")
            raise
    
    # Therapy Progress Operations
    
    async def get_or_create_therapy_progress(
        self,
        user_id: str,
        exercise_type: str,
        body_area: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get or create therapy progress record
        
        Args:
            user_id: User ID
            exercise_type: Exercise type
            body_area: Body area
            
        Returns:
            Progress record
        """
        try:
            # Try to get existing progress
            query = """
                SELECT * FROM therapy_progress 
                WHERE user_id = %s AND exercise_type = %s
            """
            result = await self.db_service.fetch_one(query, (user_id, exercise_type))
            
            if result:
                return dict(result)
            
            # Create new progress record
            progress_id = str(uuid.uuid4())
            
            insert_query = """
                INSERT INTO therapy_progress (
                    id, user_id, exercise_type, body_area, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            await self.db_service.execute_query(
                insert_query,
                (
                    progress_id,
                    user_id,
                    exercise_type,
                    body_area,
                    datetime.utcnow(),
                    datetime.utcnow()
                )
            )
            
            # Return the created record
            return await self.get_therapy_progress(progress_id)
            
        except Exception as e:
            self.logger.error(f"Error getting/creating therapy progress: {e}")
            raise
    
    async def get_therapy_progress(self, progress_id: str) -> Optional[Dict[str, Any]]:
        """
        Get therapy progress by ID
        
        Args:
            progress_id: Progress ID
            
        Returns:
            Progress data or None
        """
        try:
            query = "SELECT * FROM therapy_progress WHERE id = %s"
            result = await self.db_service.fetch_one(query, (progress_id,))
            return dict(result) if result else None
            
        except Exception as e:
            self.logger.error(f"Error getting therapy progress {progress_id}: {e}")
            raise
    
    async def update_therapy_progress(
        self,
        progress_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update therapy progress
        
        Args:
            progress_id: Progress ID
            updates: Fields to update
            
        Returns:
            True if successful
        """
        try:
            if not updates:
                return True
            
            # Build dynamic update query
            set_clauses = []
            values = []
            
            allowed_fields = [
                'total_sessions', 'total_therapy_time', 'best_quality_score',
                'average_quality_score', 'initial_rom', 'current_rom', 'best_rom',
                'functional_level', 'improvement_percentage', 'last_session_id',
                'last_session_score', 'last_practiced_at', 'progress_metadata'
            ]
            
            for field, value in updates.items():
                if field in allowed_fields:
                    set_clauses.append(f"{field} = %s")
                    values.append(value)
            
            if not set_clauses:
                return True
            
            set_clauses.append("updated_at = %s")
            values.append(datetime.utcnow())
            values.append(progress_id)
            
            query = f"UPDATE therapy_progress SET {', '.join(set_clauses)} WHERE id = %s"
            
            await self.db_service.execute_query(query, values)
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating therapy progress {progress_id}: {e}")
            raise
    
    async def get_user_progress_summary(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get progress summary for all exercises for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of progress summaries
        """
        try:
            query = """
                SELECT * FROM therapy_progress 
                WHERE user_id = %s 
                ORDER BY last_practiced_at DESC
            """
            results = await self.db_service.fetch_all(query, (user_id,))
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Error getting user progress summary for {user_id}: {e}")
            raise
    
    # Joint Measurements Operations
    
    async def create_joint_measurement(
        self,
        session_id: str,
        user_id: str,
        joint_name: str,
        measurement_type: str,
        angle_degrees: float,
        range_of_motion: Optional[float] = None,
        measurement_quality: Optional[float] = None,
        exercise_phase: Optional[str] = None,
        repetition_number: Optional[int] = None,
        measurement_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create joint measurement record
        
        Args:
            session_id: Session ID
            user_id: User ID
            joint_name: Joint name
            measurement_type: Measurement type
            angle_degrees: Angle measurement
            range_of_motion: Range of motion
            measurement_quality: Measurement quality
            exercise_phase: Exercise phase
            repetition_number: Repetition number
            measurement_metadata: Additional metadata
            
        Returns:
            Measurement ID
        """
        try:
            measurement_id = str(uuid.uuid4())
            
            query = """
                INSERT INTO joint_measurements (
                    id, session_id, user_id, joint_name, measurement_type,
                    angle_degrees, range_of_motion, measurement_quality,
                    exercise_phase, repetition_number, measurement_metadata,
                    created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            await self.db_service.execute_query(
                query,
                (
                    measurement_id,
                    session_id,
                    user_id,
                    joint_name,
                    measurement_type,
                    angle_degrees,
                    range_of_motion,
                    measurement_quality,
                    exercise_phase,
                    repetition_number,
                    measurement_metadata or {},
                    datetime.utcnow(),
                    datetime.utcnow()
                )
            )
            
            return measurement_id
            
        except Exception as e:
            self.logger.error(f"Error creating joint measurement: {e}")
            raise
    
    async def get_joint_measurements_for_session(
        self,
        session_id: str,
        joint_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get joint measurements for a session
        
        Args:
            session_id: Session ID
            joint_name: Joint name filter (optional)
            
        Returns:
            List of measurements
        """
        try:
            if joint_name:
                query = """
                    SELECT * FROM joint_measurements 
                    WHERE session_id = %s AND joint_name = %s 
                    ORDER BY created_at ASC
                """
                results = await self.db_service.fetch_all(query, (session_id, joint_name))
            else:
                query = """
                    SELECT * FROM joint_measurements 
                    WHERE session_id = %s 
                    ORDER BY joint_name, created_at ASC
                """
                results = await self.db_service.fetch_all(query, (session_id,))
            
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Error getting joint measurements for session {session_id}: {e}")
            raise
    
    async def get_joint_progress_over_time(
        self,
        user_id: str,
        joint_name: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get joint progress over time
        
        Args:
            user_id: User ID
            joint_name: Joint name
            days: Number of days to look back
            
        Returns:
            List of measurements over time
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = """
                SELECT jm.*, ts.exercise_type, ts.created_at as session_date
                FROM joint_measurements jm
                JOIN therapy_sessions ts ON jm.session_id = ts.id
                WHERE jm.user_id = %s AND jm.joint_name = %s 
                AND jm.created_at >= %s
                ORDER BY jm.created_at ASC
            """
            
            results = await self.db_service.fetch_all(
                query, 
                (user_id, joint_name, cutoff_date)
            )
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Error getting joint progress over time: {e}")
            raise
    
    # Exercise Goals Operations
    
    async def get_exercise_goals(
        self,
        goal_type: Optional[str] = None,
        exercise_type: Optional[str] = None,
        is_active: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get exercise goals with optional filters
        
        Args:
            goal_type: Goal type filter
            exercise_type: Exercise type filter
            is_active: Active status filter
            
        Returns:
            List of goals
        """
        try:
            conditions = ["is_active = %s"]
            params = [is_active]
            
            if goal_type:
                conditions.append("goal_type = %s")
                params.append(goal_type)
            
            if exercise_type:
                conditions.append("exercise_type = %s")
                params.append(exercise_type)
            
            query = f"""
                SELECT * FROM exercise_goals 
                WHERE {' AND '.join(conditions)}
                ORDER BY difficulty_level, name
            """
            
            results = await self.db_service.fetch_all(query, params)
            return [dict(row) for row in results]
            
        except Exception as e:
            self.logger.error(f"Error getting exercise goals: {e}")
            raise
    
    # Statistics and Analytics
    
    async def get_user_session_statistics(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get user session statistics
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            Statistics dictionary
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Total sessions
            total_query = """
                SELECT COUNT(*) as total_sessions,
                       AVG(average_quality) as avg_quality,
                       AVG(session_score) as avg_score,
                       SUM(session_duration) as total_time
                FROM therapy_sessions 
                WHERE user_id = %s AND created_at >= %s AND status = 'completed'
            """
            
            total_stats = await self.db_service.fetch_one(
                total_query, 
                (user_id, cutoff_date)
            )
            
            # Exercise breakdown
            exercise_query = """
                SELECT exercise_type, COUNT(*) as count,
                       AVG(average_quality) as avg_quality
                FROM therapy_sessions 
                WHERE user_id = %s AND created_at >= %s AND status = 'completed'
                GROUP BY exercise_type
                ORDER BY count DESC
            """
            
            exercise_stats = await self.db_service.fetch_all(
                exercise_query,
                (user_id, cutoff_date)
            )
            
            return {
                "total_sessions": total_stats["total_sessions"] or 0,
                "average_quality": float(total_stats["avg_quality"] or 0),
                "average_score": int(total_stats["avg_score"] or 0),
                "total_time_ms": int(total_stats["total_time"] or 0),
                "exercise_breakdown": [dict(row) for row in exercise_stats]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user session statistics: {e}")
            raise