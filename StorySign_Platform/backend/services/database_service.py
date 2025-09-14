"""
Database Service Layer for TiDB Integration
Ensures all database operations go through backend APIs only
"""

import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.sql import func
from config import get_config

logger = logging.getLogger(__name__)

# Database models
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(String(50), default="learner")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PracticeSession(Base):
    __tablename__ = "practice_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    module_type = Column(String(50), nullable=False)  # asl_world, harmony, reconnect
    session_data = Column(Text)  # JSON data
    score = Column(Integer)
    duration_seconds = Column(Integer)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Story(Base):
    __tablename__ = "stories"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    difficulty_level = Column(String(20), default="beginner")
    category = Column(String(100))
    created_by = Column(Integer, ForeignKey("users.id"))
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DatabaseService:
    """Database service for TiDB operations"""
    
    def __init__(self):
        self.config = get_config()
        self.engine = None
        self.session_factory = None
        
    async def initialize(self):
        """Initialize database connection"""
        try:
            # Create async engine for TiDB
            connection_url = self.config.database.get_connection_url(async_driver=True)
            connect_args = self.config.database.get_connect_args()
            
            self.engine = create_async_engine(
                connection_url,
                connect_args=connect_args,
                pool_size=self.config.database.pool_size,
                max_overflow=self.config.database.max_overflow,
                pool_timeout=self.config.database.pool_timeout,
                pool_recycle=self.config.database.pool_recycle,
                echo=self.config.database.echo_queries
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                
            logger.info("Database service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise
    
    async def get_session(self) -> AsyncSession:
        """Get database session"""
        if not self.session_factory:
            await self.initialize()
        return self.session_factory()
    
    async def health_check(self) -> bool:
        """Check database health"""
        try:
            async with self.get_session() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")

# Global database service instance
db_service = DatabaseService()

async def get_database_service() -> DatabaseService:
    """Get database service instance"""
    if not db_service.engine:
        await db_service.initialize()
    return db_service