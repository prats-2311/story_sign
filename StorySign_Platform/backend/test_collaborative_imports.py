"""
Test collaborative imports to ensure they work correctly
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all collaborative imports"""
    try:
        print("Testing collaborative model imports...")
        from models.collaborative import (
            LearningGroup, GroupMembership, CollaborativeSession, GroupAnalytics,
            GroupRole, GroupPrivacy, SessionStatus, DataSharingLevel
        )
        print("✅ Collaborative models imported successfully")
        
        print("Testing collaborative repository imports...")
        from repositories.collaborative_repository import (
            LearningGroupRepository, GroupMembershipRepository,
            CollaborativeSessionRepository, GroupAnalyticsRepository
        )
        print("✅ Collaborative repositories imported successfully")
        
        print("Testing collaborative service imports...")
        from services.collaborative_service import CollaborativeService
        print("✅ Collaborative service imported successfully")
        
        print("Testing collaborative API imports...")
        from api.collaborative import router
        print("✅ Collaborative API imported successfully")
        
        print("\n🎉 All collaborative imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n✅ Collaborative features are ready for integration!")
    else:
        print("\n❌ Import issues need to be resolved")
        sys.exit(1)