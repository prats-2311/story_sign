
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
