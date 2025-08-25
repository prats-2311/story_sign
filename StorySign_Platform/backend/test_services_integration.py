"""
Integration test for core services with existing functionality
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.service_registry import initialize_platform_services, shutdown_platform_services
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


async def test_asl_world_integration():
    """Test integration with ASL World functionality"""
    logger.info("Testing ASL World integration with services")
    
    try:
        # Initialize services
        container = await initialize_platform_services()
        
        # Get services
        user_service = await container.get_service("UserService")
        content_service = await container.get_service("ContentService")
        session_service = await container.get_service("SessionService")
        analytics_service = await container.get_service("AnalyticsService")
        
        # Simulate ASL World workflow
        
        # 1. Create a user
        user_data = {
            "email": "asl_learner@example.com",
            "username": "asl_learner",
            "first_name": "ASL",
            "last_name": "Learner"
        }
        user = await user_service.create_user(user_data)
        logger.info(f"Created ASL learner: {user['id']}")
        
        # 2. Create a story (simulating AI-generated story)
        story_data = {
            "title": "My First ASL Story",
            "content": "A beginner-friendly story for ASL learning",
            "difficulty_level": "beginner",
            "sentences": [
                "Hello, my name is Sarah.",
                "I am learning sign language.",
                "This is fun and exciting!"
            ],
            "is_public": True,
            "metadata": {
                "generated_by": "ai",
                "topics": ["greetings", "introductions"],
                "estimated_duration": 180
            }
        }
        story = await content_service.create_story(story_data, user['id'])
        logger.info(f"Created story: {story['title']}")
        
        # 3. Start a practice session
        session = await session_service.create_practice_session(
            user_id=user['id'],
            story_id=story['id'],
            session_type="individual"
        )
        logger.info(f"Started practice session: {session['id']}")
        
        # 4. Track analytics events
        await analytics_service.track_event(
            user_id=user['id'],
            event_type="session_start",
            module_name="asl_world",
            event_data={
                "story_id": story['id'],
                "story_title": story['title'],
                "difficulty_level": story['difficulty_level']
            },
            session_id=session['id']
        )
        
        # 5. Simulate sentence attempts
        for i, sentence in enumerate(story['sentences']):
            # Simulate MediaPipe landmark data
            landmark_data = {
                "hands": [{"landmarks": [{"x": 0.5, "y": 0.5, "z": 0.0}] * 21}],
                "face": {"landmarks": [{"x": 0.5, "y": 0.5, "z": 0.0}] * 468},
                "pose": {"landmarks": [{"x": 0.5, "y": 0.5, "z": 0.0}] * 33}
            }
            
            # Add sentence attempt
            attempt = await session_service.add_sentence_attempt(
                session_id=session['id'],
                sentence_index=i,
                target_sentence=sentence,
                landmark_data=landmark_data,
                confidence_score=0.75 + (i * 0.05),  # Improving confidence
                ai_feedback=f"Good job on sentence {i+1}! Keep practicing.",
                suggestions=["Maintain clear hand positions", "Keep steady pace"]
            )
            
            # Track attempt event
            await analytics_service.track_event(
                user_id=user['id'],
                event_type="sentence_attempt",
                module_name="asl_world",
                event_data={
                    "sentence_index": i,
                    "target_sentence": sentence,
                    "confidence_score": attempt['confidence_score'],
                    "attempt_duration": 15.0 + (i * 2.0)
                },
                session_id=session['id']
            )
            
            logger.info(f"Completed attempt {i+1}: {sentence[:30]}...")
        
        # 6. Complete the session
        final_score = 82.5
        completed_session = await session_service.complete_session(session['id'], final_score)
        logger.info(f"Completed session with score: {final_score}")
        
        # Track session completion
        await analytics_service.track_event(
            user_id=user['id'],
            event_type="session_complete",
            module_name="asl_world",
            event_data={
                "final_score": final_score,
                "sentences_completed": len(story['sentences']),
                "session_duration": 180
            },
            session_id=session['id']
        )
        
        # 7. Get learning insights
        insights = await analytics_service.get_learning_insights(user['id'])
        logger.info(f"Generated insights with {len(insights['recommendations'])} recommendations")
        
        # 8. Get user progress
        progress_summary = await session_service.get_user_progress_summary(user['id'])
        logger.info(f"User progress: {progress_summary['total_sessions']} sessions, "
                   f"avg score: {progress_summary['average_score']}")
        
        # 9. Test content discovery
        stories = await content_service.get_stories(difficulty_level="beginner")
        logger.info(f"Found {len(stories)} beginner stories")
        
        # 10. Test search functionality
        search_results = await content_service.search_stories("ASL")
        logger.info(f"Search for 'ASL' returned {len(search_results)} results")
        
        # Shutdown services
        await shutdown_platform_services(container)
        
        logger.info("ASL World integration test completed successfully!")
        
    except Exception as e:
        logger.error(f"ASL World integration test failed: {e}")
        raise


async def test_service_performance():
    """Test service performance with multiple operations"""
    logger.info("Testing service performance")
    
    try:
        # Initialize services
        container = await initialize_platform_services()
        
        # Get services
        user_service = await container.get_service("UserService")
        content_service = await container.get_service("ContentService")
        analytics_service = await container.get_service("AnalyticsService")
        
        # Create multiple users and content
        users = []
        stories = []
        
        # Create 10 users
        for i in range(10):
            user_data = {
                "email": f"user{i}@example.com",
                "username": f"user{i}",
                "first_name": f"User",
                "last_name": f"{i}"
            }
            user = await user_service.create_user(user_data)
            users.append(user)
        
        logger.info(f"Created {len(users)} users")
        
        # Create 5 stories
        for i in range(5):
            story_data = {
                "title": f"Story {i+1}",
                "content": f"Content for story {i+1}",
                "difficulty_level": ["beginner", "intermediate", "advanced"][i % 3],
                "sentences": [f"Sentence {j+1} for story {i+1}" for j in range(3)],
                "is_public": True
            }
            story = await content_service.create_story(story_data, users[i % len(users)]['id'])
            stories.append(story)
        
        logger.info(f"Created {len(stories)} stories")
        
        # Generate analytics events
        event_count = 0
        for user in users[:5]:  # Use first 5 users
            for story in stories[:3]:  # Use first 3 stories
                await analytics_service.track_event(
                    user_id=user['id'],
                    event_type="story_view",
                    module_name="asl_world",
                    event_data={"story_id": story['id']}
                )
                event_count += 1
        
        logger.info(f"Generated {event_count} analytics events")
        
        # Test bulk operations
        all_stories = await content_service.get_stories(limit=100)
        logger.info(f"Retrieved {len(all_stories)} stories in bulk")
        
        # Test analytics aggregation
        platform_metrics = await analytics_service.get_platform_metrics()
        logger.info(f"Platform metrics: {platform_metrics['user_metrics']['total_users']} users")
        
        # Shutdown services
        await shutdown_platform_services(container)
        
        logger.info("Service performance test completed successfully!")
        
    except Exception as e:
        logger.error(f"Service performance test failed: {e}")
        raise


async def main():
    """Main test function"""
    logger.info("Starting services integration tests")
    
    try:
        await test_asl_world_integration()
        await test_service_performance()
        logger.info("All integration tests passed successfully!")
        
    except Exception as e:
        logger.error(f"Integration tests failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())