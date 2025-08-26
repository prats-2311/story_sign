"""
Simple tests for collaborative learning features
Tests basic model creation and validation
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.collaborative import (
    LearningGroup, GroupMembership, CollaborativeSession, GroupAnalytics,
    GroupRole, GroupPrivacy, SessionStatus, DataSharingLevel
)


class TestCollaborativeModels:
    """Test collaborative learning models"""
    
    def test_learning_group_creation(self):
        """Test learning group model creation and validation"""
        group = LearningGroup(
            name="Test Group",
            description="Test Description",
            creator_id="user_123",
            privacy_level=GroupPrivacy.PUBLIC.value,
            max_members=20,
            skill_focus=["vocabulary", "grammar"],
            difficulty_level="intermediate"
        )
        
        assert group.name == "Test Group"
        assert group.creator_id == "user_123"
        assert group.privacy_level == GroupPrivacy.PUBLIC.value
        assert group.max_members == 20
        assert group.skill_focus == ["vocabulary", "grammar"]
        assert group.difficulty_level == "intermediate"
        assert group.is_active is True
        assert group.total_sessions == 0
    
    def test_group_membership_creation(self):
        """Test group membership model creation"""
        membership = GroupMembership(
            group_id="group_123",
            user_id="user_456",
            role=GroupRole.MEMBER.value,
            data_sharing_level=DataSharingLevel.BASIC.value,
            share_progress=True,
            share_performance=False
        )
        
        assert membership.group_id == "group_123"
        assert membership.user_id == "user_456"
        assert membership.role == GroupRole.MEMBER.value
        assert membership.is_active is True
        assert membership.data_sharing_level == DataSharingLevel.BASIC.value
        assert membership.share_progress is True
        assert membership.share_performance is False
    
    def test_collaborative_session_creation(self):
        """Test collaborative session model creation"""
        session = CollaborativeSession(
            session_name="Test Session",
            description="Test collaborative session",
            host_id="user_123",
            group_id="group_456",
            scheduled_start=datetime.utcnow() + timedelta(hours=1),
            scheduled_end=datetime.utcnow() + timedelta(hours=2),
            max_participants=5,
            difficulty_level="beginner",
            skill_focus=["fingerspelling"]
        )
        
        assert session.session_name == "Test Session"
        assert session.host_id == "user_123"
        assert session.group_id == "group_456"
        assert session.status == SessionStatus.SCHEDULED.value
        assert session.max_participants == 5
        assert session.difficulty_level == "beginner"
    
    def test_group_analytics_creation(self):
        """Test group analytics model creation"""
        now = datetime.utcnow()
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=7)
        
        analytics = GroupAnalytics(
            group_id="group_123",
            period_start=period_start,
            period_end=period_end,
            period_type="weekly",
            total_members=5,
            active_members=3,
            total_sessions=10,
            collaborative_sessions=2,
            total_practice_time=120,
            average_group_score=0.85,
            average_completion_rate=0.92
        )
        
        assert analytics.group_id == "group_123"
        assert analytics.period_type == "weekly"
        assert analytics.total_members == 5
        assert analytics.active_members == 3
        assert analytics.calculate_engagement_rate() == 60.0
    
    def test_group_join_code_generation(self):
        """Test join code generation for groups"""
        group = LearningGroup(
            name="Test Group",
            creator_id="user_123",
            privacy_level=GroupPrivacy.INVITE_ONLY.value
        )
        
        # Generate join code
        join_code = group.generate_join_code()
        
        assert join_code is not None
        assert len(join_code) == 8
        assert join_code.isalnum()
        assert group.join_code == join_code
    
    def test_membership_permissions(self):
        """Test membership permission checking"""
        # Test owner permissions
        owner_membership = GroupMembership(
            group_id="group_123",
            user_id="user_123",
            role=GroupRole.OWNER.value
        )
        
        assert owner_membership.has_permission("manage_group") is True
        assert owner_membership.has_permission("invite_members") is True
        assert owner_membership.has_permission("delete_group") is True
        
        # Test member permissions
        member_membership = GroupMembership(
            group_id="group_123",
            user_id="user_456",
            role=GroupRole.MEMBER.value
        )
        
        assert member_membership.has_permission("participate_sessions") is True
        assert member_membership.has_permission("manage_group") is False
        assert member_membership.has_permission("delete_group") is False
    
    def test_session_participant_management(self):
        """Test collaborative session participant management"""
        session = CollaborativeSession(
            session_name="Test Session",
            host_id="user_123",
            group_id="group_456",
            max_participants=3,
            status=SessionStatus.SCHEDULED.value
        )
        
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
    
    def test_data_sharing_fields(self):
        """Test data sharing field calculation"""
        # Test basic sharing
        basic_membership = GroupMembership(
            group_id="group_123",
            user_id="user_456",
            data_sharing_level=DataSharingLevel.BASIC.value,
            share_progress=True,
            share_performance=False,
            share_practice_sessions=False
        )
        
        fields = basic_membership.get_shared_data_fields()
        assert "current_level" in fields
        assert "learning_streak" in fields
        assert "total_sessions" in fields
        
        # Test detailed sharing
        detailed_membership = GroupMembership(
            group_id="group_123",
            user_id="user_789",
            data_sharing_level=DataSharingLevel.DETAILED.value,
            share_progress=True,
            share_performance=True,
            share_practice_sessions=False
        )
        
        fields = detailed_membership.get_shared_data_fields()
        assert "current_level" in fields
        assert "average_score" in fields
        assert "success_rate" in fields
        assert "recent_sessions" not in fields
        
        # Test full sharing
        full_membership = GroupMembership(
            group_id="group_123",
            user_id="user_101",
            data_sharing_level=DataSharingLevel.FULL.value,
            share_progress=True,
            share_performance=True,
            share_practice_sessions=True
        )
        
        fields = full_membership.get_shared_data_fields()
        assert "current_level" in fields
        assert "average_score" in fields
        assert "recent_sessions" in fields
        assert "performance_metrics" in fields
        
        # Test no sharing
        no_sharing_membership = GroupMembership(
            group_id="group_123",
            user_id="user_102",
            data_sharing_level=DataSharingLevel.NONE.value
        )
        
        fields = no_sharing_membership.get_shared_data_fields()
        assert len(fields) == 0
    
    def test_session_duration_calculation(self):
        """Test session duration calculation"""
        now = datetime.utcnow()
        session = CollaborativeSession(
            session_name="Test Session",
            host_id="user_123",
            group_id="group_456",
            actual_start=now,
            actual_end=now + timedelta(minutes=45)
        )
        
        duration = session.calculate_duration()
        assert duration == 45
    
    def test_group_member_count(self):
        """Test group member count calculation"""
        group = LearningGroup(
            name="Test Group",
            creator_id="user_123",
            max_members=5
        )
        
        # Mock memberships (in real implementation, this would be a relationship)
        group.memberships = [
            GroupMembership(group_id=group.id, user_id="user_1", is_active=True),
            GroupMembership(group_id=group.id, user_id="user_2", is_active=True),
            GroupMembership(group_id=group.id, user_id="user_3", is_active=False),  # Inactive
        ]
        
        assert group.get_member_count() == 2  # Only active members
        assert group.can_accept_new_members() is True
    
    def test_analytics_engagement_calculation(self):
        """Test analytics engagement rate calculation"""
        analytics = GroupAnalytics(
            group_id="group_123",
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow() + timedelta(days=7),
            period_type="weekly",
            total_members=10,
            active_members=7
        )
        
        engagement_rate = analytics.calculate_engagement_rate()
        assert engagement_rate == 70.0
        
        # Test zero members
        empty_analytics = GroupAnalytics(
            group_id="group_456",
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow() + timedelta(days=7),
            period_type="weekly",
            total_members=0,
            active_members=0
        )
        
        assert empty_analytics.calculate_engagement_rate() == 0.0


class TestCollaborativeEnums:
    """Test collaborative learning enums"""
    
    def test_group_role_enum(self):
        """Test GroupRole enum values"""
        assert GroupRole.OWNER.value == "owner"
        assert GroupRole.EDUCATOR.value == "educator"
        assert GroupRole.MODERATOR.value == "moderator"
        assert GroupRole.MEMBER.value == "member"
        assert GroupRole.OBSERVER.value == "observer"
    
    def test_group_privacy_enum(self):
        """Test GroupPrivacy enum values"""
        assert GroupPrivacy.PUBLIC.value == "public"
        assert GroupPrivacy.PRIVATE.value == "private"
        assert GroupPrivacy.INVITE_ONLY.value == "invite_only"
    
    def test_session_status_enum(self):
        """Test SessionStatus enum values"""
        assert SessionStatus.SCHEDULED.value == "scheduled"
        assert SessionStatus.ACTIVE.value == "active"
        assert SessionStatus.PAUSED.value == "paused"
        assert SessionStatus.COMPLETED.value == "completed"
        assert SessionStatus.CANCELLED.value == "cancelled"
    
    def test_data_sharing_level_enum(self):
        """Test DataSharingLevel enum values"""
        assert DataSharingLevel.NONE.value == "none"
        assert DataSharingLevel.BASIC.value == "basic"
        assert DataSharingLevel.DETAILED.value == "detailed"
        assert DataSharingLevel.FULL.value == "full"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])