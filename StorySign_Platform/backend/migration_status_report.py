"""
Generate a migration status report without requiring database connection
Shows what migrations are expected and what files exist
"""

import os
from typing import Dict, List, Set
from pathlib import Path


def get_expected_tables() -> Dict[str, str]:
    """Get expected tables from models with their migration source"""
    
    return {
        # User management tables
        "users": "user_models",
        "user_profiles": "user_models", 
        "user_sessions": "user_models",
        
        # Content management tables
        "stories": "content_migration",
        "story_tags": "content_migration",
        "story_versions": "content_migration",
        "story_ratings": "content_migration",
        "content_approvals": "content_migration",
        
        # Progress tracking tables
        "practice_sessions": "progress_migration",
        "sentence_attempts": "progress_migration",
        "user_progress": "progress_migration",
        
        # Collaborative learning tables
        "learning_groups": "collaborative_migration",
        "group_memberships": "collaborative_migration",
        "collaborative_sessions": "collaborative_migration",
        "group_analytics": "collaborative_migration",
        
        # Plugin system tables
        "plugins": "plugin_models",
        "plugin_data": "plugin_models"
    }


def check_migration_files() -> Dict[str, Dict[str, any]]:
    """Check which migration files exist"""
    
    migrations_dir = Path("migrations")
    
    migration_files = {
        "user_models": "create_user_tables.py",
        "content_migration": "create_content_tables.py", 
        "progress_migration": "create_progress_tables.py",
        "collaborative_migration": "create_collaborative_tables.py",
        "plugin_models": "create_plugin_tables.py"
    }
    
    status = {}
    
    for migration_type, filename in migration_files.items():
        file_path = migrations_dir / filename
        exists = file_path.exists()
        
        status[migration_type] = {
            "filename": filename,
            "exists": exists,
            "path": str(file_path),
            "size": file_path.stat().st_size if exists else 0
        }
    
    return status


def analyze_migration_status():
    """Analyze migration status and generate report"""
    
    print("📊 StorySign Database Migration Status Report")
    print("=" * 55)
    print()
    
    # Get expected tables
    expected_tables = get_expected_tables()
    
    # Check migration files
    migration_status = check_migration_files()
    
    # Group tables by migration
    migration_groups = {}
    for table, source in expected_tables.items():
        if source not in migration_groups:
            migration_groups[source] = []
        migration_groups[source].append(table)
    
    print("🎯 Expected Database Schema:")
    print("-" * 30)
    
    total_tables = 0
    total_migrations = 0
    available_migrations = 0
    
    for migration_type, tables in migration_groups.items():
        file_status = migration_status.get(migration_type, {})
        exists = file_status.get("exists", False)
        
        status_icon = "✅" if exists else "❌"
        status_text = "AVAILABLE" if exists else "MISSING"
        
        print(f"\n{status_icon} {migration_type.upper()} - {status_text}")
        print(f"   File: {file_status.get('filename', 'N/A')}")
        print(f"   Tables: {len(tables)} ({', '.join(tables)})")
        
        if exists:
            size_kb = file_status.get('size', 0) / 1024
            print(f"   Size: {size_kb:.1f} KB")
            available_migrations += 1
        
        total_tables += len(tables)
        total_migrations += 1
    
    print(f"\n📈 Summary:")
    print(f"   Total Expected Tables: {total_tables}")
    print(f"   Total Migrations: {total_migrations}")
    print(f"   Available Migrations: {available_migrations}")
    print(f"   Missing Migrations: {total_migrations - available_migrations}")
    
    if available_migrations == total_migrations:
        print(f"   🎉 All migration files are available!")
    else:
        print(f"   ⚠️  {total_migrations - available_migrations} migration files need to be created")
    
    return available_migrations == total_migrations


def show_migration_commands():
    """Show commands to run migrations"""
    
    print(f"\n🚀 Migration Commands:")
    print("-" * 20)
    
    migration_files = [
        "create_user_tables.py",
        "create_content_tables.py", 
        "create_progress_tables.py",
        "create_collaborative_tables.py",
        "create_plugin_tables.py"
    ]
    
    print("\nTo apply migrations (when TiDB is running):")
    for i, filename in enumerate(migration_files, 1):
        file_path = Path("migrations") / filename
        if file_path.exists():
            print(f"  {i}. python migrations/{filename}")
        else:
            print(f"  {i}. python migrations/{filename} (⚠️  FILE MISSING)")
    
    print(f"\nTo check database status:")
    print(f"  python check_database_migrations.py")
    
    print(f"\nTo create missing migration files:")
    print(f"  python create_missing_migrations.py")


def check_model_files():
    """Check if model files exist and are properly structured"""
    
    print(f"\n🏗️  Model Files Status:")
    print("-" * 25)
    
    model_files = [
        "models/base.py",
        "models/user.py",
        "models/content.py",
        "models/progress.py", 
        "models/collaborative.py",
        "models/plugin.py"
    ]
    
    for model_file in model_files:
        file_path = Path(model_file)
        exists = file_path.exists()
        
        status_icon = "✅" if exists else "❌"
        status_text = "EXISTS" if exists else "MISSING"
        
        print(f"  {status_icon} {model_file} - {status_text}")
        
        if exists:
            size_kb = file_path.stat().st_size / 1024
            print(f"      Size: {size_kb:.1f} KB")


def main():
    """Main function to generate migration status report"""
    
    # Change to backend directory if needed
    if not Path("migrations").exists():
        if Path("backend/migrations").exists():
            os.chdir("backend")
        else:
            print("❌ Cannot find migrations directory")
            return False
    
    # Check migration status
    all_available = analyze_migration_status()
    
    # Check model files
    check_model_files()
    
    # Show migration commands
    show_migration_commands()
    
    print(f"\n💡 Next Steps:")
    print("-" * 15)
    
    if all_available:
        print("  1. ✅ All migration files are available")
        print("  2. 🚀 Start TiDB database server")
        print("  3. 🔧 Run migrations to create tables")
        print("  4. ✅ Verify database schema")
        print("  5. 🧪 Test application functionality")
    else:
        print("  1. ⚠️  Create missing migration files")
        print("  2. 🚀 Start TiDB database server") 
        print("  3. 🔧 Run migrations to create tables")
        print("  4. ✅ Verify database schema")
        print("  5. 🧪 Test application functionality")
    
    print(f"\n📋 Database Requirements:")
    print("  • TiDB Server running on localhost:4000")
    print("  • Database name: storysign")
    print("  • User: root (or configured user)")
    print("  • All migration files present")
    
    return all_available


if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n🎉 Migration status check completed - All files available!")
    else:
        print(f"\n⚠️  Migration status check completed - Some files missing!")
    
    exit(0 if success else 1)