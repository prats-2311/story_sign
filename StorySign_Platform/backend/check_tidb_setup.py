#!/usr/bin/env python3
"""
TiDB Setup Verification Script
Checks if all dependencies and configuration are ready for TiDB integration
"""

import sys
import importlib
import logging

logger = logging.getLogger(__name__)


def check_dependencies():
    """Check if all required dependencies are installed"""
    
    required_packages = [
        ('sqlalchemy', 'SQLAlchemy ORM'),
        ('asyncmy', 'Async MySQL driver'),
        ('pymysql', 'PyMySQL driver'),
        ('mysql.connector', 'MySQL Connector Python'),
    ]
    
    print("🔍 Checking TiDB dependencies...")
    print("-" * 40)
    
    missing_packages = []
    
    for package, description in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package:<20} - {description}")
        except ImportError:
            print(f"❌ {package:<20} - {description} (MISSING)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: ./install_tidb_deps.sh or pip install the missing packages")
        return False
    else:
        print("\n✅ All dependencies are installed!")
        return True


def check_configuration():
    """Check if TiDB configuration is properly set"""
    
    print("\n🔍 Checking TiDB configuration...")
    print("-" * 40)
    
    try:
        from config import get_config
        
        config = get_config()
        db_config = config.database
        
        # Check required configuration fields
        required_fields = {
            'host': 'Database host',
            'port': 'Database port', 
            'database': 'Database name',
            'username': 'Database username',
            'password': 'Database password'
        }
        
        config_ok = True
        
        for field, description in required_fields.items():
            value = getattr(db_config, field, None)
            if value and str(value).strip():
                if field == 'password':
                    # Don't show password, just indicate it's set
                    print(f"✅ {field:<12} - {description} (configured)")
                else:
                    print(f"✅ {field:<12} - {description}: {value}")
            else:
                print(f"❌ {field:<12} - {description} (NOT SET)")
                config_ok = False
        
        # Check TiDB Cloud specific settings
        if hasattr(db_config, 'ssl_disabled'):
            ssl_status = "disabled" if db_config.ssl_disabled else "enabled"
            print(f"✅ {'ssl':<12} - SSL connection: {ssl_status}")
        
        if config_ok:
            print("\n✅ Configuration looks good!")
            
            # Try to build connection URL
            try:
                connection_url = db_config.get_connection_url(async_driver=True)
                # Don't print the full URL (contains password), just confirm it builds
                print("✅ Connection URL can be constructed")
                return True
            except Exception as e:
                print(f"❌ Failed to build connection URL: {e}")
                return False
        else:
            print("\n❌ Configuration is incomplete!")
            print("Please update backend/config.yaml with your TiDB Cloud details")
            return False
            
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False


def check_migration_files():
    """Check if migration files are available"""
    
    print("\n🔍 Checking migration files...")
    print("-" * 40)
    
    import os
    
    migration_files = [
        'migrations/create_user_tables.py',
        'migrations/create_progress_tables.py', 
        'migrations/create_content_tables.py',
        'migrations/create_collaborative_tables.py',
        'migrations/create_plugin_tables.py'
    ]
    
    all_present = True
    
    for migration_file in migration_files:
        if os.path.exists(migration_file):
            print(f"✅ {migration_file}")
        else:
            print(f"❌ {migration_file} (MISSING)")
            all_present = False
    
    if all_present:
        print("\n✅ All migration files are present!")
        return True
    else:
        print("\n❌ Some migration files are missing!")
        return False


def main():
    """Main verification function"""
    
    print("🗄️  TiDB Setup Verification for StorySign")
    print("=" * 50)
    
    # Check all components
    deps_ok = check_dependencies()
    config_ok = check_configuration()
    migrations_ok = check_migration_files()
    
    print("\n" + "=" * 50)
    print("📋 Setup Status Summary:")
    print(f"   Dependencies: {'✅ Ready' if deps_ok else '❌ Issues'}")
    print(f"   Configuration: {'✅ Ready' if config_ok else '❌ Issues'}")
    print(f"   Migration Files: {'✅ Ready' if migrations_ok else '❌ Issues'}")
    
    if deps_ok and config_ok and migrations_ok:
        print("\n🎉 TiDB setup verification passed!")
        print("\nNext steps:")
        print("1. Run: python run_migrations.py")
        print("2. Test: python test_tidb_connection.py")
        return 0
    else:
        print("\n❌ TiDB setup verification failed!")
        print("\nPlease fix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)