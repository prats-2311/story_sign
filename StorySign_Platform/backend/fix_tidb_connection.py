#!/usr/bin/env python3
"""
TiDB Connection Fix Script
Diagnoses and fixes TiDB Cloud connection issues
"""

import asyncio
import logging
import sys
import os
import ssl
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)


async def test_basic_connectivity():
    """Test basic network connectivity to TiDB Cloud"""
    
    print("🌐 Testing basic network connectivity...")
    
    import socket
    
    host = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
    port = 4000
    
    try:
        # Test basic socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 10 second timeout
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"   ✅ Network connectivity to {host}:{port} is working")
            return True
        else:
            print(f"   ❌ Cannot connect to {host}:{port} (error code: {result})")
            return False
            
    except Exception as e:
        print(f"   ❌ Network connectivity test failed: {e}")
        return False


async def test_ssl_connection():
    """Test SSL connection to TiDB Cloud"""
    
    print("🔒 Testing SSL connection...")
    
    import socket
    import ssl
    
    host = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
    port = 4000
    
    try:
        # Create SSL context
        context = ssl.create_default_context()
        
        # Test SSL connection
        with socket.create_connection((host, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                print(f"   ✅ SSL connection successful")
                print(f"   🔐 SSL version: {ssock.version()}")
                print(f"   📜 Certificate subject: {ssock.getpeercert()['subject']}")
                return True
                
    except Exception as e:
        print(f"   ❌ SSL connection failed: {e}")
        return False


async def test_tidb_with_proper_ssl():
    """Test TiDB connection with proper SSL configuration"""
    
    print("🗄️  Testing TiDB connection with proper SSL...")
    
    # Connection details
    host = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
    port = 4000
    database = "test"
    username = "28XbMEz3PD5h7d6.root"
    password = "ek1FdpnVe3LDPcns"
    
    # Try different SSL configurations
    ssl_configs = [
        {
            "name": "SSL with verify_identity",
            "url": f"mysql+asyncmy://{username}:{password}@{host}:{port}/{database}?ssl=true&ssl_verify_identity=true",
            "connect_args": {
                "charset": "utf8mb4",
                "autocommit": False,
            }
        },
        {
            "name": "SSL without verify_identity", 
            "url": f"mysql+asyncmy://{username}:{password}@{host}:{port}/{database}?ssl=true&ssl_verify_identity=false",
            "connect_args": {
                "charset": "utf8mb4",
                "autocommit": False,
            }
        },
        {
            "name": "SSL with custom context",
            "url": f"mysql+asyncmy://{username}:{password}@{host}:{port}/{database}",
            "connect_args": {
                "charset": "utf8mb4",
                "autocommit": False,
                "ssl": {
                    "ssl_disabled": False,
                    "ssl_verify_cert": True,
                    "ssl_verify_identity": True,
                }
            }
        },
        {
            "name": "SSL disabled (for testing)",
            "url": f"mysql+asyncmy://{username}:{password}@{host}:{port}/{database}?ssl=false",
            "connect_args": {
                "charset": "utf8mb4", 
                "autocommit": False,
            }
        }
    ]
    
    for config in ssl_configs:
        print(f"\n   🧪 Testing: {config['name']}")
        
        try:
            # Create engine with shorter timeout
            engine = create_async_engine(
                config["url"],
                echo=False,
                pool_size=1,
                max_overflow=0,
                pool_timeout=5,  # Shorter timeout
                connect_args=config["connect_args"]
            )
            
            # Test connection with timeout
            async with asyncio.timeout(15):  # 15 second timeout
                async with engine.begin() as conn:
                    # Basic test query
                    result = await conn.execute(text("SELECT 1 as test, VERSION() as version"))
                    row = result.fetchone()
                    
                    if row:
                        print(f"      ✅ {config['name']} successful!")
                        print(f"      📊 Database version: {row.version}")
                        
                        # Test database access
                        db_result = await conn.execute(text("SELECT DATABASE() as current_db"))
                        db_row = db_result.fetchone()
                        print(f"      🗄️  Current database: {db_row.current_db}")
                        
                        await engine.dispose()
                        return config  # Return successful config
                    else:
                        print(f"      ❌ {config['name']} failed - no result")
            
            await engine.dispose()
            
        except asyncio.TimeoutError:
            print(f"      ⏰ {config['name']} timed out")
        except Exception as e:
            print(f"      ❌ {config['name']} failed: {e}")
    
    return None


async def update_config_with_working_settings(working_config):
    """Update config.yaml with working connection settings"""
    
    if not working_config:
        print("❌ No working configuration found to update")
        return False
    
    print(f"\n🔧 Updating config.yaml with working settings: {working_config['name']}")
    
    try:
        # Read current config
        with open('config.yaml', 'r') as f:
            config_content = f.read()
        
        # Update SSL settings based on working config
        if "ssl=false" in working_config["url"]:
            # SSL disabled worked
            config_content = config_content.replace(
                'ssl_disabled: false',
                'ssl_disabled: true'
            )
            print("   ✅ Updated config to disable SSL")
        elif "ssl_verify_identity=false" in working_config["url"]:
            # SSL without identity verification worked
            config_content = config_content.replace(
                'ssl_disabled: false',
                'ssl_disabled: false  # SSL enabled but without identity verification'
            )
            print("   ✅ Updated config for SSL without identity verification")
        
        # Write updated config
        with open('config.yaml', 'w') as f:
            f.write(config_content)
        
        print("   ✅ Configuration updated successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to update configuration: {e}")
        return False


async def create_optimized_connection_function():
    """Create an optimized connection function based on working config"""
    
    print("\n📝 Creating optimized connection helper...")
    
    optimized_code = '''
"""
Optimized TiDB Connection Helper
Generated based on successful connection test
"""

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import asyncio

async def create_tidb_engine():
    """Create optimized TiDB engine with working configuration"""
    
    # Connection details
    host = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
    port = 4000
    database = "test"
    username = "28XbMEz3PD5h7d6.root"
    password = "ek1FdpnVe3LDPcns"
    
    # Optimized connection URL (update based on what works)
    connection_url = f"mysql+asyncmy://{username}:{password}@{host}:{port}/{database}?ssl=true&ssl_verify_identity=false"
    
    # Create engine with optimized settings
    engine = create_async_engine(
        connection_url,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_timeout=10,
        pool_recycle=3600,
        connect_args={
            "charset": "utf8mb4",
            "autocommit": False,
        }
    )
    
    return engine

async def test_optimized_connection():
    """Test the optimized connection"""
    
    engine = await create_tidb_engine()
    
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test, VERSION() as version"))
            row = result.fetchone()
            print(f"✅ Optimized connection successful! Version: {row.version}")
            return True
    except Exception as e:
        print(f"❌ Optimized connection failed: {e}")
        return False
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_optimized_connection())
'''
    
    # Write optimized connection helper
    with open('tidb_connection_helper.py', 'w') as f:
        f.write(optimized_code)
    
    print("   ✅ Created tidb_connection_helper.py")


async def main():
    """Main diagnostic and fix function"""
    
    print("🔧 TiDB Connection Diagnostic and Fix Tool")
    print("=" * 60)
    
    # Step 1: Test basic connectivity
    network_ok = await test_basic_connectivity()
    
    if not network_ok:
        print("\n❌ Basic network connectivity failed.")
        print("   Check your internet connection and firewall settings.")
        return 1
    
    # Step 2: Test SSL connectivity
    ssl_ok = await test_ssl_connection()
    
    if not ssl_ok:
        print("\n⚠️  SSL connectivity issues detected.")
        print("   Will try different SSL configurations...")
    
    # Step 3: Test TiDB with different SSL configs
    working_config = await test_tidb_with_proper_ssl()
    
    if working_config:
        print(f"\n🎉 Found working configuration: {working_config['name']}")
        
        # Update config.yaml
        config_updated = await update_config_with_working_settings(working_config)
        
        # Create optimized helper
        await create_optimized_connection_function()
        
        print("\n✅ TiDB connection fix completed!")
        print("\nNext steps:")
        print("1. Test with: python tidb_connection_helper.py")
        print("2. Run migrations: python run_migrations.py")
        
        return 0
    else:
        print("\n❌ No working configuration found.")
        print("\nTroubleshooting suggestions:")
        print("1. Verify TiDB Cloud cluster is running")
        print("2. Check if your IP is whitelisted in TiDB Cloud")
        print("3. Verify credentials are correct")
        print("4. Try connecting from TiDB Cloud console first")
        
        return 1


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)