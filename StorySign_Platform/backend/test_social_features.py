"""
Test script for social learning features
Tests the complete social functionality including friendships, feedback, ratings, and progress sharing
"""

import asyncio
import uuid
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from models.social import (
    Friendship, CommunityFeedback, CommunityRating, ProgressShare, SocialInteraction,
    FriendshipStatus, FeedbackType, RatingType, PrivacyLevel
)
from models.user import User, UserProfile
from repositories.social_repository import SocialRepository


async def create_test_users(session: AsyncSession):
    """Create test users for social features testing"""
    
    users = []
    
    # Create test users
    for i in range(3):
        user = User(
            id=str(uuid.uuid4()),
            email=f"testuser{i+1}@example.com",
            username=f"testuser{i+1}",
            password_hash="hashed_password",
            first_name=f"Test{i+1}",
            last_name="User",
            is_active=True
        )
        
        session.add(user)
        users.append(user)
    
    await session.flush()
    
    # Create profiles for users
    for user in users:
        profile = UserProfile(
            id=str(uuid.uuid4()),
            user_id=user.id,
            bio=f"Test user profile for {user.username}",
            timezone="UTC",
            language="en"
        )
        session.add(profile)
    
    await session.commit()
    return users


async def test_friendship_features(session: AsyncSession, users):
    """Test friendship management features"""
    
    print("\n=== Testing Friendship Features ===")
    
    social_repo = SocialRepository(session)
    
    # Test sending friend request
    print("1. Testing friend request...")
    result = await social_service.send_friend_request(
        requester_id=users[0].id,
        addressee_username=users[1].username,
        message="Hi! Let's practice ASL together!"
    )
    print(f"   Friend request sent: {result['success']}")
    
    # Test getting friends list with pending requests
    print("2. Testing friends list...")
    friends_data = await social_service.get_friends_list(
        user_id=users[1].id,
        include_pending=True
    )
    print(f"   Incoming requests: {friends_data['pending_incoming_count']}")
    
    # Test accepting friend request
    print("3. Testing friend request acceptance...")
    if friends_data['incoming_requests']:
        friendship_id = friends_data['incoming_requests'][0]['friendship_id']
        result = await social_service.respond_to_friend_request(
            friendship_id=friendship_id,
            user_id=users[1].id,
            accept=True
        )
        print(f"   Friend request accepted: {result['success']}")
    
    # Test getting friends after acceptance
    print("4. Testing friends list after acceptance...")
    friends_data = await social_service.get_friends_list(users[0].id)
    print(f"   Friends count: {friends_data['friends_count']}")
    
    return True


async def test_feedback_features(session: AsyncSession, users):
    """Test community feedback features"""
    
    print("\n=== Testing Community Feedback Features ===")
    
    social_service = SocialService(session)
    
    # Test giving feedback
    print("1. Testing giving feedback...")
    result = await social_service.give_feedback(
        giver_id=users[0].id,
        receiver_username=users[1].username,
        feedback_type="encouragement",
        content="Great job on your fingerspelling! Keep up the excellent work!",
        is_public=True,
        tags=["fingerspelling", "practice"],
        skill_areas=["manual dexterity", "letter formation"]
    )
    print(f"   Feedback given: {result['success']}")
    
    # Test getting received feedback
    print("2. Testing getting received feedback...")
    feedback_data = await social_service.get_user_feedback(
        user_id=users[1].id,
        feedback_direction="received"
    )
    print(f"   Received feedback count: {feedback_data['total_count']}")
    
    # Test giving different types of feedback
    print("3. Testing different feedback types...")
    feedback_types = ["suggestion", "correction", "praise"]
    for feedback_type in feedback_types:
        result = await social_service.give_feedback(
            giver_id=users[1].id,
            receiver_username=users[0].username,
            feedback_type=feedback_type,
            content=f"This is a {feedback_type} feedback for testing purposes.",
            is_public=True
        )
        print(f"   {feedback_type.capitalize()} feedback given: {result['success']}")
    
    # Test rating feedback helpfulness
    print("4. Testing feedback helpfulness rating...")
    feedback_data = await social_service.get_user_feedback(
        user_id=users[1].id,
        feedback_direction="received"
    )
    
    if feedback_data['feedback']:
        feedback_id = feedback_data['feedback'][0]['feedback_id']
        result = await social_service.rate_feedback_helpfulness(
            feedback_id=feedback_id,
            user_id=users[2].id,  # Different user rating
            is_helpful=True
        )
        print(f"   Helpfulness rating submitted: {result['success']}")
    
    return True


async def test_rating_features(session: AsyncSession, users):
    """Test community rating features"""
    
    print("\n=== Testing Community Rating Features ===")
    
    social_service = SocialService(session)
    
    # Create a dummy story ID for testing
    story_id = str(uuid.uuid4())
    
    # Test rating content
    print("1. Testing content rating...")
    result = await social_service.rate_content(
        user_id=users[0].id,
        rating_type="story",
        target_id=story_id,
        rating_value=4.5,
        review_text="This story was very helpful for practicing basic signs!",
        detailed_ratings={
            "difficulty": 3.0,
            "clarity": 5.0,
            "engagement": 4.0,
            "educational_value": 4.5
        },
        user_experience_level="beginner",
        completion_percentage=100.0
    )
    print(f"   Rating submitted: {result['success']}")
    
    # Test multiple ratings for the same content
    print("2. Testing multiple ratings...")
    for i, user in enumerate(users[1:], 1):
        result = await social_service.rate_content(
            user_id=user.id,
            rating_type="story",
            target_id=story_id,
            rating_value=4.0 + (i * 0.2),
            review_text=f"Review from user {i+1}",
            detailed_ratings={
                "difficulty": 3.0 + i,
                "clarity": 4.0 + i,
                "engagement": 3.5 + i,
                "educational_value": 4.0 + i
            }
        )
        print(f"   Rating {i+1} submitted: {result['success']}")
    
    # Test getting ratings for content
    print("3. Testing getting content ratings...")
    ratings_data = await social_service.get_content_ratings(
        rating_type="story",
        target_id=story_id
    )
    print(f"   Total ratings: {ratings_data['statistics']['total_ratings']}")
    print(f"   Average rating: {ratings_data['statistics']['average_rating']:.2f}")
    
    return True


async def test_progress_sharing_features(session: AsyncSession, users):
    """Test progress sharing features"""
    
    print("\n=== Testing Progress Sharing Features ===")
    
    social_service = SocialService(session)
    
    # Test sharing progress
    print("1. Testing progress sharing...")
    result = await social_service.share_progress(
        user_id=users[0].id,
        share_type="achievement",
        title="Completed First Story!",
        description="Just finished my first ASL story with 95% accuracy!",
        progress_data={
            "score": 95,
            "sentences_completed": 10,
            "total_sentences": 10,
            "practice_time": 25
        },
        achievement_type="milestone",
        privacy_level="friends",
        allow_comments=True,
        allow_reactions=True
    )
    print(f"   Progress shared: {result['success']}")
    
    # Test sharing different types of progress
    print("2. Testing different progress types...")
    progress_types = [
        {
            "share_type": "streak",
            "title": "7-Day Practice Streak!",
            "achievement_type": "streak",
            "progress_data": {"streak_days": 7, "total_practice_time": 180}
        },
        {
            "share_type": "score",
            "title": "New High Score!",
            "achievement_type": "score",
            "progress_data": {"score": 98, "previous_best": 85}
        }
    ]
    
    for progress in progress_types:
        result = await social_service.share_progress(
            user_id=users[1].id,
            **progress,
            privacy_level="friends"
        )
        print(f"   {progress['share_type'].capitalize()} shared: {result['success']}")
    
    # Test getting progress feed
    print("3. Testing progress feed...")
    feed_data = await social_service.get_progress_feed(
        user_id=users[0].id,
        feed_type="friends"
    )
    print(f"   Feed items: {feed_data['total_count']}")
    
    # Test interacting with progress shares
    print("4. Testing progress share interactions...")
    if feed_data['shares']:
        share_id = feed_data['shares'][0]['share']['share_id']
        
        # Test liking a share
        result = await social_service.interact_with_share(
            user_id=users[2].id,
            share_id=share_id,
            interaction_type="like"
        )
        print(f"   Like interaction: {result['success']}")
        
        # Test commenting on a share
        result = await social_service.interact_with_share(
            user_id=users[2].id,
            share_id=share_id,
            interaction_type="comment",
            content="Congratulations! That's amazing progress!"
        )
        print(f"   Comment interaction: {result['success']}")
    
    return True


async def test_social_discovery_features(session: AsyncSession, users):
    """Test social discovery and analytics features"""
    
    print("\n=== Testing Social Discovery Features ===")
    
    social_service = SocialService(session)
    
    # Test user search
    print("1. Testing user search...")
    search_results = await social_service.search_users(
        query="test",
        searcher_id=users[0].id
    )
    print(f"   Search results: {search_results['total_found']}")
    
    # Test getting user social profile
    print("2. Testing user social profile...")
    profile_data = await social_service.get_user_social_profile(
        user_id=users[1].id,
        viewer_id=users[0].id
    )
    print(f"   Profile loaded for: {profile_data['user']['username']}")
    print(f"   Friends count: {profile_data['social_stats']['friends_count']}")
    print(f"   Feedback given: {profile_data['social_stats']['feedback_given']}")
    
    # Test community leaderboard
    print("3. Testing community leaderboard...")
    leaderboard_data = await social_service.get_community_leaderboard(
        metric="progress_shares",
        time_period="month"
    )
    print(f"   Leaderboard generated for: {leaderboard_data['metric']}")
    
    return True


async def main():
    """Main test function"""
    
    print("Starting Social Learning Features Test")
    print("=" * 50)
    
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
            print("Creating test users...")
            users = await create_test_users(session)
            print(f"Created {len(users)} test users")
            
            # Run all tests
            tests = [
                test_friendship_features,
                test_feedback_features,
                test_rating_features,
                test_progress_sharing_features,
                test_social_discovery_features
            ]
            
            results = []
            for test_func in tests:
                try:
                    result = await test_func(session, users)
                    results.append(result)
                except Exception as e:
                    print(f"   ERROR in {test_func.__name__}: {e}")
                    results.append(False)
            
            # Print summary
            print("\n" + "=" * 50)
            print("TEST SUMMARY")
            print("=" * 50)
            
            passed = sum(results)
            total = len(results)
            
            print(f"Tests passed: {passed}/{total}")
            
            if passed == total:
                print("🎉 All social learning features are working correctly!")
            else:
                print("⚠️  Some tests failed. Check the output above for details.")
            
            # Clean up test data
            print("\nCleaning up test data...")
            for user in users:
                await session.delete(user)
            await session.commit()
            print("Test data cleaned up successfully")
    
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())