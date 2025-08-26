"""
Comprehensive tests for collaborative learning features
Tests models, repositories, services, and API endpoints
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from models.base import Base
from models.collaborative import (
    LearningGroup, GroupMembership, CollaborativeSession, GroupAnalytics,
    GroupRole, GroupPrivacy, SessionStatus, DataSharingLevel
)
from models.user import User, UserProfile
from models.progress import PracticeSession, UserProgress
from repositories.collaborative_repository import (
    LearningGroupRepository, GroupMembershipRepository,
    CollaborativeSessionRepository, GroupAnalyticsRepository
)
from services.collaborative_service import CollaborativeService
from migrations.create_collaborative_tables import create_collaborative_tables


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def async_session():
    """Create async database session for testing"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        # Create collaborative tables
        await create_collaborative_tables(session)
        yield session
    
    await engine.dispose()


@pytest.fixture
async def sample_users(async_session: AsyncSession):
    """Create sample users for testing"""
    users = []
    
    for i in range(5):
        user = User(
            email=f"user{i}@example.com",
            username=f"user{i}",
            password_hash="hashed_password",
            first_name=f"User{i}",
            last_name="Test",
            role="learner" if i > 0 else "educator"
        )
        async_session.add(user)
        users.append(user)
    
    await async_session.commit()
    
    # Refresh to get IDs
    for user in users:
        await async_session.refresh(user)
    
    return users


@pytest.fixture
async def sample_group(async_session: AsyncSession, sample_users):
    """Create a sample learning group"""
    creator = sample_users[0]
    
    group = LearningGroup(
        name="Test ASL Group",
        description="A test group for ASL learning",
        creator_id=creator.id,
        privacy_level=GroupPrivacy.PRIVATE.value,
        max_members=10,
        skill_focus=["fingerspelling", "basic_vocabulary"],
        difficulty_level="beginner"
    )
    
    async_session.add(group)
    await async_session.commit()
    await async_session.refresh(group)
    
    return group


class TestCollaborativeModels:
    """Test collaborative learning models"""
    
    async def test_learning_group_creation(self, async_session: AsyncSession, sample_users):
        """Test learning group model creation and validation"""
        creator = sample_users[0]
        
        group = LearningGroup(
            name="Test Group",
            description="Test Description",
            creator_id=creator.id,
            privacy_level=GroupPrivacy.PUBLIC.value,
            max_members=20,
            skill_focus=["vocabulary", "grammar"],
            difficulty_level="intermediate"
        )
        
        async_session.add(group)
        await async_session.commit()
        
        assert group.id is not None
        assert group.name == "Test Group"
        assert group.creator_id == creator.id
        assert group.privacy_level == GroupPrivacy.PUBLIC.value
        assert group.max_members == 20
        assert group.skill_focus == ["vocabulary", "grammar"]
        assert group.difficulty_level == "intermediate"
        assert group.is_active is True
        assert group.total_sessions == 0
    
    async def test_group_membership_creation(self, async_session: AsyncSession, sample_group, sample_users):
        """Test group membership model creation"""
        user = sample_users[1]
        
        membership = GroupMembership(
            group_id=sample_group.id,
            user_id=user.id,
            role=GroupRole.MEMBER.value,
            data_sharing_level=DataSharingLevel.BASIC.value,
            share_progress=True,
            share_performance=False
        )
        
        async_session.add(membership)
        await async_session.commit()
        
        assert membership.id is not None
        assert membership.group_id == sample_group.id
        assert membership.user_id == user.id
        assert membership.role == GroupRole.MEMBER.value
        assert membership.is_active is True
        assert membership.data_sharing_level == DataSharingLevel.BASIC.value
        assert membership.share_progress is True
        assert membership.share_performance is False
    
    async def test_collaborative_session_creation(self, async_session: AsyncSession, sample_group, sample_users):
        """Test collaborative session model creation"""
        host = sample_users[0]
        
        session = CollaborativeSession(
            session_name="Test Session",
            description="Test collaborative session",
            host_id=host.id,
            group_id=sample_group.id,
            scheduled_start=datetime.utcnow() + timedelta(hours=1),
            scheduled_end=datetime.utcnow() + timedelta(hours=2),
            max_participants=5,
            difficulty_level="beginner",
            skill_focus=["fingerspelling"]
        )
        
        async_session.add(session)
        await async_session.commit()
        
        assert session.id is not None
        assert session.session_name == "Test Session"
        assert session.host_id == host.id
        assert session.group_id == sample_group.id
        assert session.status == SessionStatus.SCHEDULED.value
        assert session.max_participants == 5
        assert session.difficulty_level == "beginner"
    
    async def test_group_analytics_creation(self, async_session: AsyncSession, sample_group):
        """Test group analytics model creation"""
        now = datetime.utcnow()
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=7)
        
        analytics = GroupAnalytics(
            group_id=sample_group.id,
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
        
        async_session.add(analytics)
        await async_session.commit()
        
        assert analytics.id is not None
        assert analytics.group_id == sample_group.id
        assert analytics.period_type == "weekly"
        assert analytics.total_members == 5
        assert analytics.active_members == 3
        assert analytics.calculate_engagement_rate() == 60.0


class TestCollaborativeRepositories:
    """Test collaborative learning repositories"""
    
    async def test_learning_group_repository(self, async_session: AsyncSession, sample_users):
        """Test learning group repository operations"""
        repo = LearningGroupRepository(async_session)
        creator = sample_users[0]
        
        # Test create group
        group = await repo.create_group(
            name="Repository Test Group",
            creator_id=creator.id,
            description="Test group created via repository",
            privacy_level=GroupPrivacy.PRIVATE.value,
            max_members=15
        )
        
        assert group is not None
        assert group.name == "Repository Test Group"
        assert group.creator_id == creator.id
        
        # Test get groups by creator
        creator_groups = await repo.get_groups_by_creator(creator.id)
        assert len(creator_groups) >= 1
        assert any(g.id == group.id for g in creator_groups)
        
        # Test generate and get by join code
        group.generate_join_code()
        await async_session.commit()
        
        found_group = await repo.get_group_by_join_code(group.join_code)
        assert found_group is not None
        assert found_group.id == group.id
    
    async def test_group_membership_repository(self, async_session: AsyncSession, sample_group, sample_users):
        """Test group membership repository operations"""
        repo = GroupMembershipRepository(async_session)
        user = sample_users[1]
        
        # Test create membership
        membership = await repo.create_membership(
            group_id=sample_group.id,
            user_id=user.id,
            role=GroupRole.MEMBER.value,
            invited_by=sample_users[0].id
        )
        
        assert membership is not None
        assert membership.group_id == sample_group.id
        assert membership.user_id == user.id
        assert membership.role == GroupRole.MEMBER.value
        
        # Test get user memberships
        user_memberships = await repo.get_user_memberships(user.id)
        assert len(user_memberships) >= 1
        assert any(m.id == membership.id for m in user_memberships)
        
        # Test get group members
        group_members = await repo.get_group_members(sample_group.id)
        assert len(group_members) >= 1
        assert any(m.user_id == user.id for m in group_members)
        
        # Test update role
        updated_membership = await repo.update_membership_role(
            sample_group.id, user.id, GroupRole.MODERATOR.value, sample_users[0].id
        )
        assert updated_membership.role == GroupRole.MODERATOR.value
    
    async def test_collaborative_session_repository(self, async_session: AsyncSession, sample_group, sample_users):
        """Test collaborative session repository operations"""
        repo = CollaborativeSessionRepository(async_session)
        host = sample_users[0]
        
        # Test create session
        session = await repo.create_session(
            session_name="Repository Test Session",
            host_id=host.id,
            group_id=sample_group.id,
            description="Test session via repository",
            scheduled_start=datetime.utcnow() + timedelta(hours=1),
            max_participants=8
        )
        
        assert session is not None
        assert session.session_name == "Repository Test Session"
        assert session.host_id == host.id
        assert session.group_id == sample_group.id
        
        # Test get group sessions
        group_sessions = await repo.get_group_sessions(sample_group.id)
        assert len(group_sessions) >= 1
        assert any(s.id == session.id for s in group_sessions)
        
        # Test add participant
        participant = sample_users[1]
        success = await repo.add_participant(session.id, participant.id)
        assert success is True
        
        # Test start session
        started_session = await repo.start_session(session.id)
        assert started_session.status == SessionStatus.ACTIVE.value
        assert started_session.actual_start is not None
        
        # Test end session
        performance_summary = {"average_score": 0.88, "completion_rate": 0.95}
        ended_session = await repo.end_session(session.id, performance_summary)
        assert ended_session.status == SessionStatus.COMPLETED.value
        assert ended_session.actual_end is not None
        assert ended_session.performance_summary == performance_summary


class TestCollaborativeService:
    """Test collaborative learning service layer"""
    
    async def test_create_learning_group(self, async_session: AsyncSession, sample_users):
        """Test creating a learning group via service"""
        service = CollaborativeService(async_session)
        creator = sample_users[0]
        
        group, error = await service.create_learning_group(
            creator_id=creator.id,
            name="Service Test Group",
            description="Test group via service",
            privacy_level=GroupPrivacy.INVITE_ONLY.value,
            max_members=12,
            skill_focus=["vocabulary", "grammar"],
            difficulty_level="intermediate"
        )
        
        assert error is None
        assert group is not None
        assert group.name == "Service Test Group"
        assert group.creator_id == creator.id
        assert group.privacy_level == GroupPrivacy.INVITE_ONLY.value
        assert group.join_code is not None  # Should be generated for invite-only groups
    
    async def test_join_and_leave_group(self, async_session: AsyncSession, sample_group, sample_users):
        """Test joining and leaving a group via service"""
        service = CollaborativeService(async_session)
        user = sample_users[1]
        
        # Generate join code for the group
        sample_group.generate_join_code()
        await async_session.commit()
        
        # Test join group
        membership, error = await service.join_group(
            user_id=user.id,
            join_code=sample_group.join_code
        )
        
        assert error is None
        assert membership is not None
        assert membership.user_id == user.id
        assert membership.group_id == sample_group.id
        assert membership.is_active is True
        
        # Test leave group
        success, error = await service.leave_group(user.id, sample_group.id)
        
        assert error is None
        assert success is True
    
    async def test_privacy_settings(self, async_session: AsyncSession, sample_group, sample_users):
        """Test updating privacy settings via service"""
        service = CollaborativeService(async_session)
        user = sample_users[1]
        
        # First join the group
        sample_group.generate_join_code()
        await async_session.commit()
        
        membership, _ = await service.join_group(
            user_id=user.id,
            join_code=sample_group.join_code
        )
        
        # Test update privacy settings
        privacy_settings = {
            "data_sharing_level": DataSharingLevel.DETAILED.value,
            "share_progress": True,
            "share_performance": True,
            "share_practice_sessions": False,
            "allow_peer_feedback": True
        }
        
        updated_membership, error = await service.update_privacy_settings(
            user_id=user.id,
            group_id=sample_group.id,
            privacy_settings=privacy_settings
        )
        
        assert error is None
        assert updated_membership is not None
        assert updated_membership.data_sharing_level == DataSharingLevel.DETAILED.value
        assert updated_membership.share_progress is True
        assert updated_membership.share_performance is True
        assert updated_membership.share_practice_sessions is False
    
    async def test_collaborative_session_lifecycle(self, async_session: AsyncSession, sample_group, sample_users):
        """Test complete collaborative session lifecycle via service"""
        service = CollaborativeService(async_session)
        host = sample_users[0]
        participant = sample_users[1]
        
        # Create host membership
        await service.membership_repo.create_membership(
            group_id=sample_group.id,
            user_id=host.id,
            role=GroupRole.EDUCATOR.value
        )
        
        # Create participant membership
        await service.membership_repo.create_membership(
            group_id=sample_group.id,
            user_id=participant.id,
            role=GroupRole.MEMBER.value
        )
        
        # Test create session
        session, error = await service.create_collaborative_session(
            host_id=host.id,
            group_id=sample_group.id,
            session_name="Service Test Session",
            description="Complete lifecycle test",
            scheduled_start=datetime.utcnow() + timedelta(minutes=30),
            scheduled_end=datetime.utcnow() + timedelta(hours=1, minutes=30),
            max_participants=5,
            difficulty_level="beginner"
        )
        
        assert error is None
        assert session is not None
        assert session.status == SessionStatus.SCHEDULED.value
        
        # Test join session
        success, error = await service.join_collaborative_session(session.id, participant.id)
        assert error is None
        assert success is True
        
        # Test start session
        started_session, error = await service.start_collaborative_session(session.id, host.id)
        assert error is None
        assert started_session.status == SessionStatus.ACTIVE.value
        
        # Test end session
        performance_summary = {
            "participants": [
                {"user_id": participant.id, "score": 0.92, "completion": 1.0}
            ],
            "average_score": 0.92,
            "total_duration": 45
        }
        
        ended_session, error = await service.end_collaborative_session(
            session.id, host.id, performance_summary
        )
        
        assert error is None
        assert ended_session.status == SessionStatus.COMPLETED.value
        assert ended_session.performance_summary == performance_summary
    
    async def test_group_analytics_generation(self, async_session: AsyncSession, sample_group, sample_users):
        """Test group analytics generation via service"""
        service = CollaborativeService(async_session)
        
        # Create some sample data
        for i, user in enumerate(sample_users[:3]):
            # Create membership
            await service.membership_repo.create_membership(
                group_id=sample_group.id,
                user_id=user.id,
                role=GroupRole.MEMBER.value if i > 0 else GroupRole.EDUCATOR.value
            )
        
        # Generate analytics
        analytics, error = await service.generate_group_analytics(
            group_id=sample_group.id,
            period_type="weekly"
        )
        
        assert error is None
        assert analytics is not None
        assert analytics.group_id == sample_group.id
        assert analytics.period_type == "weekly"
        assert analytics.total_members >= 0
        
        # Test get analytics summary
        summary, error = await service.get_group_analytics_summary(
            group_id=sample_group.id,
            requesting_user_id=sample_users[0].id,  # Educator role
            period_type="weekly"
        )
        
        assert error is None
        assert isinstance(summary, list)


class TestCollaborativeIntegration:
    """Integration tests for collaborative features"""
    
    async def test_complete_group_workflow(self, async_session: AsyncSession, sample_users):
        """Test complete workflow from group creation to analytics"""
        service = CollaborativeService(async_session)
        
        # Step 1: Create group
        creator = sample_users[0]
        group, error = await service.create_learning_group(
            creator_id=creator.id,
            name="Integration Test Group",
            description="Complete workflow test",
            privacy_level=GroupPrivacy.PRIVATE.value,
            max_members=10,
            skill_focus=["fingerspelling", "vocabulary"],
            difficulty_level="beginner"
        )
        
        assert error is None
        assert group is not None
        
        # Step 2: Add members
        members = sample_users[1:4]
        for member in members:
            membership, error = await service.join_group(
                user_id=member.id,
                join_code=group.join_code
            )
            assert error is None
            assert membership is not None
        
        # Step 3: Create collaborative session
        session, error = await service.create_collaborative_session(
            host_id=creator.id,
            group_id=group.id,
            session_name="Integration Test Session",
            description="Test session for workflow",
            scheduled_start=datetime.utcnow() + timedelta(minutes=5),
            max_participants=5
        )
        
        assert error is None
        assert session is not None
        
        # Step 4: Members join session
        for member in members:
            success, error = await service.join_collaborative_session(session.id, member.id)
            assert error is None
            assert success is True
        
        # Step 5: Start and end session
        started_session, error = await service.start_collaborative_session(session.id, creator.id)
        assert error is None
        
        ended_session, error = await service.end_collaborative_session(
            session.id, creator.id, {"average_score": 0.85}
        )
        assert error is None
        
        # Step 6: Generate analytics
        analytics, error = await service.generate_group_analytics(group.id, "weekly")
        assert error is None
        assert analytics is not None
        
        # Step 7: Verify data integrity
        user_groups = await service.get_user_groups(creator.id)
        assert len(user_groups) >= 1
        assert any(g["id"] == group.id for g in user_groups)
    
    async def test_privacy_and_data_sharing(self, async_session: AsyncSession, sample_users):
        """Test privacy controls and data sharing functionality"""
        service = CollaborativeService(async_session)
        
        # Create group and add members with different privacy settings
        creator = sample_users[0]
        group, _ = await service.create_learning_group(
            creator_id=creator.id,
            name="Privacy Test Group",
            privacy_level=GroupPrivacy.PRIVATE.value
        )
        
        # Add members with different sharing levels
        sharing_configs = [
            {"level": DataSharingLevel.NONE.value, "share_progress": False},
            {"level": DataSharingLevel.BASIC.value, "share_progress": True},
            {"level": DataSharingLevel.DETAILED.value, "share_progress": True, "share_performance": True},
            {"level": DataSharingLevel.FULL.value, "share_progress": True, "share_performance": True, "share_practice_sessions": True}
        ]
        
        for i, config in enumerate(sharing_configs):
            member = sample_users[i + 1]
            
            # Join group
            membership, _ = await service.join_group(
                user_id=member.id,
                join_code=group.join_code
            )
            
            # Update privacy settings
            privacy_settings = {
                "data_sharing_level": config["level"],
                "share_progress": config.get("share_progress", False),
                "share_performance": config.get("share_performance", False),
                "share_practice_sessions": config.get("share_practice_sessions", False)
            }
            
            await service.update_privacy_settings(
                user_id=member.id,
                group_id=group.id,
                privacy_settings=privacy_settings
            )
        
        # Test shared data retrieval
        shared_data = await service.get_shared_member_data(group.id, creator.id)
        
        # Should only include members who allow data sharing
        sharing_members = [m for m in shared_data if m["user_id"] != creator.id]
        assert len(sharing_members) == 3  # Excluding NONE level member
        
        # Verify different levels of data are shared appropriately
        basic_member = next((m for m in sharing_members if "current_level" in m), None)
        assert basic_member is not None
        
        detailed_member = next((m for m in sharing_members if "average_score" in m), None)
        # Would be not None if we had actual progress data
        
        full_member = next((m for m in sharing_members if "recent_sessions" in m), None)
        # Would be not None if we had actual session data


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])