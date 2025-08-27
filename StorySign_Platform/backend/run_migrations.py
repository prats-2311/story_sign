#!/usr/bin/env python3
"""
TiDB Migration Runner
Runs all database migrations in the correct order to set up the StorySign database schema
"""

import asyncio
import logging
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from migrations.create_user_tables import create_user_tables, verify_user_tables
from migrations.create_progress_tables import create_progress_tables, verify_tables as verify_progress_tables
from migrations.create_content_tables import create_content_tables
from migrations.create_collaborative_tables import create_collaborative_tables  
from migrations.create_plugin_tables import create_plugin_tables

logger = logging.getLogger(__name__)


async def run_all_migrations():
    """Run all database migrations in the correct order"""
    
    migrations = [
        ("User Management", create_user_tables, verify_user_tables),
        ("Progress Tracking", create_progress_tables, verify_progress_tables),
        ("Content Management", create_content_tables, None),
        ("Collaborative Features", create_collaborative_tables, None),
        ("Plugin System", create_plugin_tables, None),
    ]
    
    logger.info("🚀 Starting TiDB database migration process...")
    logger.info("=" * 60)
    
    success_count = 0
    total_count = len(migrations)
    
    for i, (name, create_func, verify_func) in enumerate(migrations, 1):
        try:
            logger.info(f"\n{i}/{total_count}. Creating {name} tables...")
            
            # Run the migration
            await create_func()
            
            # Verify if verification function exists
            if verify_func:
                logger.info(f"   Verifying {name} tables...")
                verification_success = await verify_func()
                if verification_success:
                    logger.info(f"   ✅ {name} migration completed and verified")
                    success_count += 1
                else:
                    logger.error(f"   ❌ {name} migration verification failed")
            else:
                logger.info(f"   ✅ {name} migration completed (no verification available)")
                success_count += 1
                
        except Exception as e:
            logger.error(f"   ❌ {name} migration failed: {e}")
            
            # Ask user if they want to continue
            if i < total_count:
                continue_migration = input(f"\nMigration {i} failed. Continue with remaining migrations? (y/N): ")
                if not continue_migration.lower().startswith('y'):
                    logger.info("Migration process stopped by user")
                    break
    
    logger.info("\n" + "=" * 60)
    logger.info(f"🎯 Migration Summary: {success_count}/{total_count} migrations completed successfully")
    
    if success_count == total_count:
        logger.info("🎉 All migrations completed successfully! Your TiDB database is ready.")
        return True
    else:
        logger.warning(f"⚠️  {total_count - success_count} migrations failed. Please check the logs above.")
        return False


async def test_database_connection():
    """Test the database connection before running migrations"""
    
    try:
        from config import get_config
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        
        logger.info("🔍 Testing database connection...")
        
        # Get database configuration
        config = get_config()
        db_config = config.database
        
        # Create async engine with proper SSL configuration
        engine = create_async_engine(
            db_config.get_connection_url(async_driver=True),
            echo=False,
            connect_args=db_config.get_connect_args()
        )
        
        # Test connection
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test, VERSION() as version"))
            row = result.fetchone()
            
            if row:
                logger.info(f"✅ Database connection successful!")
                logger.info(f"   Database version: {row.version}")
                logger.info(f"   Host: {db_config.host}:{db_config.port}")
                logger.info(f"   Database: {db_config.database}")
                return True
            else:
                logger.error("❌ Database connection test failed")
                return False
        
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.error("   Please check your database configuration in config.yaml")
        return False


async def main():
    """Main function"""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🗄️  StorySign TiDB Migration Runner")
    print("=" * 60)
    print("This script will create all necessary database tables for StorySign")
    print("Make sure your TiDB connection details are correct in config.yaml")
    print()
    
    # Test database connection first
    connection_ok = await test_database_connection()
    
    if not connection_ok:
        print("\n❌ Database connection failed. Please check your configuration and try again.")
        return 1
    
    # Ask user confirmation
    proceed = input("\nProceed with database migration? (y/N): ")
    if not proceed.lower().startswith('y'):
        print("Migration cancelled by user.")
        return 0
    
    # Run migrations
    success = await run_all_migrations()
    
    if success:
        print("\n🎉 Database setup complete! You can now run your StorySign application.")
        return 0
    else:
        print("\n❌ Some migrations failed. Please check the logs and fix any issues.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)