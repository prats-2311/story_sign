"""
Test script for core services architecture
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.service_registry import initialize_platform_services, shutdown_platform_services
from core.service_container import get_service_container, get_service
from services.user_service import UserService
from services.content_service import ContentService
from services.session_service import SessionService
from services.analytics_service import AnalyticsService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_service_container():
    """Test basic service container functionality"""
    logger.info("Testing service container functionality")
    
    try:
        # Initialize services
        container = await initialize_platform_services()
        
        # Test service retrieval
        user_service = await container.get_service("UserService")
        content_service = await container.get_service("ContentService")
        session_service = await container.get_service("SessionService")
        analytics_service = await container.get_service("AnalyticsService")
        
        logger.info(f"Retrieved services: {[service.service_name for service in [user_service, content_service, session_service, analytics_service]]}")
        
        # Test service status
        status = container.get_service_status()
        logger.info(f"Service status: {status}")
        
        # Test basic service operations
        await test_user_service(user_service)
        await test_content_service(content_service)
        await test_session_service(session_service)
        await test_analytics_service(analytics_service)
        
        # Shutdown services
        await shutdown_platform_services(container)
        
        logger.info("Service container test completed successfully")
        
    except Exception as e:
        logger.error(f"Service container test failed: {e}")
        raise


async def test_user_service(user_service: UserService):
    """Test user service operations"""
    logger.info("Testing user service")
    
    # Test user creation
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User"
    }
    
    created_user = await user_service.create_user(user_data)
    logger.info(f"Created user: {created_user['id']}")
    
    # Test user retrieval
    retrieved_user = await user_service.get_user_by_id(created_user['id'])
    logger.info(f"Retrieved user: {retrieved_user['username']}")
    
    # Test user profile
    profile = await user_service.get_user_profile(created_user['id'])
    logger.info(f"User profile: {profile['language']}")
    
    # Test user progress
    progress = await user_service.get_user_progress(created_user['id'])
    logger.info(f"User progress: {len(progress)} records")


async def test_content_service(content_service: ContentService):
    """Test content service operations"""
    logger.info("Testing content service")
    
    # Test story creation
    story_data = {
        "title": "Test Story",
        "content": "This is a test story for ASL learning.",
        "difficulty_level": "beginner",
        "sentences": ["Hello world", "How are you?"],
        "is_public": True
    }
    
    created_story = await content_service.create_story(story_data, "test-user-id")
    logger.info(f"Created story: {created_story['id']}")
    
    # Test story retrieval
    retrieved_story = await content_service.get_story_by_id(created_story['id'])
    logger.info(f"Retrieved story: {retrieved_story['title']}")
    
    # Test story listing
    stories = await content_service.get_stories(limit=5)
    logger.info(f"Retrieved {len(stories)} stories")
    
    # Test story search
    search_results = await content_service.search_stories("test")
    logger.info(f"Search results: {len(search_results)} stories")


async def test_session_service(session_service: SessionService):
    """Test session service operations"""
    logger.info("Testing session service")
    
    # Test session creation
    session = await session_service.create_practice_session(
        user_id="test-user-id",
        story_id="test-story-id",
        session_type="individual"
    )
    logger.info(f"Created session: {session['id']}")
    
    # Test session retrieval
    retrieved_session = await session_service.get_session_by_id(session['id'])
    logger.info(f"Retrieved session: {retrieved_session['session_type']}")
    
    # Test sentence attempt
    attempt = await session_service.add_sentence_attempt(
        session_id=session['id'],
        sentence_index=0,
        target_sentence="Hello world",
        landmark_data={"hands": []},
        confidence_score=0.85,
        ai_feedback="Good job!",
        suggestions=["Keep practicing"]
    )
    logger.info(f"Added attempt: {attempt['id']}")
    
    # Test progress summary
    progress = await session_service.get_user_progress_summary("test-user-id")
    logger.info(f"Progress summary: {progress['total_sessions']} sessions")


async def test_analytics_service(analytics_service: AnalyticsService):
    """Test analytics service operations"""
    logger.info("Testing analytics service")
    
    # Test event tracking
    event = await analytics_service.track_event(
        user_id="test-user-id",
        event_type="session_start",
        module_name="asl_world",
        event_data={"story_id": "test-story-id"}
    )
    logger.info(f"Tracked event: {event['id']}")
    
    # Test user events retrieval
    events = await analytics_service.get_user_events("test-user-id")
    logger.info(f"Retrieved {len(events)} events")
    
    # Test learning insights
    insights = await analytics_service.get_learning_insights("test-user-id")
    logger.info(f"Learning insights: {len(insights['recommendations'])} recommendations")
    
    # Test platform metrics
    metrics = await analytics_service.get_platform_metrics()
    logger.info(f"Platform metrics: {metrics['user_metrics']['total_users']} users")


async def main():
    """Main test function"""
    logger.info("Starting core services architecture test")
    
    try:
        await test_service_container()
        logger.info("All tests passed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())