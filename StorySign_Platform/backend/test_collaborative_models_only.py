"""
Simple test for collaborative models without SQLAlchemy relationships
"""

import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test enum values directly
def test_enums():
    """Test enum values"""
    from models.collaborative import GroupRole, GroupPrivacy, SessionStatus, DataSharingLevel
    
    # Test GroupRole enum
    assert GroupRole.OWNER.value == "owner"
    assert GroupRole.EDUCATOR.value == "educator"
    assert GroupRole.MODERATOR.value == "moderator"
    assert GroupRole.MEMBER.value == "member"
    assert GroupRole.OBSERVER.value == "observer"
    
    # Test GroupPrivacy enum
    assert GroupPrivacy.PUBLIC.value == "public"
    assert GroupPrivacy.PRIVATE.value == "private"
    assert GroupPrivacy.INVITE_ONLY.value == "invite_only"
    
    # Test SessionStatus enum
    assert SessionStatus.SCHEDULED.value == "scheduled"
    assert SessionStatus.ACTIVE.value == "active"
    assert SessionStatus.PAUSED.value == "paused"
    assert SessionStatus.COMPLETED.value == "completed"
    assert SessionStatus.CANCELLED.value == "cancelled"
    
    # Test DataSharingLevel enum
    assert DataSharingLevel.NONE.value == "none"
    assert DataSharingLevel.BASIC.value == "basic"
    assert DataSharingLevel.DETAILED.value == "detailed"
    assert DataSharingLevel.FULL.value == "full"
    
    print("✓ All enum tests passed")


def test_model_methods():
    """Test model methods without SQLAlchemy initialization"""
    from models.collaborative import LearningGroup, GroupMembership, CollaborativeSession, GroupAnalytics
    from models.collaborative import GroupRole, GroupPrivacy, SessionStatus, DataSharingLevel
    
    # Test LearningGroup methods
    group = LearningGroup.__new__(LearningGroup)
    group.id = "group_123"
    group.name = "Test Group"
    group.creator_id = "user_123"
    group.privacy_level = GroupPrivacy.PRIVATE.value
    group.is_public = False
    group.max_members = 10
    group.skill_focus = ["vocabulary"]
    group.difficulty_level = "beginner"
    group.learning_goals = ["Learn ASL basics"]
    group.tags = ["beginner", "vocabulary"]
    group.language = "en"
    group.timezone = "UTC"
    group.total_sessions = 5
    group.last_activity_at = datetime.utcnow()
    group.is_active = True
    group.created_at = datetime.utcnow()
    
    # Test join code generation
    join_code = group.generate_join_code()
    assert join_code is not None
    assert len(join_code) == 8
    assert group.join_code == join_code
    
    # Test group summary
    summary = group.get_group_summary()
    assert summary["id"] == "group_123"
    assert summary["name"] == "Test Group"
    assert summary["privacy_level"] == GroupPrivacy.PRIVATE.value
    
    print("✓ LearningGroup methods test passed")
    
    # Test GroupMembership methods
    membership = GroupMembership.__new__(GroupMembership)
    membership.id = "membership_123"
    membership.group_id = "group_123"
    membership.user_id = "user_456"
    membership.role = GroupRole.MEMBER.value
    membership.is_active = True
    membership.joined_at = datetime.utcnow()
    membership.data_sharing_level = DataSharingLevel.BASIC.value
    membership.share_progress = True
    membership.share_performance = False
    membership.share_practice_sessions = False
    membership.allow_peer_feedback = True
    membership.notify_new_sessions = True
    membership.notify_group_updates = True
    membership.notify_peer_achievements = True
    membership.created_at = datetime.utcnow()
    membership.updated_at = datetime.utcnow()
    
    # Test permissions
    assert membership.has_permission("participate_sessions") is True
    assert membership.has_permission("manage_group") is False
    
    # Test data sharing fields
    fields = membership.get_shared_data_fields()
    assert "current_level" in fields
    assert "learning_streak" in fields
    
    # Test membership summary
    summary = membership.get_membership_summary()
    assert summary["group_id"] == "group_123"
    assert summary["user_id"] == "user_456"
    assert summary["role"] == GroupRole.MEMBER.value
    
    print("✓ GroupMembership methods test passed")
    
    # Test CollaborativeSession methods
    session = CollaborativeSession.__new__(CollaborativeSession)
    session.id = "session_123"
    session.session_name = "Test Session"
    session.host_id = "user_123"
    session.group_id = "group_456"
    session.status = SessionStatus.SCHEDULED.value
    session.max_participants = 5
    session.participant_ids = []
    session.difficulty_level = "beginner"
    session.skill_focus = ["fingerspelling"]
    session.allow_peer_feedback = True
    session.enable_voice_chat = False
    session.enable_text_chat = True
    session.record_session = False
    session.is_public = False
    session.requires_approval = False
    session.tags = []
    session.created_at = datetime.utcnow()
    
    # Test participant management
    assert session.add_participant("user_1") is True
    assert session.add_participant("user_2") is True
    assert session.get_participant_count() == 2
    assert session.can_accept_participants() is True
    
    # Fill to capacity
    session.add_participant("user_3")
    session.add_participant("user_4")
    session.add_participant("user_5")
    assert session.get_participant_count() == 5
    assert session.can_accept_participants() is False
    
    # Test remove participant
    assert session.remove_participant("user_2") is True
    assert session.get_participant_count() == 4
    
    # Test duration calculation
    now = datetime.utcnow()
    session.actual_start = now
    session.actual_end = now + timedelta(minutes=45)
    duration = session.calculate_duration()
    assert duration == 45
    
    # Test session summary
    summary = session.get_session_summary()
    assert summary["session_id"] == "session_123"
    assert summary["session_name"] == "Test Session"
    assert summary["status"] == SessionStatus.SCHEDULED.value
    
    print("✓ CollaborativeSession methods test passed")
    
    # Test GroupAnalytics methods
    analytics = GroupAnalytics.__new__(GroupAnalytics)
    analytics.id = "analytics_123"
    analytics.group_id = "group_123"
    analytics.period_start = datetime.utcnow()
    analytics.period_end = datetime.utcnow() + timedelta(days=7)
    analytics.period_type = "weekly"
    analytics.total_members = 10
    analytics.active_members = 7
    analytics.total_sessions = 15
    analytics.collaborative_sessions = 3
    analytics.total_practice_time = 180
    analytics.average_group_score = 0.85
    analytics.average_completion_rate = 0.92
    analytics.peer_feedback_count = 25
    analytics.group_interactions = 50
    analytics.milestones_achieved = []
    analytics.group_achievements = []
    analytics.created_at = datetime.utcnow()
    analytics.updated_at = datetime.utcnow()
    
    # Test engagement calculation
    engagement_rate = analytics.calculate_engagement_rate()
    assert engagement_rate == 70.0
    
    # Test analytics summary
    summary = analytics.get_analytics_summary()
    assert summary["group_id"] == "group_123"
    assert summary["period"]["type"] == "weekly"
    assert summary["membership"]["total_members"] == 10
    assert summary["membership"]["active_members"] == 7
    assert summary["membership"]["engagement_rate"] == 70.0
    
    print("✓ GroupAnalytics methods test passed")


if __name__ == "__main__":
    test_enums()
    test_model_methods()
    print("\n🎉 All collaborative model tests passed!")