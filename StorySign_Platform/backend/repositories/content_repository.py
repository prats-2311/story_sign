"""
Content repository for StorySign ASL Platform
Provides data access layer for content management with search capabilities
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func, desc, asc, text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from .base_repository import BaseRepository
from ..models.content import (
    Story, StoryTag, StoryVersion, StoryRating, ContentApproval,
    ContentStatus, DifficultyLevel, ContentType
)
from ..models.user import User


class ContentRepository(BaseRepository[Story]):
    """Repository for content management operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(Story, session)
    
    async def create_story(
        self,
        title: str,
        sentences: List[Dict[str, Any]],
        created_by: str,
        description: Optional[str] = None,
        content: Optional[str] = None,
        difficulty_level: str = DifficultyLevel.BEGINNER.value,
        content_type: str = ContentType.STORY.value,
        learning_objectives: Optional[List[str]] = None,
        skill_areas: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        language: str = "en"
    ) -> Story:
        """
        Create a new story with initial version
        
        Args:
            title: Story title
            sentences: List of story sentences
            created_by: ID of user creating the story
            description: Optional story description
            content: Optional full text content
            difficulty_level: Story difficulty level
            content_type: Type of content
            learning_objectives: List of learning objectives
            skill_areas: List of skill areas covered
            metadata: Additional metadata
            language: Content language
            
        Returns:
            Created story instance
        """
        story = Story(
            title=title,
            description=description,
            content=content,
            sentences=sentences,
            difficulty_level=difficulty_level,
            content_type=content_type,
            learning_objectives=learning_objectives or [],
            skill_areas=skill_areas or [],
            created_by=created_by,
            story_metadata=metadata or {},
            language=language,
            status=ContentStatus.DRAFT.value
        )
        
        # Update calculated fields
        story.update_sentence_count()
        story.update_word_count()
        
        self.session.add(story)
        await self.session.flush()  # Get the ID
        
        # Create initial version
        await self.create_version(
            story_id=story.id,
            changed_by=created_by,
            change_type="create",
            change_summary="Initial story creation"
        )
        
        return story
    
    async def update_story(
        self,
        story_id: str,
        updated_by: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[str] = None,
        sentences: Optional[List[Dict[str, Any]]] = None,
        difficulty_level: Optional[str] = None,
        learning_objectives: Optional[List[str]] = None,
        skill_areas: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        change_summary: Optional[str] = None
    ) -> Optional[Story]:
        """
        Update story and create new version
        
        Args:
            story_id: ID of story to update
            updated_by: ID of user making the update
            title: New title
            description: New description
            content: New content
            sentences: New sentences
            difficulty_level: New difficulty level
            learning_objectives: New learning objectives
            skill_areas: New skill areas
            metadata: New metadata
            change_summary: Summary of changes
            
        Returns:
            Updated story instance or None if not found
        """
        story = await self.get_by_id(story_id)
        if not story:
            return None
        
        # Track what changed
        changes = []
        
        if title is not None and title != story.title:
            story.title = title
            changes.append("title")
        
        if description is not None and description != story.description:
            story.description = description
            changes.append("description")
        
        if content is not None and content != story.content:
            story.content = content
            changes.append("content")
        
        if sentences is not None and sentences != story.sentences:
            story.sentences = sentences
            story.update_sentence_count()
            changes.append("sentences")
        
        if difficulty_level is not None and difficulty_level != story.difficulty_level:
            story.difficulty_level = difficulty_level
            changes.append("difficulty")
        
        if learning_objectives is not None:
            story.learning_objectives = learning_objectives
            changes.append("objectives")
        
        if skill_areas is not None:
            story.skill_areas = skill_areas
            changes.append("skills")
        
        if metadata is not None:
            story.story_metadata = {**(story.story_metadata or {}), **metadata}
            changes.append("metadata")
        
        # Update calculated fields
        story.update_word_count()
        
        # Create new version if there were changes
        if changes:
            await self.create_version(
                story_id=story_id,
                changed_by=updated_by,
                change_type="edit",
                change_summary=change_summary or f"Updated: {', '.join(changes)}"
            )
        
        return story
    
    async def create_version(
        self,
        story_id: str,
        changed_by: str,
        change_type: str = "edit",
        change_summary: Optional[str] = None
    ) -> StoryVersion:
        """
        Create a new version of a story
        
        Args:
            story_id: ID of the story
            changed_by: ID of user making the change
            change_type: Type of change
            change_summary: Summary of changes
            
        Returns:
            Created version instance
        """
        story = await self.get_by_id(story_id)
        if not story:
            raise ValueError(f"Story {story_id} not found")
        
        # Get next version number
        result = await self.session.execute(
            text("SELECT COALESCE(MAX(version_number), 0) + 1 FROM story_versions WHERE story_id = :story_id"),
            {"story_id": story_id}
        )
        version_number = result.scalar()
        
        # Mark previous versions as not current
        await self.session.execute(
            text("UPDATE story_versions SET is_current = FALSE WHERE story_id = :story_id"),
            {"story_id": story_id}
        )
        
        # Create new version
        version = StoryVersion(
            story_id=story_id,
            version_number=version_number,
            title=story.title,
            description=story.description,
            content=story.content,
            sentences=story.sentences,
            version_metadata=story.story_metadata,
            change_summary=change_summary,
            changed_by=changed_by,
            change_type=change_type,
            is_current=True
        )
        
        self.session.add(version)
        return version
    
    async def search_stories(
        self,
        query: Optional[str] = None,
        difficulty_levels: Optional[List[str]] = None,
        content_types: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        skill_areas: Optional[List[str]] = None,
        language: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_duration: Optional[int] = None,
        is_public: Optional[bool] = None,
        status: Optional[str] = None,
        created_by: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Story], int]:
        """
        Search stories with advanced filtering
        
        Args:
            query: Text search query
            difficulty_levels: List of difficulty levels to filter by
            content_types: List of content types to filter by
            tags: List of tags to filter by
            skill_areas: List of skill areas to filter by
            language: Language code to filter by
            min_rating: Minimum average rating
            max_duration: Maximum estimated duration
            is_public: Filter by public status
            status: Filter by content status
            created_by: Filter by creator ID
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            Tuple of (stories list, total count)
        """
        # Build base query
        query_stmt = select(Story).options(
            selectinload(Story.tags),
            joinedload(Story.creator)
        )
        
        # Apply filters
        conditions = []
        
        # Text search
        if query:
            search_conditions = or_(
                Story.title.ilike(f"%{query}%"),
                Story.description.ilike(f"%{query}%"),
                Story.content.ilike(f"%{query}%")
            )
            conditions.append(search_conditions)
        
        # Difficulty levels
        if difficulty_levels:
            conditions.append(Story.difficulty_level.in_(difficulty_levels))
        
        # Content types
        if content_types:
            conditions.append(Story.content_type.in_(content_types))
        
        # Language
        if language:
            conditions.append(Story.language == language)
        
        # Rating filter
        if min_rating is not None:
            conditions.append(Story.avg_rating >= min_rating)
        
        # Duration filter
        if max_duration is not None:
            conditions.append(Story.estimated_duration <= max_duration)
        
        # Public status
        if is_public is not None:
            conditions.append(Story.is_public == is_public)
        
        # Content status
        if status:
            conditions.append(Story.status == status)
        
        # Creator filter
        if created_by:
            conditions.append(Story.created_by == created_by)
        
        # Tag filter
        if tags:
            tag_subquery = select(StoryTag.story_id).filter(
                StoryTag.tag_name.in_(tags)
            ).subquery()
            conditions.append(Story.id.in_(select(tag_subquery.c.story_id)))
        
        # Skill areas filter
        if skill_areas:
            skill_conditions = []
            for skill in skill_areas:
                skill_conditions.append(
                    func.json_contains(Story.skill_areas, f'"{skill}"')
                )
            conditions.append(or_(*skill_conditions))
        
        # Apply all conditions
        if conditions:
            query_stmt = query_stmt.where(and_(*conditions))
        
        # Get total count
        count_stmt = select(func.count(Story.id))
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total_count_result = await self.session.execute(count_stmt)
        total_count = total_count_result.scalar()
        
        # Apply sorting
        sort_column = getattr(Story, sort_by, Story.created_at)
        if sort_order.lower() == "desc":
            query_stmt = query_stmt.order_by(desc(sort_column))
        else:
            query_stmt = query_stmt.order_by(asc(sort_column))
        
        # Apply pagination
        query_stmt = query_stmt.offset(offset).limit(limit)
        
        # Execute query
        result = await self.session.execute(query_stmt)
        stories = result.scalars().all()
        
        return stories, total_count
    
    async def get_story_with_details(self, story_id: str) -> Optional[Story]:
        """
        Get story with all related data loaded
        
        Args:
            story_id: ID of the story
            
        Returns:
            Story with related data or None if not found
        """
        result = await self.session.execute(
            select(Story)
            .options(
                selectinload(Story.tags),
                selectinload(Story.versions),
                selectinload(Story.ratings),
                joinedload(Story.creator)
            )
            .where(Story.id == story_id)
        )
        return result.scalar_one_or_none()
    
    async def add_tags(self, story_id: str, tags: List[Dict[str, Any]]) -> List[StoryTag]:
        """
        Add tags to a story
        
        Args:
            story_id: ID of the story
            tags: List of tag dictionaries with name, category, etc.
            
        Returns:
            List of created tag instances
        """
        created_tags = []
        
        for tag_data in tags:
            # Check if tag already exists
            existing_tag = await self.session.execute(
                select(StoryTag).where(
                    and_(
                        StoryTag.story_id == story_id,
                        StoryTag.tag_name == tag_data["name"],
                        StoryTag.tag_category == tag_data.get("category")
                    )
                )
            )
            
            if not existing_tag.scalar_one_or_none():
                tag = StoryTag(
                    story_id=story_id,
                    tag_name=tag_data["name"],
                    tag_category=tag_data.get("category"),
                    tag_value=tag_data.get("value"),
                    is_system_tag=tag_data.get("is_system", False),
                    weight=tag_data.get("weight", 1.0)
                )
                self.session.add(tag)
                created_tags.append(tag)
        
        return created_tags
    
    async def remove_tags(self, story_id: str, tag_names: List[str]) -> int:
        """
        Remove tags from a story
        
        Args:
            story_id: ID of the story
            tag_names: List of tag names to remove
            
        Returns:
            Number of tags removed
        """
        result = await self.session.execute(
            text("""
                DELETE FROM story_tags 
                WHERE story_id = :story_id AND tag_name IN :tag_names
            """),
            {"story_id": story_id, "tag_names": tuple(tag_names)}
        )
        return result.rowcount
    
    async def add_rating(
        self,
        story_id: str,
        user_id: str,
        rating: int,
        review_text: Optional[str] = None,
        difficulty_rating: Optional[int] = None,
        engagement_rating: Optional[int] = None,
        educational_value_rating: Optional[int] = None
    ) -> StoryRating:
        """
        Add or update a story rating
        
        Args:
            story_id: ID of the story
            user_id: ID of the user providing the rating
            rating: Overall rating (1-5)
            review_text: Optional review text
            difficulty_rating: Difficulty rating (1-5)
            engagement_rating: Engagement rating (1-5)
            educational_value_rating: Educational value rating (1-5)
            
        Returns:
            Created or updated rating instance
        """
        # Check for existing rating
        existing_rating = await self.session.execute(
            select(StoryRating).where(
                and_(
                    StoryRating.story_id == story_id,
                    StoryRating.user_id == user_id
                )
            )
        )
        existing_rating = existing_rating.scalar_one_or_none()
        
        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating
            existing_rating.review_text = review_text
            existing_rating.difficulty_rating = difficulty_rating
            existing_rating.engagement_rating = engagement_rating
            existing_rating.educational_value_rating = educational_value_rating
            story_rating = existing_rating
        else:
            # Create new rating
            story_rating = StoryRating(
                story_id=story_id,
                user_id=user_id,
                rating=rating,
                review_text=review_text,
                difficulty_rating=difficulty_rating,
                engagement_rating=engagement_rating,
                educational_value_rating=educational_value_rating
            )
            self.session.add(story_rating)
        
        # Update story average rating
        await self._update_story_rating(story_id)
        
        return story_rating
    
    async def _update_story_rating(self, story_id: str) -> None:
        """Update story average rating and count"""
        result = await self.session.execute(
            text("""
                SELECT AVG(rating), COUNT(*) 
                FROM story_ratings 
                WHERE story_id = :story_id
            """),
            {"story_id": story_id}
        )
        avg_rating, count = result.fetchone()
        
        await self.session.execute(
            text("""
                UPDATE stories 
                SET avg_rating = :avg_rating, rating_count = :count 
                WHERE id = :story_id
            """),
            {
                "avg_rating": float(avg_rating) if avg_rating else 0.0,
                "count": int(count) if count else 0,
                "story_id": story_id
            }
        )
    
    async def publish_story(self, story_id: str) -> Optional[Story]:
        """
        Publish a story (make it public and available)
        
        Args:
            story_id: ID of the story to publish
            
        Returns:
            Published story or None if not found
        """
        story = await self.get_by_id(story_id)
        if not story:
            return None
        
        if story.can_be_published():
            story.publish()
            return story
        else:
            raise ValueError("Story cannot be published in its current state")
    
    async def archive_story(self, story_id: str) -> Optional[Story]:
        """
        Archive a story (remove from public access)
        
        Args:
            story_id: ID of the story to archive
            
        Returns:
            Archived story or None if not found
        """
        story = await self.get_by_id(story_id)
        if not story:
            return None
        
        story.archive()
        return story
    
    async def get_popular_stories(
        self,
        limit: int = 10,
        days: int = 30,
        min_rating: float = 3.0
    ) -> List[Story]:
        """
        Get popular stories based on ratings and activity
        
        Args:
            limit: Maximum number of stories to return
            days: Number of days to look back for activity
            min_rating: Minimum average rating
            
        Returns:
            List of popular stories
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        result = await self.session.execute(
            select(Story)
            .where(
                and_(
                    Story.is_public == True,
                    Story.status == ContentStatus.PUBLISHED.value,
                    Story.avg_rating >= min_rating,
                    Story.created_at >= cutoff_date
                )
            )
            .order_by(
                desc(Story.avg_rating * Story.rating_count + Story.practice_count)
            )
            .limit(limit)
        )
        
        return result.scalars().all()
    
    async def get_featured_stories(self, limit: int = 5) -> List[Story]:
        """
        Get featured stories
        
        Args:
            limit: Maximum number of stories to return
            
        Returns:
            List of featured stories
        """
        result = await self.session.execute(
            select(Story)
            .where(
                and_(
                    Story.is_public == True,
                    Story.is_featured == True,
                    Story.status == ContentStatus.PUBLISHED.value
                )
            )
            .order_by(desc(Story.created_at))
            .limit(limit)
        )
        
        return result.scalars().all()
    
    async def get_story_analytics(self, story_id: str) -> Dict[str, Any]:
        """
        Get analytics data for a story
        
        Args:
            story_id: ID of the story
            
        Returns:
            Analytics data dictionary
        """
        story = await self.get_by_id(story_id)
        if not story:
            return {}
        
        # Get rating distribution
        rating_dist = await self.session.execute(
            text("""
                SELECT rating, COUNT(*) as count
                FROM story_ratings 
                WHERE story_id = :story_id
                GROUP BY rating
                ORDER BY rating
            """),
            {"story_id": story_id}
        )
        rating_distribution = {row.rating: row.count for row in rating_dist.fetchall()}
        
        # Get practice session stats
        practice_stats = await self.session.execute(
            text("""
                SELECT 
                    COUNT(*) as total_sessions,
                    AVG(overall_score) as avg_score,
                    AVG(sentences_completed) as avg_completion
                FROM practice_sessions 
                WHERE story_id = :story_id
            """),
            {"story_id": story_id}
        )
        practice_data = practice_stats.fetchone()
        
        return {
            "story_id": story_id,
            "view_count": story.view_count,
            "practice_count": story.practice_count,
            "avg_rating": story.avg_rating,
            "rating_count": story.rating_count,
            "rating_distribution": rating_distribution,
            "practice_stats": {
                "total_sessions": practice_data.total_sessions if practice_data else 0,
                "avg_score": float(practice_data.avg_score) if practice_data and practice_data.avg_score else 0.0,
                "avg_completion": float(practice_data.avg_completion) if practice_data and practice_data.avg_completion else 0.0
            }
        }


class ContentApprovalRepository(BaseRepository[ContentApproval]):
    """Repository for content approval workflow"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(ContentApproval, session)
    
    async def submit_for_review(self, story_id: str) -> Story:
        """
        Submit story for review
        
        Args:
            story_id: ID of the story to submit
            
        Returns:
            Updated story
        """
        story = await self.session.get(Story, story_id)
        if not story:
            raise ValueError(f"Story {story_id} not found")
        
        story.status = ContentStatus.PENDING_REVIEW.value
        return story
    
    async def create_approval(
        self,
        story_id: str,
        reviewer_id: str,
        status: str,
        review_notes: Optional[str] = None,
        content_quality_score: Optional[int] = None,
        educational_value_score: Optional[int] = None,
        technical_accuracy_score: Optional[int] = None
    ) -> ContentApproval:
        """
        Create content approval record
        
        Args:
            story_id: ID of the story being reviewed
            reviewer_id: ID of the reviewer
            status: Approval status
            review_notes: Review notes
            content_quality_score: Content quality score (1-5)
            educational_value_score: Educational value score (1-5)
            technical_accuracy_score: Technical accuracy score (1-5)
            
        Returns:
            Created approval record
        """
        approval = ContentApproval(
            story_id=story_id,
            reviewer_id=reviewer_id,
            status=status,
            review_notes=review_notes,
            content_quality_score=content_quality_score,
            educational_value_score=educational_value_score,
            technical_accuracy_score=technical_accuracy_score,
            reviewed_at=func.now() if status != "pending" else None
        )
        
        self.session.add(approval)
        
        # Update story status based on approval
        story = await self.session.get(Story, story_id)
        if story:
            if status == "approved":
                story.status = ContentStatus.APPROVED.value
            elif status == "rejected":
                story.status = ContentStatus.REJECTED.value
            elif status == "needs_revision":
                story.status = ContentStatus.DRAFT.value
        
        return approval
    
    async def get_pending_reviews(self, reviewer_id: Optional[str] = None) -> List[Story]:
        """
        Get stories pending review
        
        Args:
            reviewer_id: Optional reviewer ID to filter by
            
        Returns:
            List of stories pending review
        """
        query = select(Story).where(
            Story.status == ContentStatus.PENDING_REVIEW.value
        )
        
        if reviewer_id:
            # Get stories not yet reviewed by this reviewer
            reviewed_stories = select(ContentApproval.story_id).where(
                ContentApproval.reviewer_id == reviewer_id
            ).subquery()
            
            query = query.where(~Story.id.in_(select(reviewed_stories.c.story_id)))
        
        result = await self.session.execute(query)
        return result.scalars().all()