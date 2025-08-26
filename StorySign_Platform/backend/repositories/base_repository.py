"""
Base repository class for common database operations
"""

from abc import ABC
from typing import TypeVar, Generic, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import DeclarativeBase

from models.base import BaseModel

T = TypeVar('T', bound=BaseModel)


class BaseRepository(Generic[T], ABC):
    """
    Base repository class with common CRUD operations
    """
    
    def __init__(self, model_class: type[T], session: AsyncSession):
        self.model_class = model_class
        self.session = session
    
    async def create(self, obj: T) -> T:
        """
        Create a new record
        
        Args:
            obj: Model instance to create
            
        Returns:
            Created model instance
        """
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """
        Get record by ID
        
        Args:
            id: Record ID
            
        Returns:
            Model instance or None if not found
        """
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Get all records with pagination
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of model instances
        """
        stmt = select(self.model_class).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_by_id(self, id: str, update_data: Dict[str, Any]) -> Optional[T]:
        """
        Update record by ID
        
        Args:
            id: Record ID
            update_data: Data to update
            
        Returns:
            Updated model instance or None if not found
        """
        stmt = (
            update(self.model_class)
            .where(self.model_class.id == id)
            .values(**update_data)
            .returning(self.model_class.id)
        )
        result = await self.session.execute(stmt)
        
        if result.rowcount == 0:
            return None
            
        await self.session.commit()
        return await self.get_by_id(id)
    
    async def delete_by_id(self, id: str) -> bool:
        """
        Delete record by ID
        
        Args:
            id: Record ID
            
        Returns:
            True if record was deleted, False if not found
        """
        stmt = delete(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0
    
    async def count(self) -> int:
        """
        Count total records
        
        Returns:
            Total number of records
        """
        stmt = select(self.model_class)
        result = await self.session.execute(stmt)
        return len(result.scalars().all())
    
    async def exists(self, id: str) -> bool:
        """
        Check if record exists by ID
        
        Args:
            id: Record ID
            
        Returns:
            True if record exists, False otherwise
        """
        obj = await self.get_by_id(id)
        return obj is not None