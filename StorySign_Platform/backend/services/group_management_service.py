"""
Service layer for group management features
Handles business logic for educator tools, assignments, and group analytics
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.assignment_repository import AssignmentRepository, AssignmentSubmissionRepository
from repositories.notification_repository import NotificationRepository, GroupMessageRepository
from repositories.collaborative_repository import LearningGroupRepository, GroupMembershipRepository
from repositories.user_repository import UserRepository
from repositories.progress_repository import ProgressRepository
from models.assignments import Assignment, AssignmentSubmission, AssignmentType, AssignmentStatus, SubmissionStatus
from models.notifications import NotificationType, NotificationPriority
from models.collaborative import GroupRole


class GroupManagementService:
    """Service for group management and educator tools"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.assignment_repo = AssignmentRepository(session)
        self.submission_repo = AssignmentSubmissionRepository(session)
        self.notification_repo = NotificationRepository(session)
        self.message_repo = GroupMessageRepository(session)
        self.group_repo = LearningGroupRepository(session)
        self.membership_repo = GroupMembershipRepository(session)
        self.user_repo = UserRepository(session)
        self.progress_repo = ProgressRepository(session)
    
    # Assignment Management
    
    async def create_assignment(
        self,
        creator_id: str,
        group_id: str,
        title: str,
        description: str = None,
        assignment_type: str = AssignmentType.PRACTICE_SESSION.value,
        story_id: str = None,
        due_date: datetime = None,
        skill_areas: List[str] = None,
        difficulty_level: str = None,
        min_score_required: float = None,
        max_attempts: int = None,
        **kwargs
    ) -> Tuple[Assignment, str]:
        """Create a new assignment for a group"""
        try:
            # Verify creator has permission
            membership = await self.membership_repo.get_membership(group_id, creator_id)
            if not membership or not membership.has_permission("manage_sessions"):
                return None, "Insufficient permissions to create assignments"
            
            # Create assignment
            assignment = await self.assignment_repo.create_assignment(
                creator_id=creator_id,
                group_id=group_id,
                title=title,
                description=description,
                assignment_type=assignment_type,
                story_id=story_id,
                due_date=due_date,
                skill_areas=skill_areas,
                difficulty_level=difficulty_level,
                min_score_required=min_score_required,
                max_attempts=max_attempts,
                **kwargs
            )
            
            await self.session.commit()
            return assignment, None
            
        except Exception as e:
            await self.session.rollback()
            return None, f"Failed to create assignment: {str(e)}"
    
    async def publish_assignment(
        self,
        assignment_id: str,
        publisher_id: str,
        notify_students: bool = True
    ) -> Tuple[Assignment, str]:
        """Publish an assignment and notify students"""
        try:
            assignment = await self.assignment_repo.get_by_id(assignment_id)
            if not assignment:
                return None, "Assignment not found"
            
            # Verify publisher has permission
            membership = await self.membership_repo.get_membership(assignment.group_id, publisher_id)
            if not membership or not membership.has_permission("manage_sessions"):
                return None, "Insufficient permissions to publish assignments"
            
            # Publish assignment
            assignment = await self.assignment_repo.publish_assignment(assignment_id)
            
            # Create submissions for all group members
            await self._create_submissions_for_group_members(assignment)
            
            # Send notifications if requested
            if notify_students:
                await self._notify_assignment_created(assignment)
            
            await self.session.commit()
            return assignment, None
            
        except Exception as e:
            await self.session.rollback()
            return None, f"Failed to publish assignment: {str(e)}"
    
    async def _create_submissions_for_group_members(self, assignment: Assignment) -> None:
        """Create submission records for all group members"""
        members = await self.membership_repo.get_active_members(assignment.group_id)
        
        for member in members:
            # Skip the creator
            if member.user_id == assignment.creator_id:
                continue
            
            # Create submission record
            await self.submission_repo.create_submission(
                assignment_id=assignment.id,
                student_id=member.user_id,
                status=SubmissionStatus.NOT_STARTED.value
            )
    
    async def _notify_assignment_created(self, assignment: Assignment) -> None:
        """Send notifications about new assignment"""
        # Get group members (excluding creator)
        members = await self.membership_repo.get_active_members(assignment.group_id)
        student_ids = [m.user_id for m in members if m.user_id != assignment.creator_id]
        
        # Create notifications
        title = f"New Assignment: {assignment.title}"
        message = f"A new assignment has been posted in your group."
        if assignment.due_date:
            message += f" Due: {assignment.due_date.strftime('%Y-%m-%d %H:%M')}"
        
        await self.notification_repo.create_bulk_notifications(
            user_ids=student_ids,
            title=title,
            message=message,
            notification_type=NotificationType.ASSIGNMENT_CREATED.value,
            priority=NotificationPriority.NORMAL.value,
            sender_id=assignment.creator_id,
            group_id=assignment.group_id,
            assignment_id=assignment.id,
            action_url=f"/assignments/{assignment.id}",
            action_text="View Assignment"
        )
    
    async def get_group_assignments(
        self,
        group_id: str,
        requesting_user_id: str,
        status_filter: str = None,
        include_drafts: bool = False
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Get assignments for a group with user-specific data"""
        try:
            # Verify user is a member
            membership = await self.membership_repo.get_membership(group_id, requesting_user_id)
            if not membership or not membership.is_active:
                return [], "Not a member of this group"
            
            # Get assignments
            assignments = await self.assignment_repo.get_group_assignments(
                group_id, status_filter, include_drafts
            )
            
            # Add user-specific data for each assignment
            assignment_data = []
            for assignment in assignments:
                assignment_dict = assignment.get_assignment_summary()
                
                # Get user's submission if they're a student
                if membership.role not in [GroupRole.OWNER.value, GroupRole.EDUCATOR.value]:
                    submission = await self.submission_repo.get_student_submission(
                        assignment.id, requesting_user_id
                    )
                    if submission:
                        assignment_dict["user_submission"] = submission.get_submission_summary()
                
                assignment_data.append(assignment_dict)
            
            return assignment_data, None
            
        except Exception as e:
            return [], f"Failed to get assignments: {str(e)}"
    
    async def start_assignment(
        self,
        assignment_id: str,
        student_id: str
    ) -> Tuple[AssignmentSubmission, str]:
        """Start working on an assignment"""
        try:
            assignment = await self.assignment_repo.get_by_id(assignment_id)
            if not assignment:
                return None, "Assignment not found"
            
            # Check if assignment is available
            if not assignment.is_available():
                return None, "Assignment is not currently available"
            
            # Verify student is a group member
            membership = await self.membership_repo.get_membership(assignment.group_id, student_id)
            if not membership or not membership.is_active:
                return None, "Not a member of this group"
            
            # Start or resume submission
            submission = await self.submission_repo.start_submission(assignment_id, student_id)
            
            await self.session.commit()
            return submission, None
            
        except Exception as e:
            await self.session.rollback()
            return None, f"Failed to start assignment: {str(e)}"
    
    async def submit_assignment(
        self,
        assignment_id: str,
        student_id: str,
        practice_session_id: str = None,
        collaborative_session_id: str = None,
        performance_metrics: Dict[str, Any] = None
    ) -> Tuple[AssignmentSubmission, str]:
        """Submit an assignment for grading"""
        try:
            # Get current submission
            submission = await self.submission_repo.get_student_submission(assignment_id, student_id)
            if not submission:
                return None, "No active submission found"
            
            # Submit assignment
            submission = await self.submission_repo.submit_assignment(
                submission.id,
                practice_session_id,
                collaborative_session_id,
                performance_metrics
            )
            
            # Auto-grade if enabled
            if submission.assignment.auto_grade and performance_metrics:
                await self._auto_grade_submission(submission, performance_metrics)
            
            # Update assignment statistics
            await self.assignment_repo.update_assignment_stats(assignment_id)
            
            # Notify educator
            await self._notify_assignment_submitted(submission)
            
            await self.session.commit()
            return submission, None
            
        except Exception as e:
            await self.session.rollback()
            return None, f"Failed to submit assignment: {str(e)}"
    
    async def _auto_grade_submission(
        self,
        submission: AssignmentSubmission,
        performance_metrics: Dict[str, Any]
    ) -> None:
        """Automatically grade a submission based on performance"""
        # Calculate auto score based on performance metrics
        overall_score = performance_metrics.get("overall_score", 0.0)
        completion_rate = performance_metrics.get("completion_percentage", 0.0) / 100.0
        
        # Weighted score: 70% performance, 30% completion
        auto_score = (overall_score * 0.7) + (completion_rate * 0.3)
        
        # Generate AI feedback
        ai_feedback = self._generate_ai_feedback(performance_metrics)
        
        # Apply auto grade
        await self.submission_repo.auto_grade_submission(
            submission.id, auto_score, ai_feedback
        )
    
    def _generate_ai_feedback(self, performance_metrics: Dict[str, Any]) -> str:
        """Generate AI feedback based on performance metrics"""
        feedback_parts = []
        
        overall_score = performance_metrics.get("overall_score", 0.0)
        if overall_score >= 0.8:
            feedback_parts.append("Excellent work! Your signing accuracy is very good.")
        elif overall_score >= 0.6:
            feedback_parts.append("Good effort! Keep practicing to improve your accuracy.")
        else:
            feedback_parts.append("Keep practicing! Focus on clear hand shapes and movements.")
        
        completion_rate = performance_metrics.get("completion_percentage", 0.0)
        if completion_rate < 100:
            feedback_parts.append(f"Try to complete all sentences in the assignment ({completion_rate:.0f}% completed).")
        
        return " ".join(feedback_parts)
    
    async def _notify_assignment_submitted(self, submission: AssignmentSubmission) -> None:
        """Notify educator about assignment submission"""
        # Get group educators
        educators = await self.membership_repo.get_members_by_role(
            submission.assignment.group_id, [GroupRole.OWNER.value, GroupRole.EDUCATOR.value]
        )
        
        educator_ids = [e.user_id for e in educators]
        
        title = f"Assignment Submitted: {submission.assignment.title}"
        message = f"A student has submitted their assignment."
        
        await self.notification_repo.create_bulk_notifications(
            user_ids=educator_ids,
            title=title,
            message=message,
            notification_type=NotificationType.ASSIGNMENT_CREATED.value,
            priority=NotificationPriority.NORMAL.value,
            sender_id=submission.student_id,
            group_id=submission.assignment.group_id,
            assignment_id=submission.assignment.id,
            action_url=f"/assignments/{submission.assignment.id}/submissions",
            action_text="Review Submissions"
        )
    
    async def grade_submission(
        self,
        submission_id: str,
        reviewer_id: str,
        score: float = None,
        feedback: str = None,
        meets_requirements: bool = None
    ) -> Tuple[AssignmentSubmission, str]:
        """Grade a student submission"""
        try:
            submission = await self.submission_repo.get_by_id(submission_id)
            if not submission:
                return None, "Submission not found"
            
            # Verify reviewer has permission
            membership = await self.membership_repo.get_membership(
                submission.assignment.group_id, reviewer_id
            )
            if not membership or not membership.has_permission("manage_sessions"):
                return None, "Insufficient permissions to grade submissions"
            
            # Grade submission
            submission = await self.submission_repo.grade_submission(
                submission_id, reviewer_id, score, feedback, meets_requirements
            )
            
            # Update assignment statistics
            await self.assignment_repo.update_assignment_stats(submission.assignment_id)
            
            # Notify student
            await self._notify_assignment_graded(submission)
            
            await self.session.commit()
            return submission, None
            
        except Exception as e:
            await self.session.rollback()
            return None, f"Failed to grade submission: {str(e)}"
    
    async def _notify_assignment_graded(self, submission: AssignmentSubmission) -> None:
        """Notify student about graded assignment"""
        title = f"Assignment Graded: {submission.assignment.title}"
        message = f"Your assignment has been graded."
        if submission.score:
            message += f" Score: {submission.score:.1%}"
        
        await self.notification_repo.create_notification(
            user_id=submission.student_id,
            title=title,
            message=message,
            notification_type=NotificationType.ASSIGNMENT_GRADED.value,
            priority=NotificationPriority.NORMAL.value,
            sender_id=submission.reviewed_by,
            group_id=submission.assignment.group_id,
            assignment_id=submission.assignment.id,
            action_url=f"/assignments/{submission.assignment.id}",
            action_text="View Results"
        )
    
    # Group Analytics and Reporting
    
    async def get_group_progress_report(
        self,
        group_id: str,
        requesting_user_id: str,
        period_days: int = 30
    ) -> Tuple[Dict[str, Any], str]:
        """Get comprehensive group progress report"""
        try:
            # Verify user has permission to view analytics
            membership = await self.membership_repo.get_membership(group_id, requesting_user_id)
            if not membership or membership.role not in [
                GroupRole.OWNER.value, GroupRole.EDUCATOR.value, GroupRole.MODERATOR.value
            ]:
                return {}, "Insufficient permissions to view group analytics"
            
            # Get date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Get group members
            members = await self.membership_repo.get_active_members(group_id)
            member_ids = [m.user_id for m in members]
            
            # Get assignment statistics
            assignments = await self.assignment_repo.get_group_assignments(group_id)
            assignment_stats = await self._calculate_assignment_statistics(assignments)
            
            # Get member progress
            member_progress = await self._get_member_progress_summary(member_ids, start_date, end_date)
            
            # Get engagement metrics
            engagement_metrics = await self._calculate_engagement_metrics(group_id, start_date, end_date)
            
            report = {
                "group_id": group_id,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "member_count": len(members),
                "assignment_statistics": assignment_stats,
                "member_progress": member_progress,
                "engagement_metrics": engagement_metrics,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return report, None
            
        except Exception as e:
            return {}, f"Failed to generate progress report: {str(e)}"
    
    async def _calculate_assignment_statistics(self, assignments: List[Assignment]) -> Dict[str, Any]:
        """Calculate statistics for group assignments"""
        total_assignments = len(assignments)
        published_assignments = len([a for a in assignments if a.status == AssignmentStatus.PUBLISHED.value])
        
        total_submissions = sum(a.total_submissions for a in assignments)
        completed_submissions = sum(a.completed_submissions for a in assignments)
        
        avg_completion_rate = 0.0
        if total_submissions > 0:
            avg_completion_rate = (completed_submissions / total_submissions) * 100
        
        avg_score = 0.0
        scored_assignments = [a for a in assignments if a.average_score is not None]
        if scored_assignments:
            avg_score = sum(a.average_score for a in scored_assignments) / len(scored_assignments)
        
        return {
            "total_assignments": total_assignments,
            "published_assignments": published_assignments,
            "total_submissions": total_submissions,
            "completed_submissions": completed_submissions,
            "completion_rate": avg_completion_rate,
            "average_score": avg_score
        }
    
    async def _get_member_progress_summary(
        self,
        member_ids: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get progress summary for group members"""
        member_progress = []
        
        for member_id in member_ids:
            # Get user progress data
            progress_data = await self.progress_repo.get_user_progress_summary(member_id)
            
            # Get recent activity
            recent_sessions = await self.progress_repo.get_user_sessions_in_period(
                member_id, start_date, end_date
            )
            
            member_summary = {
                "user_id": member_id,
                "total_practice_time": progress_data.get("total_practice_time", 0),
                "recent_sessions": len(recent_sessions),
                "average_score": progress_data.get("average_score"),
                "learning_streak": progress_data.get("learning_streak", 0),
                "skill_progress": progress_data.get("skill_areas", {})
            }
            
            member_progress.append(member_summary)
        
        return member_progress
    
    async def _calculate_engagement_metrics(
        self,
        group_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Calculate group engagement metrics"""
        # Get message count
        messages = await self.message_repo.get_group_messages(group_id, limit=1000)
        recent_messages = [
            m for m in messages 
            if start_date <= m.created_at.replace(tzinfo=None) <= end_date
        ]
        
        # Calculate metrics
        return {
            "total_messages": len(recent_messages),
            "active_participants": len(set(m.sender_id for m in recent_messages)),
            "announcements": len([m for m in recent_messages if m.is_announcement]),
            "average_messages_per_day": len(recent_messages) / max(1, (end_date - start_date).days)
        }
    
    # Communication and Notifications
    
    async def send_group_announcement(
        self,
        group_id: str,
        sender_id: str,
        subject: str,
        content: str,
        notify_members: bool = True
    ) -> Tuple[Any, str]:
        """Send an announcement to the group"""
        try:
            # Verify sender has permission
            membership = await self.membership_repo.get_membership(group_id, sender_id)
            if not membership or not membership.has_permission("moderate_content"):
                return None, "Insufficient permissions to send announcements"
            
            # Create message
            message = await self.message_repo.create_message(
                group_id=group_id,
                sender_id=sender_id,
                content=content,
                subject=subject,
                is_announcement=True,
                message_type="announcement"
            )
            
            # Send notifications if requested
            if notify_members:
                await self._notify_group_announcement(group_id, sender_id, subject, content)
            
            await self.session.commit()
            return message, None
            
        except Exception as e:
            await self.session.rollback()
            return None, f"Failed to send announcement: {str(e)}"
    
    async def _notify_group_announcement(
        self,
        group_id: str,
        sender_id: str,
        subject: str,
        content: str
    ) -> None:
        """Send notifications about group announcement"""
        # Get group members (excluding sender)
        members = await self.membership_repo.get_active_members(group_id)
        member_ids = [m.user_id for m in members if m.user_id != sender_id]
        
        title = f"Group Announcement: {subject}"
        message = content[:200] + "..." if len(content) > 200 else content
        
        await self.notification_repo.create_bulk_notifications(
            user_ids=member_ids,
            title=title,
            message=message,
            notification_type=NotificationType.GROUP_UPDATE.value,
            priority=NotificationPriority.NORMAL.value,
            sender_id=sender_id,
            group_id=group_id,
            action_url=f"/groups/{group_id}/messages",
            action_text="View Announcement"
        )
    
    async def check_and_send_due_date_reminders(self) -> int:
        """Check for assignments due soon and send reminders"""
        try:
            # Get assignments due in the next 24 hours
            tomorrow = datetime.utcnow() + timedelta(days=1)
            
            assignments = await self.assignment_repo.get_assignments_due_soon(tomorrow)
            
            reminder_count = 0
            for assignment in assignments:
                # Get incomplete submissions
                incomplete_submissions = await self.submission_repo.get_assignment_submissions(
                    assignment.id,
                    status_filter=SubmissionStatus.NOT_STARTED.value
                )
                
                student_ids = [s.student_id for s in incomplete_submissions]
                
                if student_ids:
                    title = f"Assignment Due Soon: {assignment.title}"
                    message = f"Your assignment is due on {assignment.due_date.strftime('%Y-%m-%d %H:%M')}."
                    
                    await self.notification_repo.create_bulk_notifications(
                        user_ids=student_ids,
                        title=title,
                        message=message,
                        notification_type=NotificationType.ASSIGNMENT_DUE.value,
                        priority=NotificationPriority.HIGH.value,
                        group_id=assignment.group_id,
                        assignment_id=assignment.id,
                        action_url=f"/assignments/{assignment.id}",
                        action_text="Complete Assignment"
                    )
                    
                    reminder_count += len(student_ids)
            
            await self.session.commit()
            return reminder_count
            
        except Exception as e:
            await self.session.rollback()
            return 0