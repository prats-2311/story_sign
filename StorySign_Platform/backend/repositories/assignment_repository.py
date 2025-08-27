"""
Repository layer for assignment management
Handles database operations for assignments and submissions
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from .base_repository import BaseRepository
from models.assignments import Assignment, AssignmentSubmission, AssignmentType, AssignmentStatus, SubmissionStatus
from models.collaborative import LearningGroup, GroupMembership


class AssignmentRepository(BaseRepository):
    """Repository for assignment operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Assignment)
    
    async def create_assignment(
        self,
        creator_id: str,
        group_id: str,
        title: str,
        assignment_type: str = AssignmentType.PRACTICE_SESSION.value,
        **kwargs
    ) -> Assignment:
        """Create a new assignment"""
        assignment_data = {
            "creator_id": creator_id,
            "group_id": group_id,
            "title": title,
            "assignment_type": assignment_type,
            **kwargs
        }
        
        assignment = Assignment(**assignment_data)
        self.session.add(assignment)
        await self.session.flush()
        return assignment
    
    async def get_group_assignments(
        self,
        group_id: str,
        status_filter: str = None,
        include_drafts: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Assignment]:
        """Get assignments for a specific group"""
        query = select(Assignment).where(Assignment.group_id == group_id)
        
        if status_filter:
            query = query.where(Assignment.status == status_filter)
        elif not include_drafts:
            query = query.where(Assignment.status != AssignmentStatus.DRAFT.value)
        
        query = query.order_by(Assignment.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_assignments_by_creator(
        self,
        creator_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Assignment]:
        """Get assignments created by a specific user"""
        query = select(Assignment).where(Assignment.creator_id == creator_id)
        query = query.order_by(Assignment.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_available_assignments_for_student(
        self,
        student_id: str,
        group_ids: List[str] = None
    ) -> List[Assignment]:
        """Get assignments available to a student"""
        query = select(Assignment).where(
            and_(
                Assignment.status.in_([AssignmentStatus.PUBLISHED.value, AssignmentStatus.ACTIVE.value]),
                or_(
                    Assignment.available_from.is_(None),
                    Assignment.available_from <= datetime.utcnow()
                ),
                or_(
                    Assignment.available_until.is_(None),
                    Assignment.available_until >= datetime.utcnow()
                )
            )
        )
        
        if group_ids:
            query = query.where(Assignment.group_id.in_(group_ids))
        
        query = query.order_by(Assignment.due_date.asc().nullslast(), Assignment.created_at.desc())
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_overdue_assignments(self, days_overdue: int = 1) -> List[Assignment]:
        """Get assignments that are overdue"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_overdue)
        
        query = select(Assignment).where(
            and_(
                Assignment.due_date < cutoff_date,
                Assignment.status.in_([AssignmentStatus.PUBLISHED.value, AssignmentStatus.ACTIVE.value])
            )
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def publish_assignment(self, assignment_id: str) -> Optional[Assignment]:
        """Publish an assignment (make it available to students)"""
        assignment = await self.get_by_id(assignment_id)
        if not assignment:
            return None
        
        assignment.status = AssignmentStatus.PUBLISHED.value
        assignment.published_at = datetime.utcnow()
        
        await self.session.flush()
        return assignment
    
    async def update_assignment_stats(self, assignment_id: str) -> None:
        """Update assignment statistics (submission counts, average score)"""
        # Get submission statistics
        submission_stats = await self.session.execute(
            select(
                func.count(AssignmentSubmission.id).label('total_submissions'),
                func.count(
                    AssignmentSubmission.id
                ).filter(
                    AssignmentSubmission.status.in_([
                        SubmissionStatus.COMPLETED.value,
                        SubmissionStatus.REVIEWED.value
                    ])
                ).label('completed_submissions'),
                func.avg(AssignmentSubmission.score).label('average_score')
            ).where(AssignmentSubmission.assignment_id == assignment_id)
        )
        
        stats = submission_stats.first()
        
        # Update assignment
        await self.session.execute(
            update(Assignment)
            .where(Assignment.id == assignment_id)
            .values(
                total_submissions=stats.total_submissions or 0,
                completed_submissions=stats.completed_submissions or 0,
                average_score=stats.average_score
            )
        )


class AssignmentSubmissionRepository(BaseRepository):
    """Repository for assignment submission operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, AssignmentSubmission)
    
    async def create_submission(
        self,
        assignment_id: str,
        student_id: str,
        **kwargs
    ) -> AssignmentSubmission:
        """Create a new assignment submission"""
        # Get current attempt number
        existing_submissions = await self.session.execute(
            select(func.max(AssignmentSubmission.attempt_number))
            .where(
                and_(
                    AssignmentSubmission.assignment_id == assignment_id,
                    AssignmentSubmission.student_id == student_id
                )
            )
        )
        
        max_attempt = existing_submissions.scalar() or 0
        
        submission_data = {
            "assignment_id": assignment_id,
            "student_id": student_id,
            "attempt_number": max_attempt + 1,
            **kwargs
        }
        
        submission = AssignmentSubmission(**submission_data)
        self.session.add(submission)
        await self.session.flush()
        return submission
    
    async def get_student_submission(
        self,
        assignment_id: str,
        student_id: str,
        attempt_number: int = None
    ) -> Optional[AssignmentSubmission]:
        """Get a student's submission for an assignment"""
        query = select(AssignmentSubmission).where(
            and_(
                AssignmentSubmission.assignment_id == assignment_id,
                AssignmentSubmission.student_id == student_id
            )
        )
        
        if attempt_number:
            query = query.where(AssignmentSubmission.attempt_number == attempt_number)
        else:
            # Get latest attempt
            query = query.order_by(AssignmentSubmission.attempt_number.desc())
        
        result = await self.session.execute(query)
        return result.scalars().first()
    
    async def get_assignment_submissions(
        self,
        assignment_id: str,
        status_filter: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AssignmentSubmission]:
        """Get all submissions for an assignment"""
        query = select(AssignmentSubmission).where(
            AssignmentSubmission.assignment_id == assignment_id
        )
        
        if status_filter:
            query = query.where(AssignmentSubmission.status == status_filter)
        
        query = query.order_by(AssignmentSubmission.submitted_at.desc().nullslast())
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_student_submissions(
        self,
        student_id: str,
        group_ids: List[str] = None,
        status_filter: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[AssignmentSubmission]:
        """Get submissions by a student"""
        query = select(AssignmentSubmission).options(
            selectinload(AssignmentSubmission.assignment)
        ).where(AssignmentSubmission.student_id == student_id)
        
        if group_ids:
            query = query.join(Assignment).where(Assignment.group_id.in_(group_ids))
        
        if status_filter:
            query = query.where(AssignmentSubmission.status == status_filter)
        
        query = query.order_by(AssignmentSubmission.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def start_submission(
        self,
        assignment_id: str,
        student_id: str
    ) -> AssignmentSubmission:
        """Start a new submission or resume existing one"""
        # Check for existing in-progress submission
        existing = await self.get_student_submission(assignment_id, student_id)
        
        if existing and existing.status == SubmissionStatus.IN_PROGRESS.value:
            return existing
        
        # Create new submission
        submission = await self.create_submission(
            assignment_id=assignment_id,
            student_id=student_id,
            status=SubmissionStatus.IN_PROGRESS.value,
            started_at=datetime.utcnow()
        )
        
        return submission
    
    async def submit_assignment(
        self,
        submission_id: str,
        practice_session_id: str = None,
        collaborative_session_id: str = None,
        performance_metrics: Dict[str, Any] = None
    ) -> Optional[AssignmentSubmission]:
        """Submit an assignment for review"""
        submission = await self.get_by_id(submission_id)
        if not submission:
            return None
        
        # Update submission
        submission.status = SubmissionStatus.SUBMITTED.value
        submission.submitted_at = datetime.utcnow()
        submission.practice_session_id = practice_session_id
        submission.collaborative_session_id = collaborative_session_id
        submission.performance_metrics = performance_metrics
        
        # Calculate time spent
        if submission.started_at:
            time_spent = (datetime.utcnow() - submission.started_at).total_seconds()
            submission.time_spent = int(time_spent)
        
        # Check if submission is late
        if submission.assignment.due_date:
            submission.is_late = datetime.utcnow() > submission.assignment.due_date.replace(tzinfo=None)
        
        await self.session.flush()
        return submission
    
    async def grade_submission(
        self,
        submission_id: str,
        reviewer_id: str,
        score: float = None,
        feedback: str = None,
        meets_requirements: bool = None
    ) -> Optional[AssignmentSubmission]:
        """Grade a submission"""
        submission = await self.get_by_id(submission_id)
        if not submission:
            return None
        
        submission.status = SubmissionStatus.REVIEWED.value
        submission.reviewed_by = reviewer_id
        submission.reviewed_at = datetime.utcnow()
        submission.manual_grade_score = score
        submission.feedback = feedback
        submission.meets_requirements = meets_requirements
        
        # Calculate final score
        submission.score = submission.calculate_final_score()
        
        # Mark as completed if requirements are met
        if meets_requirements or (score and score >= (submission.assignment.min_score_required or 0.0)):
            submission.status = SubmissionStatus.COMPLETED.value
        
        await self.session.flush()
        return submission
    
    async def auto_grade_submission(
        self,
        submission_id: str,
        auto_score: float,
        ai_feedback: str = None
    ) -> Optional[AssignmentSubmission]:
        """Automatically grade a submission based on performance"""
        submission = await self.get_by_id(submission_id)
        if not submission:
            return None
        
        submission.auto_grade_score = auto_score
        submission.ai_feedback = ai_feedback
        
        # If auto-grading is enabled, calculate final score
        if submission.assignment.auto_grade:
            submission.score = submission.calculate_final_score()
            
            # Check if meets requirements
            min_score = submission.assignment.min_score_required or 0.0
            if auto_score >= min_score:
                submission.meets_requirements = True
                submission.status = SubmissionStatus.COMPLETED.value
        
        await self.session.flush()
        return submission
    
    async def get_submission_statistics(
        self,
        assignment_id: str
    ) -> Dict[str, Any]:
        """Get statistics for assignment submissions"""
        stats_query = await self.session.execute(
            select(
                func.count(AssignmentSubmission.id).label('total_submissions'),
                func.count(AssignmentSubmission.id).filter(
                    AssignmentSubmission.status == SubmissionStatus.NOT_STARTED.value
                ).label('not_started'),
                func.count(AssignmentSubmission.id).filter(
                    AssignmentSubmission.status == SubmissionStatus.IN_PROGRESS.value
                ).label('in_progress'),
                func.count(AssignmentSubmission.id).filter(
                    AssignmentSubmission.status == SubmissionStatus.SUBMITTED.value
                ).label('submitted'),
                func.count(AssignmentSubmission.id).filter(
                    AssignmentSubmission.status == SubmissionStatus.COMPLETED.value
                ).label('completed'),
                func.avg(AssignmentSubmission.score).label('average_score'),
                func.count(AssignmentSubmission.id).filter(
                    AssignmentSubmission.is_late == True
                ).label('late_submissions')
            ).where(AssignmentSubmission.assignment_id == assignment_id)
        )
        
        stats = stats_query.first()
        
        return {
            "total_submissions": stats.total_submissions or 0,
            "not_started": stats.not_started or 0,
            "in_progress": stats.in_progress or 0,
            "submitted": stats.submitted or 0,
            "completed": stats.completed or 0,
            "completion_rate": (stats.completed / stats.total_submissions * 100) if stats.total_submissions else 0,
            "average_score": float(stats.average_score) if stats.average_score else None,
            "late_submissions": stats.late_submissions or 0
        }
    
    async def get_overdue_submissions(
        self,
        days_overdue: int = 1
    ) -> List[AssignmentSubmission]:
        """Get submissions that are overdue"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_overdue)
        
        query = select(AssignmentSubmission).options(
            selectinload(AssignmentSubmission.assignment)
        ).join(Assignment).where(
            and_(
                Assignment.due_date < cutoff_date,
                AssignmentSubmission.status.in_([
                    SubmissionStatus.NOT_STARTED.value,
                    SubmissionStatus.IN_PROGRESS.value
                ])
            )
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()