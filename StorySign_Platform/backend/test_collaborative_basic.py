"""
Basic tests for collaborative learning features - testing business logic only
"""

import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


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


def test_business_logic():
    """Test business logic methods"""
    from models.collaborative import LearningGroup, GroupMembership, CollaborativeSession, GroupAnalytics
    from models.collaborative import GroupRole, GroupPrivacy, SessionStatus, DataSharingLevel
    
    # Test join code generation
    group = LearningGroup.__new__(LearningGroup)
    join_code = group.generate_join_code()
    assert join_code is not None
    assert len(join_code) == 8
    assert join_code.isalnum()
    print("✓ Join code generation test passed")
    
    # Test membership permissions
    membership = GroupMembership.__new__(GroupMembership)
    
    # Mock the role attribute
    membership.role = GroupRole.OWNER.value
    assert membership.has_permission("manage_group") is True
    assert membership.has_permission("delete_group") is True
    
    membership.role = GroupRole.MEMBER.value
    assert membership.has_permission("participate_sessions") is True
    assert membership.has_permission("manage_group") is False
    
    print("✓ Membership permissions test passed")
    
    # Test data sharing fields
    membership.data_sharing_level = DataSharingLevel.BASIC.value
    membership.share_progress = True
    membership.share_performance = False
    membership.share_practice_sessions = False
    
    fields = membership.get_shared_data_fields()
    assert "current_level" in fields
    assert "learning_streak" in fields
    assert "total_sessions" in fields
    
    membership.data_sharing_level = DataSharingLevel.NONE.value
    fields = membership.get_shared_data_fields()
    assert len(fields) == 0
    
    print("✓ Data sharing fields test passed")
    
    # Test session participant management
    session = CollaborativeSession.__new__(CollaborativeSession)
    session.max_participants = 3
    session.participant_ids = []
    session.status = SessionStatus.SCHEDULED.value
    
    # Test adding participants
    assert session.add_participant("user_1") is True
    assert session.add_participant("user_2") is True
    assert session.add_participant("user_3") is True
    assert session.get_participant_count() == 3
    
    # Test max participants limit
    assert session.add_participant("user_4") is False
    assert session.get_participant_count() == 3
    
    # Test removing participants
    assert session.remove_participant("user_2") is True
    assert session.get_participant_count() == 2
    
    # Test can accept participants
    assert session.can_accept_participants() is True
    
    print("✓ Session participant management test passed")
    
    # Test session duration calculation
    now = datetime.utcnow()
    session.actual_start = now
    session.actual_end = now + timedelta(minutes=45)
    duration = session.calculate_duration()
    assert duration == 45
    
    print("✓ Session duration calculation test passed")
    
    # Test analytics engagement calculation
    analytics = GroupAnalytics.__new__(GroupAnalytics)
    analytics.total_members = 10
    analytics.active_members = 7
    
    engagement_rate = analytics.calculate_engagement_rate()
    assert engagement_rate == 70.0
    
    # Test zero members case
    analytics.total_members = 0
    analytics.active_members = 0
    assert analytics.calculate_engagement_rate() == 0.0
    
    print("✓ Analytics engagement calculation test passed")


def test_validation_logic():
    """Test validation methods"""
    from models.collaborative import LearningGroup, GroupMembership, CollaborativeSession
    from models.collaborative import GroupRole, GroupPrivacy, SessionStatus
    
    # Test group member count and capacity
    group = LearningGroup.__new__(LearningGroup)
    group.max_members = 5
    group.is_active = True
    
    # Mock memberships list
    class MockMembership:
        def __init__(self, is_active):
            self.is_active = is_active
    
    group.memberships = [
        MockMembership(True),
        MockMembership(True),
        MockMembership(False),  # Inactive member
        MockMembership(True),
    ]
    
    assert group.get_member_count() == 3  # Only active members
    assert group.can_accept_new_members() is True
    
    # Test when group is full
    group.memberships = [MockMembership(True) for _ in range(5)]
    assert group.get_member_count() == 5
    assert group.can_accept_new_members() is False
    
    print("✓ Group capacity validation test passed")
    
    # Test session capacity
    session = CollaborativeSession.__new__(CollaborativeSession)
    session.max_participants = 2
    session.participant_ids = ["user_1", "user_2"]
    session.status = SessionStatus.SCHEDULED.value
    
    assert session.can_accept_participants() is False
    
    # Test with available capacity
    session.participant_ids = ["user_1"]
    assert session.can_accept_participants() is True
    
    # Test with inactive status
    session.status = SessionStatus.COMPLETED.value
    assert session.can_accept_participants() is False
    
    print("✓ Session capacity validation test passed")


def test_summary_methods():
    """Test summary generation methods"""
    from models.collaborative import LearningGroup, GroupMembership, CollaborativeSession, GroupAnalytics
    from models.collaborative import GroupRole, GroupPrivacy, SessionStatus, DataSharingLevel
    
    # Test group summary
    group = LearningGroup.__new__(LearningGroup)
    
    # Set required attributes for summary
    group.id = "group_123"
    group.name = "Test Group"
    group.description = "Test Description"
    group.creator_id = "user_123"
    group.privacy_level = GroupPrivacy.PRIVATE.value
    group.is_public = False
    group.join_code = "ABC12345"
    group.max_members = 10
    group.skill_focus = ["vocabulary"]
    group.difficulty_level = "beginner"
    group.learning_goals = ["Learn ASL"]
    group.tags = ["beginner"]
    group.language = "en"
    group.timezone = "UTC"
    group.total_sessions = 5
    group.last_activity_at = datetime.utcnow()
    group.is_active = True
    group.created_at = datetime.utcnow()
    group.memberships = []  # Empty for count
    
    summary = group.get_group_summary()
    assert summary["id"] == "group_123"
    assert summary["name"] == "Test Group"
    assert summary["privacy_level"] == GroupPrivacy.PRIVATE.value
    assert summary["member_count"] == 0
    
    print("✓ Group summary test passed")
    
    # Test membership summary
    membership = GroupMembership.__new__(GroupMembership)
    membership.id = "membership_123"
    membership.group_id = "group_123"
    membership.user_id = "user_456"
    membership.role = GroupRole.MEMBER.value
    membership.custom_role_name = None
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
    
    summary = membership.get_membership_summary()
    assert summary["group_id"] == "group_123"
    assert summary["user_id"] == "user_456"
    assert summary["role"] == GroupRole.MEMBER.value
    assert summary["data_sharing_level"] == DataSharingLevel.BASIC.value
    
    print("✓ Membership summary test passed")
    
    # Test session summary
    session = CollaborativeSession.__new__(CollaborativeSession)
    session.id = "session_123"
    session.session_name = "Test Session"
    session.description = "Test Description"
    session.host_id = "user_123"
    session.group_id = "group_456"
    session.story_id = None
    session.status = SessionStatus.SCHEDULED.value
    session.participant_ids = ["user_1", "user_2"]
    session.max_participants = 5
    session.scheduled_start = datetime.utcnow()
    session.scheduled_end = None
    session.actual_start = None
    session.actual_end = None
    session.difficulty_level = "beginner"
    session.skill_focus = ["vocabulary"]
    session.allow_peer_feedback = True
    session.enable_voice_chat = False
    session.enable_text_chat = True
    session.record_session = False
    session.is_public = False
    session.requires_approval = False
    session.tags = []
    session.created_at = datetime.utcnow()
    
    summary = session.get_session_summary()
    assert summary["session_id"] == "session_123"
    assert summary["session_name"] == "Test Session"
    assert summary["status"] == SessionStatus.SCHEDULED.value
    assert summary["participant_count"] == 2
    
    print("✓ Session summary test passed")
    
    # Test analytics summary
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
    
    summary = analytics.get_analytics_summary()
    assert summary["group_id"] == "group_123"
    assert summary["period"]["type"] == "weekly"
    assert summary["membership"]["total_members"] == 10
    assert summary["membership"]["engagement_rate"] == 70.0
    
    print("✓ Analytics summary test passed")


if __name__ == "__main__":
    test_enums()
    test_business_logic()
    test_validation_logic()
    test_summary_methods()
    print("\n🎉 All collaborative feature tests passed!")
    print("\nImplemented features:")
    print("- Learning Groups with privacy controls")
    print("- Group Memberships with role-based permissions")
    print("- Collaborative Sessions with participant management")
    print("- Group Analytics with engagement tracking")
    print("- Privacy controls for data sharing")
    print("- Comprehensive validation and business logic")