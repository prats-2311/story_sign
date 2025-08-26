"""
Plugin repository for database operations.
Handles CRUD operations for plugin data.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from repositories.base_repository import BaseRepository
from models.plugin import Plugin, PluginData, PluginStatus


class PluginRepository(BaseRepository[Plugin]):
    """Repository for plugin database operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Plugin)
    
    async def get_by_name(self, name: str) -> Optional[Plugin]:
        """Get plugin by name"""
        stmt = select(Plugin).where(Plugin.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_active_plugins(self) -> List[Plugin]:
        """Get all active plugins"""
        stmt = select(Plugin).where(Plugin.status == PluginStatus.ACTIVE)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_status(self, status: PluginStatus) -> List[Plugin]:
        """Get plugins by status"""
        stmt = select(Plugin).where(Plugin.status == status)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_plugin_status(self, plugin_id: str, status: PluginStatus, 
                                  error_message: Optional[str] = None) -> bool:
        """Update plugin status"""
        update_data = {
            'status': status,
            'updated_at': datetime.utcnow()
        }
        
        if error_message is not None:
            update_data['error_message'] = error_message
        
        stmt = update(Plugin).where(Plugin.id == plugin_id).values(**update_data)
        result = await self.session.execute(stmt)
        return result.rowcount > 0
    
    async def get_plugins_by_user(self, user_id: str) -> List[Plugin]:
        """Get plugins installed by a specific user"""
        stmt = select(Plugin).where(Plugin.installed_by == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()


class PluginDataRepository(BaseRepository[PluginData]):
    """Repository for plugin data operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, PluginData)
    
    async def get_plugin_data(self, plugin_id: str, user_id: Optional[str] = None, 
                             data_key: Optional[str] = None) -> List[PluginData]:
        """Get plugin data with optional filters"""
        stmt = select(PluginData).where(PluginData.plugin_id == plugin_id)
        
        if user_id is not None:
            stmt = stmt.where(PluginData.user_id == user_id)
        
        if data_key is not None:
            stmt = stmt.where(PluginData.data_key == data_key)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def set_plugin_data(self, plugin_id: str, data_key: str, data_value: Any,
                             user_id: Optional[str] = None) -> PluginData:
        """Set plugin data (create or update)"""
        # Check if data already exists
        existing_stmt = select(PluginData).where(
            PluginData.plugin_id == plugin_id,
            PluginData.data_key == data_key,
            PluginData.user_id == user_id
        )
        result = await self.session.execute(existing_stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing data
            existing.data_value = data_value
            existing.updated_at = datetime.utcnow()
            await self.session.flush()
            return existing
        else:
            # Create new data
            plugin_data = PluginData(
                plugin_id=plugin_id,
                user_id=user_id,
                data_key=data_key,
                data_value=data_value
            )
            return await self.create(plugin_data)
    
    async def delete_plugin_data(self, plugin_id: str, user_id: Optional[str] = None,
                                data_key: Optional[str] = None) -> int:
        """Delete plugin data with optional filters"""
        stmt = delete(PluginData).where(PluginData.plugin_id == plugin_id)
        
        if user_id is not None:
            stmt = stmt.where(PluginData.user_id == user_id)
        
        if data_key is not None:
            stmt = stmt.where(PluginData.data_key == data_key)
        
        result = await self.session.execute(stmt)
        return result.rowcount
    
    async def get_user_data(self, user_id: str, plugin_id: Optional[str] = None) -> List[PluginData]:
        """Get all data for a specific user"""
        stmt = select(PluginData).where(PluginData.user_id == user_id)
        
        if plugin_id is not None:
            stmt = stmt.where(PluginData.plugin_id == plugin_id)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()