"""
Simple test for social learning models
Tests basic model creation and database operations
"""

import asyncio
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config import get_config
from models.social import (
    Friendship, CommunityFeedback, CommunityRating, ProgressShare, SocialInteraction,
    FriendshipStatus, FeedbackType, RatingType, PrivacyLevel
)
from models.user import User, UserProfile


async def test_social_models():
    """Test social learning models"""
    
    print("Testing Social Learning Models")
    print("=" * 40)
    
    # Get database configuration
    config = get_config()
    db_config = config.database
    
    # Create async engine
    engine = create_async_engine(
        db_config.get_connection_url(async_driver=True),
        echo=False,
        connect_args=db_config.get_connect_args()
    )
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    try:
        async with async_session() as session:
            # Create test users
            user1 = User(
                id=str(uuid.uuid4()),
                email="testuser1@example.com",
                username="testuser1",
                password_hash="hashed_password",
                first_name="Test1",
                last_name="User",
                is_active=True,
                preferences={}
            )
            
            user2 = User(
                id=str(uuid.uuid4()),
                email="testuser2@example.com", 
                username="testuser2",
                password_hash="hashed_password",
                first_name="Test2",
                last_name="User",
                is_active=True,
                preferences={}
            )
            
            session.add(user1)
            session.add(user2)
            await session.commit()
            
            print("✓ Created test users")
            
            # Test Friendship model
            friendship = Friendship(
                id=str(uuid.uuid4()),
                requester_id=user1.id,
                addressee_id=user2.id,
                status=FriendshipStatus.PENDING.value
            )
            
            session.add(friendship)
            await session.commit()
            print("✓ Created friendship")
            
            # Test CommunityFeedback model
            feedback = CommunityFeedback(
                id=str(uuid.uuid4()),
                giver_id=user1.id,
                receiver_id=user2.id,
                feedback_type=FeedbackType.ENCOURAGEMENT.value,
                content="Great job on your practice!",
                is_public=True
            )
            
            session.add(feedback)
            await session.commit()
            print("✓ Created community feedback")
            
            # Test CommunityRating model
            rating = CommunityRating(
                id=str(uuid.uuid4()),
                user_id=user1.id,
                rating_type=RatingType.STORY.value,
                target_id=str(uuid.uuid4()),
                rating_value=4.5,
                review_text="Excellent story for beginners!"
            )
            
            session.add(rating)
            await session.commit()
            print("✓ Created community rating")
            
            # Test ProgressShare model
            progress_share = ProgressShare(
                id=str(uuid.uuid4()),
                user_id=user1.id,
                share_type="achievement",
                title="Completed First Story!",
                description="Just finished my first ASL story!",
                privacy_level=PrivacyLevel.FRIENDS.value,
                progress_data={"score": 95, "time": 25}
            )
            
            session.add(progress_share)
            await session.commit()
            print("✓ Created progress share")
            
            # Test SocialInteraction model
            interaction = SocialInteraction(
                id=str(uuid.uuid4()),
                user_id=user2.id,
                target_type="progress_share",
                target_id=progress_share.id,
                interaction_type="like"
            )
            
            session.add(interaction)
            await session.commit()
            print("✓ Created social interaction")
            
            print("\n🎉 All social models created successfully!")
            
            # Clean up
            await session.delete(interaction)
            await session.delete(progress_share)
            await session.delete(rating)
            await session.delete(feedback)
            await session.delete(friendship)
            await session.delete(user1)
            await session.delete(user2)
            await session.commit()
            
            print("✓ Cleaned up test data")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_social_models())