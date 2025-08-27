#!/usr/bin/env python3
"""
Debug TiDB Connection Script
Tests the TiDB connection with the exact credentials from the screenshot
"""

import asyncio
import logging
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)


async def debug_tidb_connection():
    """Debug TiDB connection with exact credentials from screenshot"""
    
    # Connection details from the screenshot
    host = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
    port = 4000
    database = "test"  # Database name from screenshot
    username = "28XbMEz3PD5h7d6.root"  # Username from connection string
    password = "ek1FdpnVe3LDPcns"  # Password provided
    
    print("🔍 TiDB Connection Debug")
    print("=" * 50)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Database: {database}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print()
    
    # Test different connection methods
    connection_methods = [
        ("asyncmy (recommended)", f"mysql+asyncmy://{username}:{password}@{host}:{port}/{database}?ssl=true"),
        ("pymysql", f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}?ssl=true"),
        ("mysqldb (from screenshot)", f"mysql+mysqldb://{username}:{password}@{host}:{port}/{database}?ssl_mode=VERIFY_IDENTITY")
    ]
    
    for method_name, connection_url in connection_methods:
        print(f"🧪 Testing {method_name}...")
        
        try:
            # Create engine
            engine = create_async_engine(
                connection_url,
                echo=False,
                pool_size=1,
                max_overflow=0,
                pool_timeout=10,
                connect_args={
                    "charset": "utf8mb4",
                    "autocommit": False,
                }
            )
            
            # Test connection
            async with engine.begin() as conn:
                # Basic test query
                result = await conn.execute(text("SELECT 1 as test, VERSION() as version, NOW() as current_time"))
                row = result.fetchone()
                
                if row:
                    print(f"   ✅ {method_name} connection successful!")
                    print(f"   📊 Database version: {row.version}")
                    print(f"   🕒 Current time: {row.current_time}")
                    
                    # Test database info
                    db_result = await conn.execute(text("SELECT DATABASE() as current_db"))
                    db_row = db_result.fetchone()
                    print(f"   🗄️  Current database: {db_row.current_db}")
                    
                    # List existing tables
                    tables_result = await conn.execute(text("""
                        SELECT table_name, table_type 
                        FROM information_schema.tables 
                        WHERE table_schema = :database_name
                        ORDER BY table_name
                    """), {"database_name": database})
                    
                    existing_tables = tables_result.fetchall()
                    print(f"   📋 Existing tables ({len(existing_tables)}):")
                    for table in existing_tables[:5]:  # Show first 5 tables
                        print(f"      - {table.table_name} ({table.table_type})")
                    if len(existing_tables) > 5:
                        print(f"      ... and {len(existing_tables) - 5} more")
                    
                    print(f"   🎉 {method_name} test completed successfully!")
                    
                else:
                    print(f"   ❌ {method_name} test failed - no result returned")
            
            await engine.dispose()
            print()
            
        except Exception as e:
            print(f"   ❌ {method_name} failed: {e}")
            print()
    
    # Test with config loading
    print("🔧 Testing with config.py...")
    try:
        from config import get_config
        
        config = get_config()
        db_config = config.database
        
        print(f"   Config loaded - Database: {db_config.database}")
        print(f"   Config loaded - Username: {db_config.username}")
        
        # Test config-based connection
        engine = create_async_engine(
            db_config.get_connection_url(async_driver=True),
            echo=False,
            connect_args=db_config.get_connect_args()
        )
        
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            
            if row:
                print("   ✅ Config-based connection successful!")
            else:
                print("   ❌ Config-based connection failed")
        
        await engine.dispose()
        
    except Exception as e:
        print(f"   ❌ Config-based connection failed: {e}")


async def main():
    """Main debug function"""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    await debug_tidb_connection()


if __name__ == "__main__":
    asyncio.run(main())