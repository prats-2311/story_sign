"""
Enhanced content service for StorySign ASL Platform
Handles business logic for content management, search, and workflow
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import logging

from ..repositories.content_repository import ContentRepository, ContentApprovalRepository
from ..models.content import Story, StoryTag, ContentStatus, DifficultyLevel
from ..core.database_service import DatabaseService

logger = logging.getLogger(__name__)


class EnhancedContentService:
    """Service for content management operations"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    async def create_story(
        self,
        title: str,
        sentences: List[Dict[str, Any]],
        created_by: str,
        description: Optional[str] = None,
        content: Optional[str] = None,
        difficulty_level: str = DifficultyLevel.BEGINNER.value,
        learning_objectives: Optional[List[str]] = None,
        skill_areas: Optional[List[str]] = None,
        tags: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Story:
        """
        Create a new story with tags and metadata
        
        Args:
            title: Story title
            sentences: List of story sentences
            created_by: ID of user creating the story
            description: Optional story description
            content: Optional full text content
            difficulty_level: Story difficulty level
            learning_objectives: List of learning objectives
            skill_areas: List of skill areas covered
            tags: List of tags to add
            metadata: Additional metadata
            
        Returns:
            Created story instance
        """
        async with self.db_service.get_session() as session:
            content_repo = ContentRepository(session)
            
            # Create the story
            story = await content_repo.create_story(
                title=title,
                sentences=sentences,
                created_by=created_by,
                description=description,
                content=content,
                difficulty_level=difficulty_level,
                learning_objectives=learning_objectives,
                skill_areas=skill_areas,
                metadata=metadata
            )
            
            # Add tags if provided
            if tags:
                await content_repo.add_tags(story.id, tags)
            
            await session.commit()
            return story
    
    async def update_story(
        self,
        story_id: str,
        updated_by: str,
        **update_data
    ) -> Optional[Story]:
        """
        Update an existing story
        
        Args:
            story_id: ID of story to update
            updated_by: ID of user making the update
            **update_data: Fields to update
            
        Returns:
            Updated story or None if not found
        """
        async with self.db_service.get_session() as session:
            content_repo = ContentRepository(session)
            
            story = await content_repo.update_story(
                story_id=story_id,
                updated_by=updated_by,
                **update_data
            )
            
            if story:
                await session.commit()
            
            return story
    
    async def search_stories(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Story], int]:
        """
        Search stories with advanced filtering
        
        Args:
            query: Text search query
            filters: Dictionary of filters to apply
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            Tuple of (stories list, total count)
        """
        async with self.db_service.get_session() as session:
            content_repo = ContentRepository(session)
            
            # Extract filters
            filters = filters or {}
            
            return await content_repo.search_stories(
                query=query,
                difficulty_levels=filters.get("difficulty_levels"),
                content_types=filters.get("content_types"),
                tags=filters.get("tags"),
                skill_areas=filters.get("skill_areas"),
                language=filters.get("language"),
                min_rating=filters.get("min_rating"),
                max_duration=filters.get("max_duration"),
                is_public=filters.get("is_public"),
                status=filters.get("status"),
                created_by=filters.get("created_by"),
                sort_by=sort_by,
                sort_order=sort_order,
                limit=limit,
                offset=offset
            )
    
    async def get_story_details(self, story_id: str) -> Optional[Story]:
        """
        Get story with all related details
        
        Args:
            story_id: ID of the story
            
        Returns:
            Story with related data or None if not found
        """
        async with self.db_service.get_session() as session:
            content_repo = ContentRepository(session)
            return await content_repo.get_story_with_details(story_id)
    
    async def add_story_rating(
        self,
        story_id: str,
        user_id: str,
        rating: int,
        review_text: Optional[str] = None,
        **rating_categories
    ) -> bool:
        """
        Add or update a story rating
        
        Args:
            story_id: ID of the story
            user_id: ID of the user providing the rating
            rating: Overall rating (1-5)
            review_text: Optional review text
            **rating_categories: Additional rating categories
            
        Returns:
            True if rating was added successfully
        """
        try:
            async with self.db_service.get_session() as session:
                content_repo = ContentRepository(session)
                
                await content_repo.add_rating(
                    story_id=story_id,
                    user_id=user_id,
                    rating=rating,
                    review_text=review_text,
                    **rating_categories
                )
                
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding story rating: {e}")
            return False
    
    async def publish_story(self, story_id: str, publisher_id: str) -> bool:
        """
        Publish a story
        
        Args:
            story_id: ID of the story to publish
            publisher_id: ID of user publishing the story
            
        Returns:
            True if story was published successfully
        """
        try:
            async with self.db_service.get_session() as session:
                content_repo = ContentRepository(session)
                
                story = await content_repo.publish_story(story_id)
                if story:
                    # Create version record for publication
                    await content_repo.create_version(
                        story_id=story_id,
                        changed_by=publisher_id,
                        change_type="publish",
                        change_summary="Story published"
                    )
                    
                    await session.commit()
                    return True
                
                return False
        except Exception as e:
            logger.error(f"Error publishing story: {e}")
            return False
    
    async def get_popular_stories(self, limit: int = 10) -> List[Story]:
        """
        Get popular stories
        
        Args:
            limit: Maximum number of stories to return
            
        Returns:
            List of popular stories
        """
        async with self.db_service.get_session() as session:
            content_repo = ContentRepository(session)
            return await content_repo.get_popular_stories(limit=limit)
    
    async def get_featured_stories(self, limit: int = 5) -> List[Story]:
        """
        Get featured stories
        
        Args:
            limit: Maximum number of stories to return
            
        Returns:
            List of featured stories
        """
        async with self.db_service.get_session() as session:
            content_repo = ContentRepository(session)
            return await content_repo.get_featured_stories(limit=limit)
    
    async def get_story_analytics(self, story_id: str) -> Dict[str, Any]:
        """
        Get analytics data for a story
        
        Args:
            story_id: ID of the story
            
        Returns:
            Analytics data dictionary
        """
        async with self.db_service.get_session() as session:
            content_repo = ContentRepository(session)
            return await content_repo.get_story_analytics(story_id)
    
    async def manage_story_tags(
        self,
        story_id: str,
        add_tags: Optional[List[Dict[str, Any]]] = None,
        remove_tags: Optional[List[str]] = None
    ) -> bool:
        """
        Add or remove tags from a story
        
        Args:
            story_id: ID of the story
            add_tags: List of tags to add
            remove_tags: List of tag names to remove
            
        Returns:
            True if operation was successful
        """
        try:
            async with self.db_service.get_session() as session:
                content_repo = ContentRepository(session)
                
                if add_tags:
                    await content_repo.add_tags(story_id, add_tags)
                
                if remove_tags:
                    await content_repo.remove_tags(story_id, remove_tags)
                
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error managing story tags: {e}")
            return False


class ContentApprovalService:
    """Service for content approval workflow"""
    
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
    
    async def submit_for_review(self, story_id: str) -> bool:
        """
        Submit story for review
        
        Args:
            story_id: ID of the story to submit
            
        Returns:
            True if submission was successful
        """
        try:
            async with self.db_service.get_session() as session:
                approval_repo = ContentApprovalRepository(session)
                
                await approval_repo.submit_for_review(story_id)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error submitting story for review: {e}")
            return False
    
    async def review_content(
        self,
        story_id: str,
        reviewer_id: str,
        status: str,
        review_notes: Optional[str] = None,
        **scores
    ) -> bool:
        """
        Review and approve/reject content
        
        Args:
            story_id: ID of the story being reviewed
            reviewer_id: ID of the reviewer
            status: Approval status
            review_notes: Review notes
            **scores: Review scores
            
        Returns:
            True if review was successful
        """
        try:
            async with self.db_service.get_session() as session:
                approval_repo = ContentApprovalRepository(session)
                
                await approval_repo.create_approval(
                    story_id=story_id,
                    reviewer_id=reviewer_id,
                    status=status,
                    review_notes=review_notes,
                    **scores
                )
                
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error reviewing content: {e}")
            return False
    
    async def get_pending_reviews(self, reviewer_id: Optional[str] = None) -> List[Story]:
        """
        Get stories pending review
        
        Args:
            reviewer_id: Optional reviewer ID to filter by
            
        Returns:
            List of stories pending review
        """
        async with self.db_service.get_session() as session:
            approval_repo = ContentApprovalRepository(session)
            return await approval_repo.get_pending_reviews(reviewer_id)