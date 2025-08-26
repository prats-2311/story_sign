"""
Example plugin demonstrating the StorySign plugin architecture.
This plugin enhances the ASL learning experience with additional progress tracking and analytics.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from core.plugin_interface import PluginInterface, PluginContext, HookContext, HookType


class Plugin(PluginInterface):
    """Example plugin implementation"""
    
    def __init__(self, manifest, plugin_id: str):
        super().__init__(manifest, plugin_id)
        self.user_sessions = {}
        self.enhanced_analytics = {}
    
    async def initialize(self, context: PluginContext) -> bool:
        """Initialize the example plugin"""
        try:
            # Register hooks
            self.register_hook(
                "practice_session_start", 
                HookType.AFTER, 
                "asl_world.practice_session.start",
                self._on_practice_session_start,
                priority=100
            )
            
            self.register_hook(
                "story_generation_filter",
                HookType.FILTER,
                "asl_world.story.generate",
                self._filter_story_generation,
                priority=50
            )
            
            # Register UI components
            self.register_ui_component("progress_widget", {
                "component": "EnhancedProgressWidget",
                "props": {
                    "title": "Enhanced Progress Tracking",
                    "plugin_id": self.plugin_id
                }
            })
            
            # Register API endpoints
            self.register_api_endpoint("custom_analytics", {
                "path": "/custom-analytics",
                "method": "GET",
                "handler": self.get_custom_analytics,
                "permissions": ["read:user_data"]
            })
            
            # Initialize plugin data storage
            await self._initialize_storage(context)
            
            return True
            
        except Exception as e:
            print(f"Plugin initialization failed: {e}")
            return False
    
    async def cleanup(self) -> bool:
        """Cleanup plugin resources"""
        try:
            # Save any pending data
            await self._save_analytics_data()
            
            # Clear in-memory data
            self.user_sessions.clear()
            self.enhanced_analytics.clear()
            
            return True
            
        except Exception as e:
            print(f"Plugin cleanup failed: {e}")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get plugin status information"""
        return {
            "initialized": self._is_initialized,
            "active_sessions": len(self.user_sessions),
            "analytics_entries": len(self.enhanced_analytics),
            "hooks_registered": len(self._hooks),
            "ui_components": len(self._ui_components),
            "api_endpoints": len(self._api_endpoints)
        }
    
    async def _initialize_storage(self, context: PluginContext):
        """Initialize plugin storage"""
        # Load existing analytics data
        try:
            stored_data = await context.platform_services.get_user_data(
                context.user_id, f"{self.plugin_id}_analytics"
            )
            if stored_data:
                self.enhanced_analytics = stored_data
        except Exception as e:
            print(f"Failed to load stored analytics: {e}")
    
    async def _on_practice_session_start(self, hook_context: HookContext) -> Any:
        """Handle practice session start event"""
        try:
            user_id = hook_context.plugin_context.user_id
            session_data = hook_context.kwargs.get('session_data', {})
            
            # Track session start
            session_info = {
                'start_time': datetime.utcnow().isoformat(),
                'story_id': session_data.get('story_id'),
                'difficulty': session_data.get('difficulty', 'unknown'),
                'plugin_enhanced': True
            }
            
            self.user_sessions[user_id] = session_info
            
            # Log analytics event
            await hook_context.plugin_context.platform_services.log_event(
                user_id=user_id,
                event_type="enhanced_session_start",
                module_name=f"plugin_{self.plugin_id}",
                event_data=session_info
            )
            
            # Send notification to user
            await hook_context.plugin_context.platform_services.send_notification(
                user_id=user_id,
                message="Enhanced progress tracking is active for this session!",
                type="info"
            )
            
            return hook_context.result
            
        except Exception as e:
            print(f"Practice session start hook failed: {e}")
            return hook_context.result
    
    async def _filter_story_generation(self, hook_context: HookContext) -> Any:
        """Filter story generation to add enhanced features"""
        try:
            story_data = hook_context.result
            
            if story_data and isinstance(story_data, dict):
                # Add plugin enhancements to the story
                story_data['plugin_enhancements'] = {
                    'enhanced_by': self.plugin_id,
                    'enhancement_version': self.manifest.version,
                    'enhanced_at': datetime.utcnow().isoformat(),
                    'features': [
                        'progress_tracking',
                        'advanced_analytics',
                        'personalized_feedback'
                    ]
                }
                
                # Add difficulty adjustment based on user progress
                user_id = hook_context.plugin_context.user_id
                if user_id in self.enhanced_analytics:
                    user_stats = self.enhanced_analytics[user_id]
                    avg_score = user_stats.get('average_score', 0.5)
                    
                    # Adjust difficulty based on performance
                    if avg_score > 0.8:
                        story_data['suggested_difficulty'] = 'harder'
                    elif avg_score < 0.4:
                        story_data['suggested_difficulty'] = 'easier'
                    else:
                        story_data['suggested_difficulty'] = 'current'
            
            return story_data
            
        except Exception as e:
            print(f"Story generation filter failed: {e}")
            return hook_context.result
    
    async def get_custom_analytics(self, user_id: str, date_range: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Custom analytics endpoint"""
        try:
            # Get user analytics from plugin storage
            user_analytics = self.enhanced_analytics.get(user_id, {})
            
            # Calculate enhanced metrics
            enhanced_metrics = {
                'total_enhanced_sessions': user_analytics.get('session_count', 0),
                'average_improvement_rate': user_analytics.get('improvement_rate', 0.0),
                'personalized_recommendations': self._generate_recommendations(user_analytics),
                'plugin_version': self.manifest.version,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            return enhanced_metrics
            
        except Exception as e:
            print(f"Custom analytics failed: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self, user_analytics: Dict[str, Any]) -> List[str]:
        """Generate personalized recommendations based on analytics"""
        recommendations = []
        
        avg_score = user_analytics.get('average_score', 0.5)
        session_count = user_analytics.get('session_count', 0)
        
        if avg_score < 0.5:
            recommendations.append("Focus on basic hand shapes and finger positioning")
            recommendations.append("Practice slower, more deliberate movements")
        elif avg_score > 0.8:
            recommendations.append("Try more complex sentences and stories")
            recommendations.append("Explore advanced ASL grammar concepts")
        
        if session_count < 5:
            recommendations.append("Establish a regular practice routine")
        elif session_count > 20:
            recommendations.append("Consider teaching others to reinforce your learning")
        
        return recommendations
    
    async def _save_analytics_data(self):
        """Save analytics data to persistent storage"""
        try:
            # This would save to the platform's plugin data storage
            # Implementation depends on the platform services API
            pass
        except Exception as e:
            print(f"Failed to save analytics data: {e}")


# Plugin entry point - this is what gets loaded by the plugin system
def create_plugin(manifest, plugin_id: str) -> PluginInterface:
    """Create and return plugin instance"""
    return Plugin(manifest, plugin_id)