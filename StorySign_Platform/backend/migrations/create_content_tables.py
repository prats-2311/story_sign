"""
Database migration to create content management tables
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from models.base import Base
from models.content import (
    Story, StoryTag, StoryVersion, StoryRating, ContentApproval
)
from models.user import User
from models.progress import PracticeSession, SentenceAttempt, UserProgress
from config import get_config


async def create_content_tables():
    """Create content management tables"""
    print("Creating content management tables...")
    
    # Get database configuration
    config = get_config()
    db_config = config.database
    
    # Create async engine
    connection_url = db_config.get_connection_url(async_driver=True)
    engine = create_async_engine(connection_url, echo=True)
    
    try:
        # Create all tables
        async with engine.begin() as conn:
            # Create tables in dependency order
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Content management tables created successfully!")
        
        # Print created tables
        print("\nCreated tables:")
        print("  • stories - Main story content")
        print("  • story_tags - Content tagging system")
        print("  • story_versions - Version control")
        print("  • story_ratings - User ratings and reviews")
        print("  • content_approvals - Approval workflow")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise
    finally:
        await engine.dispose()


async def verify_tables():
    """Verify that tables were created correctly"""
    print("\nVerifying table structure...")
    
    config = get_config()
    db_config = config.database
    connection_url = db_config.get_connection_url(async_driver=True)
    engine = create_async_engine(connection_url, echo=False)
    
    try:
        async with engine.begin() as conn:
            # Check if tables exist
            tables_to_check = [
                'stories', 'story_tags', 'story_versions', 
                'story_ratings', 'content_approvals'
            ]
            
            for table_name in tables_to_check:
                result = await conn.execute(
                    f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
                )
                if result.fetchone():
                    print(f"  ✓ {table_name} table exists")
                else:
                    print(f"  ❌ {table_name} table missing")
        
        print("✅ Table verification complete!")
        
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        raise
    finally:
        await engine.dispose()


def run_migration():
    """Run the content management migration"""
    print("Content Management Schema Migration")
    print("=" * 40)
    
    try:
        # Run async migration
        asyncio.run(create_content_tables())
        asyncio.run(verify_tables())
        
        print("\n🎉 Content management migration completed successfully!")
        print("\nNext steps:")
        print("  1. Update your application to use the new content models")
        print("  2. Test content creation and management features")
        print("  3. Set up content approval workflows")
        print("  4. Configure search and filtering capabilities")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_migration()
    
    if not success:
        exit(1)
    
    print("\n✅ Content management schema is ready!")
    print("\nFeatures available:")
    print("  • Story creation with metadata")
    print("  • Content tagging and categorization")
    print("  • Version control and change tracking")
    print("  • User ratings and reviews")
    print("  • Content approval workflow")
    print("  • Advanced search capabilities")
    print("  • Repository pattern for data access")
    print("  • Service layer for business logic")
    print("  • REST API endpoints")