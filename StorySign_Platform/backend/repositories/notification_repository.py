"""
Repository layer for notification and messaging management
Handles database operations for notifications, messages, and preferences
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from .base_repository import BaseRepository
from models.notifications import (
    Notification, GroupMessage, NotificationPreference,
    NotificationType, NotificationPriority, MessageType
)


class NotificationRepository(BaseRepository):
    """Repository for notification operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Notification)
    
    async def create_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        notification_type: str,
        priority: str = NotificationPriority.NORMAL.value,
        **kwargs
    ) -> Notification:
        """Create a new notification"""
        notification_data = {
            "user_id": user_id,
            "title": title,
            "message": message,
            "notification_type": notification_type,
            "priority": priority,
            **kwargs
        }
        
        notification = Notification(**notification_data)
        self.session.add(notification)
        await self.session.flush()
        return notification
    
    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """Get notifications for a user"""
        query = select(Notification).where(Notification.user_id == user_id)
        
        if unread_only:
            query = query.where(Notification.is_read == False)
        
        # Filter out expired notifications
        query = query.where(
            or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.utcnow()
            )
        )
        
        query = query.order_by(Notification.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_pending_notifications(self) -> List[Notification]:
        """Get notifications that should be delivered now"""
        query = select(Notification).where(
            and_(
                or_(
                    Notification.scheduled_for.is_(None),
                    Notification.scheduled_for <= datetime.utcnow()
                ),
                or_(
                    Notification.expires_at.is_(None),
                    Notification.expires_at > datetime.utcnow()
                ),
                Notification.is_dismissed == False
            )
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def mark_as_read(self, notification_id: str) -> Optional[Notification]:
        """Mark a notification as read"""
        notification = await self.get_by_id(notification_id)
        if notification:
            notification.mark_as_read()
            await self.session.flush()
        return notification
    
    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user"""
        result = await self.session.execute(
            update(Notification)
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False
                )
            )
            .values(
                is_read=True,
                read_at=datetime.utcnow()
            )
        )
        
        return result.rowcount
    
    async def dismiss_notification(self, notification_id: str) -> Optional[Notification]:
        """Dismiss a notification"""
        notification = await self.get_by_id(notification_id)
        if notification:
            notification.dismiss()
            await self.session.flush()
        return notification
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user"""
        result = await self.session.execute(
            select(func.count(Notification.id))
            .where(
                and_(
                    Notification.user_id == user_id,
                    Notification.is_read == False,
                    Notification.is_dismissed == False,
                    or_(
                        Notification.expires_at.is_(None),
                        Notification.expires_at > datetime.utcnow()
                    )
                )
            )
        )
        
        return result.scalar() or 0
    
    async def cleanup_expired_notifications(self) -> int:
        """Remove expired notifications"""
        result = await self.session.execute(
            delete(Notification)
            .where(
                and_(
                    Notification.expires_at < datetime.utcnow(),
                    Notification.is_dismissed == True
                )
            )
        )
        
        return result.rowcount
    
    async def create_bulk_notifications(
        self,
        user_ids: List[str],
        title: str,
        message: str,
        notification_type: str,
        **kwargs
    ) -> List[Notification]:
        """Create notifications for multiple users"""
        notifications = []
        
        for user_id in user_ids:
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                **kwargs
            )
            notifications.append(notification)
            self.session.add(notification)
        
        await self.session.flush()
        return notifications


class GroupMessageRepository(BaseRepository):
    """Repository for group message operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, GroupMessage)
    
    async def create_message(
        self,
        group_id: str,
        sender_id: str,
        content: str,
        message_type: str = MessageType.GROUP_MESSAGE.value,
        **kwargs
    ) -> GroupMessage:
        """Create a new group message"""
        message_data = {
            "group_id": group_id,
            "sender_id": sender_id,
            "content": content,
            "message_type": message_type,
            **kwargs
        }
        
        message = GroupMessage(**message_data)
        self.session.add(message)
        await self.session.flush()
        return message
    
    async def get_group_messages(
        self,
        group_id: str,
        include_deleted: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[GroupMessage]:
        """Get messages for a group"""
        query = select(GroupMessage).where(GroupMessage.group_id == group_id)
        
        if not include_deleted:
            query = query.where(GroupMessage.is_deleted == False)
        
        query = query.order_by(GroupMessage.created_at.desc())
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_pinned_messages(self, group_id: str) -> List[GroupMessage]:
        """Get pinned messages for a group"""
        query = select(GroupMessage).where(
            and_(
                GroupMessage.group_id == group_id,
                GroupMessage.is_pinned == True,
                GroupMessage.is_deleted == False
            )
        ).order_by(GroupMessage.created_at.desc())
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_announcements(
        self,
        group_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[GroupMessage]:
        """Get announcements for a group"""
        query = select(GroupMessage).where(
            and_(
                GroupMessage.group_id == group_id,
                GroupMessage.is_announcement == True,
                GroupMessage.is_deleted == False
            )
        ).order_by(GroupMessage.created_at.desc())
        
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_message_thread(
        self,
        parent_message_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[GroupMessage]:
        """Get replies to a message"""
        query = select(GroupMessage).where(
            and_(
                GroupMessage.parent_message_id == parent_message_id,
                GroupMessage.is_deleted == False
            )
        ).order_by(GroupMessage.created_at.asc())
        
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def pin_message(self, message_id: str) -> Optional[GroupMessage]:
        """Pin a message"""
        message = await self.get_by_id(message_id)
        if message:
            message.is_pinned = True
            await self.session.flush()
        return message
    
    async def unpin_message(self, message_id: str) -> Optional[GroupMessage]:
        """Unpin a message"""
        message = await self.get_by_id(message_id)
        if message:
            message.is_pinned = False
            await self.session.flush()
        return message
    
    async def edit_message(
        self,
        message_id: str,
        new_content: str
    ) -> Optional[GroupMessage]:
        """Edit a message"""
        message = await self.get_by_id(message_id)
        if message:
            message.content = new_content
            message.is_edited = True
            message.edited_at = datetime.utcnow()
            await self.session.flush()
        return message
    
    async def delete_message(self, message_id: str) -> Optional[GroupMessage]:
        """Soft delete a message"""
        message = await self.get_by_id(message_id)
        if message:
            message.is_deleted = True
            message.deleted_at = datetime.utcnow()
            await self.session.flush()
        return message
    
    async def add_reaction(
        self,
        message_id: str,
        user_id: str,
        emoji: str
    ) -> Optional[GroupMessage]:
        """Add a reaction to a message"""
        message = await self.get_by_id(message_id)
        if message:
            message.add_reaction(user_id, emoji)
            await self.session.flush()
        return message
    
    async def remove_reaction(
        self,
        message_id: str,
        user_id: str,
        emoji: str
    ) -> Optional[GroupMessage]:
        """Remove a reaction from a message"""
        message = await self.get_by_id(message_id)
        if message:
            message.remove_reaction(user_id, emoji)
            await self.session.flush()
        return message
    
    async def increment_thread_count(self, parent_message_id: str) -> None:
        """Increment thread count for a parent message"""
        await self.session.execute(
            update(GroupMessage)
            .where(GroupMessage.id == parent_message_id)
            .values(thread_count=GroupMessage.thread_count + 1)
        )


class NotificationPreferenceRepository(BaseRepository):
    """Repository for notification preference operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, NotificationPreference)
    
    async def get_user_preferences(self, user_id: str) -> Optional[NotificationPreference]:
        """Get notification preferences for a user"""
        query = select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
        
        result = await self.session.execute(query)
        return result.scalars().first()
    
    async def create_default_preferences(self, user_id: str) -> NotificationPreference:
        """Create default notification preferences for a user"""
        preferences = NotificationPreference(user_id=user_id)
        self.session.add(preferences)
        await self.session.flush()
        return preferences
    
    async def update_preferences(
        self,
        user_id: str,
        preferences_data: Dict[str, Any]
    ) -> Optional[NotificationPreference]:
        """Update notification preferences for a user"""
        preferences = await self.get_user_preferences(user_id)
        
        if not preferences:
            preferences = await self.create_default_preferences(user_id)
        
        # Update preferences
        for key, value in preferences_data.items():
            if hasattr(preferences, key):
                setattr(preferences, key, value)
        
        await self.session.flush()
        return preferences
    
    async def should_send_notification(
        self,
        user_id: str,
        notification_type: str,
        priority: str,
        group_id: str = None
    ) -> bool:
        """Check if a notification should be sent to a user"""
        preferences = await self.get_user_preferences(user_id)
        
        if not preferences:
            # Default to sending notifications if no preferences set
            return True
        
        return preferences.should_receive_notification(
            notification_type, priority, group_id
        )
    
    async def get_users_for_notification(
        self,
        user_ids: List[str],
        notification_type: str,
        priority: str,
        group_id: str = None
    ) -> List[str]:
        """Filter user IDs based on notification preferences"""
        filtered_users = []
        
        for user_id in user_ids:
            should_send = await self.should_send_notification(
                user_id, notification_type, priority, group_id
            )
            if should_send:
                filtered_users.append(user_id)
        
        return filtered_users