"""
Plugin API interface for accessing platform services.
Provides a secure API layer for plugins to interact with platform functionality.
"""

from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
import asyncio
import logging
from datetime import datetime

from models.plugin import PluginPermission
from core.plugin_security import PluginSecurityManager, SecurityViolationError


logger = logging.getLogger(__name__)


class PluginAPIError(Exception):
    """Base exception for plugin API errors"""
    pass


class PermissionDeniedError(PluginAPIError):
    """Raised when plugin lacks required permissions"""
    pass


class PluginAPI:
    """Main API interface for plugins to access platform services"""
    
    def __init__(self, plugin_id: str, permissions: List[PluginPermission], 
                 platform_services, security_manager: PluginSecurityManager):
        self.plugin_id = plugin_id
        self.permissions = permissions
        self.platform_services = platform_services
        self.security_manager = security_manager
        
        # Initialize API modules
        self.user = UserAPI(self)
        self.content = ContentAPI(self)
        self.analytics = AnalyticsAPI(self)
        self.ai = AIAPI(self)
        self.websocket = WebSocketAPI(self)
        self.storage = StorageAPI(self)
        self.notifications = NotificationAPI(self)
    
    def _check_permission(self, required_permission: PluginPermission):
        """Check if plugin has required permission"""
        if required_permission not in self.permissions:
            raise PermissionDeniedError(
                f"Plugin {self.plugin_id} lacks permission: {required_permission}"
            )
    
    async def _execute_with_security(self, func, *args, **kwargs):
        """Execute function with security checks"""
        try:
            sandbox_manager = self.security_manager.create_sandbox_manager(
                self.plugin_id, self.permissions
            )
            return await sandbox_manager.execute_plugin_function(func, *args, **kwargs)
        except Exception as e:
            logger.error(f"Plugin {self.plugin_id} API call failed: {e}")
            raise PluginAPIError(f"API call failed: {str(e)}")


class BasePluginAPI(ABC):
    """Base class for plugin API modules"""
    
    def __init__(self, plugin_api: PluginAPI):
        self.plugin_api = plugin_api
        self.plugin_id = plugin_api.plugin_id
        self.permissions = plugin_api.permissions
        self.platform_services = plugin_api.platform_services
    
    def _check_permission(self, permission: PluginPermission):
        """Check permission wrapper"""
        self.plugin_api._check_permission(permission)


class UserAPI(BasePluginAPI):
    """User-related API for plugins"""
    
    async def get_current_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get current user information"""
        self._check_permission(PluginPermission.READ_USER_DATA)
        
        try:
            user = await self.platform_services.user.get_user_by_id(user_id)
            if user:
                return {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'preferences': user.preferences
                }
            return None
        except Exception as e:
            raise PluginAPIError(f"Failed to get user: {str(e)}")
    
    async def get_user_progress(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user learning progress"""
        self._check_permission(PluginPermission.READ_USER_DATA)
        
        try:
            progress_records = await self.platform_services.progress.get_user_progress(user_id)
            return [
                {
                    'skill_area': p.skill_area,
                    'current_level': p.current_level,
                    'experience_points': p.experience_points,
                    'milestones': p.milestones,
                    'last_updated': p.last_updated.isoformat()
                }
                for p in progress_records
            ]
        except Exception as e:
            raise PluginAPIError(f"Failed to get user progress: {str(e)}")
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        self._check_permission(PluginPermission.WRITE_USER_DATA)
        
        try:
            return await self.platform_services.user.update_user_preferences(user_id, preferences)
        except Exception as e:
            raise PluginAPIError(f"Failed to update user preferences: {str(e)}")


class ContentAPI(BasePluginAPI):
    """Content-related API for plugins"""
    
    async def get_stories(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get stories with optional filters"""
        self._check_permission(PluginPermission.READ_USER_DATA)
        
        try:
            stories = await self.platform_services.content.get_stories(filters or {})
            return [
                {
                    'id': s.id,
                    'title': s.title,
                    'content': s.content,
                    'difficulty_level': s.difficulty_level,
                    'sentences': s.sentences,
                    'metadata': s.metadata,
                    'avg_rating': s.avg_rating,
                    'created_at': s.created_at.isoformat()
                }
                for s in stories
            ]
        except Exception as e:
            raise PluginAPIError(f"Failed to get stories: {str(e)}")
    
    async def create_story(self, story_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new story"""
        self._check_permission(PluginPermission.WRITE_USER_DATA)
        
        try:
            story = await self.platform_services.content.create_story(story_data)
            return {
                'id': story.id,
                'title': story.title,
                'content': story.content,
                'difficulty_level': story.difficulty_level,
                'created_at': story.created_at.isoformat()
            }
        except Exception as e:
            raise PluginAPIError(f"Failed to create story: {str(e)}")
    
    async def search_content(self, query: str, content_type: str = "story") -> List[Dict[str, Any]]:
        """Search content"""
        self._check_permission(PluginPermission.READ_USER_DATA)
        
        try:
            results = await self.platform_services.content.search_content(query, content_type)
            return results
        except Exception as e:
            raise PluginAPIError(f"Failed to search content: {str(e)}")


class AnalyticsAPI(BasePluginAPI):
    """Analytics-related API for plugins"""
    
    async def log_event(self, event_type: str, event_data: Dict[str, Any], 
                       user_id: Optional[str] = None) -> bool:
        """Log an analytics event"""
        # No specific permission required for logging events
        
        try:
            return await self.platform_services.analytics.log_event(
                user_id=user_id,
                event_type=event_type,
                module_name=f"plugin_{self.plugin_id}",
                event_data=event_data
            )
        except Exception as e:
            raise PluginAPIError(f"Failed to log event: {str(e)}")
    
    async def get_user_analytics(self, user_id: str, 
                                date_range: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get user analytics data"""
        self._check_permission(PluginPermission.READ_USER_DATA)
        
        try:
            analytics = await self.platform_services.analytics.get_user_analytics(
                user_id, date_range
            )
            return analytics
        except Exception as e:
            raise PluginAPIError(f"Failed to get user analytics: {str(e)}")


class AIAPI(BasePluginAPI):
    """AI services API for plugins"""
    
    async def generate_text(self, prompt: str, model: str = "default") -> str:
        """Generate text using AI service"""
        self._check_permission(PluginPermission.ACCESS_AI_SERVICES)
        
        try:
            result = await self.platform_services.ai.generate_text(prompt, model)
            return result
        except Exception as e:
            raise PluginAPIError(f"Failed to generate text: {str(e)}")
    
    async def analyze_gesture(self, landmark_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze gesture data"""
        self._check_permission(PluginPermission.ACCESS_AI_SERVICES)
        
        try:
            analysis = await self.platform_services.ai.analyze_gesture(landmark_data)
            return analysis
        except Exception as e:
            raise PluginAPIError(f"Failed to analyze gesture: {str(e)}")
    
    async def process_video_frame(self, frame_data: bytes) -> Dict[str, Any]:
        """Process video frame"""
        self._check_permission(PluginPermission.ACCESS_VIDEO_STREAM)
        
        try:
            result = await self.platform_services.ai.process_video_frame(frame_data)
            return result
        except Exception as e:
            raise PluginAPIError(f"Failed to process video frame: {str(e)}")


class WebSocketAPI(BasePluginAPI):
    """WebSocket communication API for plugins"""
    
    async def send_message(self, user_id: str, message: Dict[str, Any]) -> bool:
        """Send WebSocket message to user"""
        self._check_permission(PluginPermission.MODIFY_UI)
        
        try:
            return await self.platform_services.websocket.send_user_message(
                user_id, {
                    'type': 'plugin_message',
                    'plugin_id': self.plugin_id,
                    'data': message,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            raise PluginAPIError(f"Failed to send WebSocket message: {str(e)}")
    
    async def broadcast_message(self, message: Dict[str, Any], 
                               channel: str = "general") -> bool:
        """Broadcast message to all connected users"""
        self._check_permission(PluginPermission.MODIFY_UI)
        
        try:
            return await self.platform_services.websocket.broadcast_message(
                channel, {
                    'type': 'plugin_broadcast',
                    'plugin_id': self.plugin_id,
                    'data': message,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            raise PluginAPIError(f"Failed to broadcast message: {str(e)}")


class StorageAPI(BasePluginAPI):
    """Storage API for plugins"""
    
    async def get_data(self, key: str, user_id: Optional[str] = None) -> Any:
        """Get plugin data"""
        self._check_permission(PluginPermission.READ_USER_DATA)
        
        try:
            return await self.platform_services.database.get_plugin_data(
                self.plugin_id, user_id, key
            )
        except Exception as e:
            raise PluginAPIError(f"Failed to get data: {str(e)}")
    
    async def set_data(self, key: str, value: Any, user_id: Optional[str] = None) -> bool:
        """Set plugin data"""
        self._check_permission(PluginPermission.WRITE_USER_DATA)
        
        try:
            return await self.platform_services.database.set_plugin_data(
                self.plugin_id, user_id, key, value
            )
        except Exception as e:
            raise PluginAPIError(f"Failed to set data: {str(e)}")
    
    async def delete_data(self, key: str, user_id: Optional[str] = None) -> bool:
        """Delete plugin data"""
        self._check_permission(PluginPermission.WRITE_USER_DATA)
        
        try:
            return await self.platform_services.database.delete_plugin_data(
                self.plugin_id, user_id, key
            )
        except Exception as e:
            raise PluginAPIError(f"Failed to delete data: {str(e)}")


class NotificationAPI(BasePluginAPI):
    """Notification API for plugins"""
    
    async def send_notification(self, user_id: str, title: str, message: str,
                               notification_type: str = "info") -> bool:
        """Send notification to user"""
        self._check_permission(PluginPermission.MODIFY_UI)
        
        try:
            return await self.platform_services.notifications.send_notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                source=f"plugin_{self.plugin_id}"
            )
        except Exception as e:
            raise PluginAPIError(f"Failed to send notification: {str(e)}")
    
    async def create_toast(self, user_id: str, message: str, 
                          toast_type: str = "info", duration: int = 5000) -> bool:
        """Create toast notification"""
        self._check_permission(PluginPermission.MODIFY_UI)
        
        try:
            return await self.platform_services.websocket.send_user_message(
                user_id, {
                    'type': 'toast_notification',
                    'plugin_id': self.plugin_id,
                    'message': message,
                    'toast_type': toast_type,
                    'duration': duration,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            raise PluginAPIError(f"Failed to create toast: {str(e)}")


class PluginAPIFactory:
    """Factory for creating plugin API instances"""
    
    def __init__(self, platform_services, security_manager: PluginSecurityManager):
        self.platform_services = platform_services
        self.security_manager = security_manager
    
    def create_api(self, plugin_id: str, permissions: List[PluginPermission]) -> PluginAPI:
        """Create a plugin API instance"""
        return PluginAPI(
            plugin_id=plugin_id,
            permissions=permissions,
            platform_services=self.platform_services,
            security_manager=self.security_manager
        )