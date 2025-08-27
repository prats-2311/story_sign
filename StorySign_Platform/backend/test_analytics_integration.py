"""
Analytics Integration Test
Test analytics system integration with existing StorySign infrastructure
"""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import uuid

# Test the analytics system integration
def test_analytics_models_import():
    """Test that analytics models can be imported correctly"""
    try:
        from models.analytics import (
            AnalyticsEvent, UserConsent, AnalyticsAggregation, 
            DataRetentionPolicy, AnalyticsSession, ConsentType, EventType
        )
        print("✓ Analytics models imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import analytics models: {e}")
        return False

def test_analytics_repository_import():
    """Test that analytics repositories can be imported"""
    try:
        from repositories.analytics_repository import (
            AnalyticsRepository, ConsentRepository, AnalyticsSessionRepository
        )
        print("✓ Analytics repositories imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import analytics repositories: {e}")
        return False

def test_analytics_service_import():
    """Test that analytics service can be imported"""
    try:
        from services.enhanced_analytics_service import AnalyticsService, get_analytics_service
        print("✓ Analytics service imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import analytics service: {e}")
        return False

def test_analytics_api_import():
    """Test that analytics API can be imported"""
    try:
        from api.analytics_simple import router
        print("✓ Analytics API imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Failed to import analytics API: {e}")
        return False

def test_event_type_definitions():
    """Test that event types are properly defined"""
    try:
        from models.analytics import EventType, ConsentType
        
        # Test some key event types
        assert EventType.PRACTICE_SESSION_START == "practice_session_start"
        assert EventType.GESTURE_DETECTED == "gesture_detected"
        assert EventType.USER_LOGIN == "user_login"
        
        # Test consent types
        assert ConsentType.ANALYTICS == "analytics"
        assert ConsentType.RESEARCH == "research"
        
        print("✓ Event and consent types defined correctly")
        return True
    except Exception as e:
        print(f"✗ Event type definitions failed: {e}")
        return False

def test_analytics_event_creation():
    """Test creating analytics events"""
    try:
        from models.analytics import AnalyticsEvent, EventType
        
        event = AnalyticsEvent(
            user_id=str(uuid.uuid4()),
            session_id="test_session",
            event_type=EventType.PRACTICE_SESSION_START,
            module_name="asl_world",
            event_data={"story_id": "test_story", "difficulty": "beginner"},
            is_anonymous=False
        )
        
        assert event.user_id is not None
        assert event.session_id == "test_session"
        assert event.event_type == EventType.PRACTICE_SESSION_START
        assert event.event_data["story_id"] == "test_story"
        
        print("✓ Analytics event creation works")
        return True
    except Exception as e:
        print(f"✗ Analytics event creation failed: {e}")
        return False

def test_consent_management():
    """Test user consent management"""
    try:
        from models.analytics import UserConsent, ConsentType
        
        consent = UserConsent(
            user_id=str(uuid.uuid4()),
            consent_type=ConsentType.ANALYTICS,
            consent_given=True,
            consent_version="1.0"
        )
        
        assert consent.is_active is True
        
        # Test revocation
        consent.revoke()
        assert consent.is_active is False
        assert consent.revoked_at is not None
        
        print("✓ Consent management works")
        return True
    except Exception as e:
        print(f"✗ Consent management failed: {e}")
        return False

def test_analytics_service_initialization():
    """Test analytics service can be initialized"""
    try:
        from services.enhanced_analytics_service import AnalyticsService
        from core.database_service import DatabaseService
        
        # Mock database service
        mock_db_service = Mock(spec=DatabaseService)
        
        # Initialize analytics service
        analytics_service = AnalyticsService(mock_db_service)
        
        assert analytics_service.db_service == mock_db_service
        assert analytics_service._event_queue is not None
        
        print("✓ Analytics service initialization works")
        return True
    except Exception as e:
        print(f"✗ Analytics service initialization failed: {e}")
        return False

def test_frontend_integration():
    """Test that frontend analytics components exist"""
    import os
    
    # Get the correct base path
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    frontend_files = [
        os.path.join(base_path, "frontend/src/services/AnalyticsService.js"),
        os.path.join(base_path, "frontend/src/hooks/useAnalytics.js"),
        os.path.join(base_path, "frontend/src/components/privacy/ConsentManager.js"),
        os.path.join(base_path, "frontend/src/components/privacy/ConsentManager.css")
    ]
    
    all_exist = True
    for file_path in frontend_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} missing")
            all_exist = False
    
    return all_exist

def test_api_router_integration():
    """Test that analytics API is integrated into main router"""
    try:
        from api.router import api_router
        
        # Check if analytics routes are included
        routes = []
        for route in api_router.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
            elif hasattr(route, 'prefix'):
                routes.append(route.prefix)
        
        # Look for analytics-related routes
        has_analytics_routes = any("/analytics" in str(route) for route in routes)
        
        if has_analytics_routes:
            print("✓ Analytics API integrated into main router")
            return True
        else:
            print("✗ Analytics API not found in main router")
            print(f"Available routes: {routes}")
            return False
            
    except Exception as e:
        print(f"✗ API router integration test failed: {e}")
        return False

def test_privacy_compliance_features():
    """Test privacy compliance features"""
    try:
        from models.analytics import AnalyticsEvent
        
        # Test anonymization
        event = AnalyticsEvent(
            user_id=str(uuid.uuid4()),
            session_id="test_session",
            event_type="test_event",
            module_name="test_module",
            event_data={
                "email": "test@example.com",
                "ip_address": "192.168.1.1",
                "normal_data": "keep_this"
            }
        )
        
        # Anonymize
        event.anonymize()
        
        assert event.user_id is None
        assert event.is_anonymous is True
        assert "email" not in event.event_data
        assert "ip_address" not in event.event_data
        assert event.event_data.get("normal_data") == "keep_this"
        
        print("✓ Privacy compliance features work")
        return True
    except Exception as e:
        print(f"✗ Privacy compliance test failed: {e}")
        return False

def run_integration_tests():
    """Run all analytics integration tests"""
    print("🔍 Running Analytics Integration Tests...")
    print("=" * 50)
    
    tests = [
        ("Model Imports", test_analytics_models_import),
        ("Repository Imports", test_analytics_repository_import),
        ("Service Imports", test_analytics_service_import),
        ("API Imports", test_analytics_api_import),
        ("Event Type Definitions", test_event_type_definitions),
        ("Event Creation", test_analytics_event_creation),
        ("Consent Management", test_consent_management),
        ("Service Initialization", test_analytics_service_initialization),
        ("Frontend Integration", test_frontend_integration),
        ("API Router Integration", test_api_router_integration),
        ("Privacy Compliance", test_privacy_compliance_features),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All analytics integration tests passed!")
        print("\n✅ Analytics System Ready:")
        print("   • Real-time event collection")
        print("   • Privacy-compliant data processing")
        print("   • User consent management")
        print("   • GDPR compliance features")
        print("   • Frontend integration")
        print("   • API endpoints")
        return True
    else:
        print(f"❌ {failed} tests failed. Please fix issues before proceeding.")
        return False

if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)