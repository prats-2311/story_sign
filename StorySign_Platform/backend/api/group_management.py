"""
API endpoints for group management features
Handles assignments, notifications, and educator tools
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db_session
from services.group_management_service import GroupManagementService
from models.assignments import AssignmentType, AssignmentStatus, SubmissionStatus


router = APIRouter()


# Pydantic models for request/response

class CreateAssignmentRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    assignment_type: str = Field(default=AssignmentType.PRACTICE_SESSION.value)
    story_id: Optional[str] = None
    due_date: Optional[datetime] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    skill_areas: Optional[List[str]] = Field(default_factory=list)
    difficulty_level: Optional[str] = None
    min_score_required: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_attempts: Optional[int] = Field(None, gt=0)
    estimated_duration: Optional[int] = Field(None, gt=0)
    is_required: bool = Field(default=True)
    allow_late_submission: bool = Field(default=False)
    auto_grade: bool = Field(default=True)
    instructions: Optional[str] = None


class SubmitAssignmentRequest(BaseModel):
    practice_session_id: Optional[str] = None
    collaborative_session_id: Optional[str] = None
    performance_metrics: Optional[Dict[str, Any]] = None


class GradeSubmissionRequest(BaseModel):
    score: Optional[float] = Field(None, ge=0.0, le=1.0)
    feedback: Optional[str] = None
    meets_requirements: Optional[bool] = None


class SendAnnouncementRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=5000)
    notify_members: bool = Field(default=True)


class AssignmentResponse(BaseModel):
    assignment_id: str
    title: str
    description: Optional[str]
    creator_id: str
    group_id: str
    assignment_type: str
    story_id: Optional[str]
    skill_areas: List[str]
    difficulty_level: Optional[str]
    status: str
    is_required: bool
    is_available: bool
    is_overdue: bool
    published_at: Optional[str]
    due_date: Optional[str]
    available_from: Optional[str]
    available_until: Optional[str]
    min_score_required: Optional[float]
    max_attempts: Optional[int]
    estimated_duration: Optional[int]
    allow_late_submission: bool
    auto_grade: bool
    total_submissions: int
    completed_submissions: int
    completion_rate: float
    average_score: Optional[float]
    created_at: str
    user_submission: Optional[Dict[str, Any]] = None


class SubmissionResponse(BaseModel):
    submission_id: str
    assignment_id: str
    student_id: str
    status: str
    attempt_number: int
    practice_session_id: Optional[str]
    collaborative_session_id: Optional[str]
    score: Optional[float]
    auto_grade_score: Optional[float]
    manual_grade_score: Optional[float]
    final_score: Optional[float]
    started_at: Optional[str]
    submitted_at: Optional[str]
    reviewed_at: Optional[str]
    time_spent: Optional[int]
    reviewed_by: Optional[str]
    has_feedback: bool
    has_ai_feedback: bool
    meets_requirements: Optional[bool]
    is_late: bool
    is_completed: bool
    created_at: str


class ProgressReportResponse(BaseModel):
    group_id: str
    period_start: str
    period_end: str
    member_count: int
    assignment_statistics: Dict[str, Any]
    member_progress: List[Dict[str, Any]]
    engagement_metrics: Dict[str, Any]
    generated_at: str


# Dependency to get current user ID (placeholder - would integrate with auth)
async def get_current_user_id() -> str:
    # This would be replaced with actual authentication
    return "user_123"


# Assignment Management Endpoints

@router.post("/groups/{group_id}/assignments", response_model=AssignmentResponse)
async def create_assignment(
    group_id: str,
    request: CreateAssignmentRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new assignment for a group"""
    service = GroupManagementService(db)
    
    assignment, error = await service.create_assignment(
        creator_id=current_user_id,
        group_id=group_id,
        title=request.title,
        description=request.description,
        assignment_type=request.assignment_type,
        story_id=request.story_id,
        due_date=request.due_date,
        available_from=request.available_from,
        available_until=request.available_until,
        skill_areas=request.skill_areas,
        difficulty_level=request.difficulty_level,
        min_score_required=request.min_score_required,
        max_attempts=request.max_attempts,
        estimated_duration=request.estimated_duration,
        is_required=request.is_required,
        allow_late_submission=request.allow_late_submission,
        auto_grade=request.auto_grade,
        instructions=request.instructions
    )
    
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return assignment.get_assignment_summary()


@router.post("/assignments/{assignment_id}/publish")
async def publish_assignment(
    assignment_id: str,
    notify_students: bool = Query(True, description="Send notifications to students"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Publish an assignment and notify students"""
    service = GroupManagementService(db)
    
    assignment, error = await service.publish_assignment(
        assignment_id, current_user_id, notify_students
    )
    
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return {
        "message": "Assignment published successfully",
        "assignment": assignment.get_assignment_summary()
    }


@router.get("/groups/{group_id}/assignments", response_model=List[AssignmentResponse])
async def get_group_assignments(
    group_id: str,
    status_filter: Optional[str] = Query(None, description="Filter by assignment status"),
    include_drafts: bool = Query(False, description="Include draft assignments"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Get assignments for a group"""
    service = GroupManagementService(db)
    
    assignments, error = await service.get_group_assignments(
        group_id, current_user_id, status_filter, include_drafts
    )
    
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return assignments


@router.post("/assignments/{assignment_id}/start")
async def start_assignment(
    assignment_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Start working on an assignment"""
    service = GroupManagementService(db)
    
    submission, error = await service.start_assignment(assignment_id, current_user_id)
    
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return {
        "message": "Assignment started successfully",
        "submission": submission.get_submission_summary()
    }


@router.post("/assignments/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: str,
    request: SubmitAssignmentRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Submit an assignment for grading"""
    service = GroupManagementService(db)
    
    submission, error = await service.submit_assignment(
        assignment_id=assignment_id,
        student_id=current_user_id,
        practice_session_id=request.practice_session_id,
        collaborative_session_id=request.collaborative_session_id,
        performance_metrics=request.performance_metrics
    )
    
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return {
        "message": "Assignment submitted successfully",
        "submission": submission.get_submission_summary()
    }


@router.get("/assignments/{assignment_id}/submissions", response_model=List[SubmissionResponse])
async def get_assignment_submissions(
    assignment_id: str,
    status_filter: Optional[str] = Query(None, description="Filter by submission status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Get submissions for an assignment (educators only)"""
    service = GroupManagementService(db)
    
    # This would include permission checking in the service
    submissions = await service.submission_repo.get_assignment_submissions(
        assignment_id, status_filter, limit, offset
    )
    
    return [s.get_submission_summary() for s in submissions]


@router.post("/submissions/{submission_id}/grade")
async def grade_submission(
    submission_id: str,
    request: GradeSubmissionRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Grade a student submission"""
    service = GroupManagementService(db)
    
    submission, error = await service.grade_submission(
        submission_id=submission_id,
        reviewer_id=current_user_id,
        score=request.score,
        feedback=request.feedback,
        meets_requirements=request.meets_requirements
    )
    
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return {
        "message": "Submission graded successfully",
        "submission": submission.get_submission_summary()
    }


# Analytics and Reporting Endpoints

@router.get("/groups/{group_id}/progress-report", response_model=ProgressReportResponse)
async def get_group_progress_report(
    group_id: str,
    period_days: int = Query(30, ge=1, le=365, description="Number of days to include in report"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Get comprehensive group progress report"""
    service = GroupManagementService(db)
    
    report, error = await service.get_group_progress_report(
        group_id, current_user_id, period_days
    )
    
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return report


@router.get("/groups/{group_id}/assignment-statistics")
async def get_assignment_statistics(
    group_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Get assignment statistics for a group"""
    service = GroupManagementService(db)
    
    # Get assignments and calculate statistics
    assignments, error = await service.get_group_assignments(group_id, current_user_id)
    
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    # Calculate summary statistics
    total_assignments = len(assignments)
    published_assignments = len([a for a in assignments if a["status"] == AssignmentStatus.PUBLISHED.value])
    
    total_submissions = sum(a["total_submissions"] for a in assignments)
    completed_submissions = sum(a["completed_submissions"] for a in assignments)
    
    avg_completion_rate = 0.0
    if total_submissions > 0:
        avg_completion_rate = (completed_submissions / total_submissions) * 100
    
    return {
        "group_id": group_id,
        "total_assignments": total_assignments,
        "published_assignments": published_assignments,
        "total_submissions": total_submissions,
        "completed_submissions": completed_submissions,
        "completion_rate": avg_completion_rate,
        "assignments": assignments
    }


# Communication Endpoints

@router.post("/groups/{group_id}/announcements")
async def send_group_announcement(
    group_id: str,
    request: SendAnnouncementRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Send an announcement to the group"""
    service = GroupManagementService(db)
    
    message, error = await service.send_group_announcement(
        group_id=group_id,
        sender_id=current_user_id,
        subject=request.subject,
        content=request.content,
        notify_members=request.notify_members
    )
    
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)
    
    return {
        "message": "Announcement sent successfully",
        "announcement": message.get_message_summary()
    }


@router.get("/groups/{group_id}/messages")
async def get_group_messages(
    group_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    announcements_only: bool = Query(False, description="Get only announcements"),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Get messages for a group"""
    service = GroupManagementService(db)
    
    if announcements_only:
        messages = await service.message_repo.get_announcements(group_id, limit, offset)
    else:
        messages = await service.message_repo.get_group_messages(group_id, False, limit, offset)
    
    return {
        "group_id": group_id,
        "messages": [m.get_message_summary() for m in messages]
    }


# Background Tasks and Utilities

@router.post("/admin/send-due-date-reminders")
async def send_due_date_reminders(
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Send due date reminders for assignments (admin only)"""
    # This would include admin permission checking
    
    async def send_reminders():
        service = GroupManagementService(db)
        reminder_count = await service.check_and_send_due_date_reminders()
        return reminder_count
    
    background_tasks.add_task(send_reminders)
    
    return {"message": "Due date reminder task scheduled"}


@router.get("/my/assignments")
async def get_my_assignments(
    status_filter: Optional[str] = Query(None, description="Filter by submission status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Get assignments for the current user"""
    service = GroupManagementService(db)
    
    # Get user's group memberships first
    memberships = await service.membership_repo.get_user_memberships(current_user_id)
    group_ids = [m.group_id for m in memberships if m.is_active]
    
    # Get submissions
    submissions = await service.submission_repo.get_student_submissions(
        current_user_id, group_ids, status_filter, limit, offset
    )
    
    return {
        "user_id": current_user_id,
        "submissions": [s.get_submission_summary() for s in submissions]
    }


@router.get("/my/notifications")
async def get_my_notifications(
    unread_only: bool = Query(False, description="Get only unread notifications"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Get notifications for the current user"""
    service = GroupManagementService(db)
    
    notifications = await service.notification_repo.get_user_notifications(
        current_user_id, unread_only, limit, offset
    )
    
    unread_count = await service.notification_repo.get_unread_count(current_user_id)
    
    return {
        "user_id": current_user_id,
        "unread_count": unread_count,
        "notifications": [n.get_notification_summary() for n in notifications]
    }


@router.post("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Mark a notification as read"""
    service = GroupManagementService(db)
    
    notification = await service.notification_repo.mark_as_read(notification_id)
    
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    
    return {"message": "Notification marked as read"}


@router.post("/notifications/mark-all-read")
async def mark_all_notifications_as_read(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session)
):
    """Mark all notifications as read for the current user"""
    service = GroupManagementService(db)
    
    count = await service.notification_repo.mark_all_as_read(current_user_id)
    
    return {
        "message": f"Marked {count} notifications as read"
    }