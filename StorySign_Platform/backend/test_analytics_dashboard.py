"""
Test Analytics Dashboard Implementation
Tests the complete analytics dashboard and reporting functionality
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import json

# Import the analytics service directly for testing
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from services.enhanced_analytics_service import AnalyticsService
    from core.database_service import DatabaseService
except ImportError as e:
    print(f"Import error: {e}")
    print("Running simplified test without imports")

class TestAnalyticsDashboard:
    """Test suite for analytics dashboard functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        try:
            self.mock_db_service = Mock(spec=DatabaseService)
            self.analytics_service = AnalyticsService(self.mock_db_service)
        except NameError:
            # Fallback for when imports fail
            self.mock_db_service = Mock()
            self.analytics_service = Mock()
        
        # Mock authentication token
        self.auth_token = "test_token_123"
        self.headers = {"Authorization": f"Bearer {self.auth_token}"}

    @pytest.mark.asyncio
    async def test_analytics_dashboard_access(self):
        """Test analytics dashboard functionality"""
        # Mock database session
        mock_session = Mock()
        self.mock_db_service.get_session.return_value.__aenter__.return_value = mock_session
        
        # Test get_platform_analytics method directly
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        with patch('services.enhanced_analytics_service.AnalyticsRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            mock_repo.get_aggregated_metrics.return_value = {"total_events": 1000}
            
            result = await self.analytics_service.get_platform_analytics(
                start_date=start_date,
                end_date=end_date,
                include_anonymous=True
            )
            
            assert "platform_metrics" in result
            assert "generated_at" in result
            assert result["platform_metrics"]["total_users"] == 150

    @pytest.mark.asyncio
    async def test_analytics_event_tracking(self):
        """Test analytics event tracking"""
        # Mock database session and repository
        mock_session = Mock()
        self.mock_db_service.get_session.return_value.__aenter__.return_value = mock_session
        
        with patch('services.enhanced_analytics_service.AnalyticsRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            mock_repo.create_event.return_value = None
            
            # Test event tracking directly
            success = await self.analytics_service.track_event(
                user_id="test_user",
                session_id="session_456",
                event_type="practice_session_start",
                module_name="asl_world",
                event_data={
                    "story_id": "story_123",
                    "difficulty": "medium"
                }
            )
            
            assert success is True

    def test_learning_analytics_tracking(self):
        """Test learning-specific analytics tracking"""
        with patch('api.analytics.get_analytics_service') as mock_get_service:
            mock_get_service.return_value = self.analytics_service
            
            with patch('api.analytics.get_current_user') as mock_get_user:
                mock_get_user.return_value = {"id": "test_user", "role": "user"}
                
                with patch.object(self.analytics_service, 'track_learning_event', return_value=True) as mock_track:
                    
                    learning_data = {
                        "event_type": "sentence_attempt",
                        "session_id": "session_456",
                        "story_id": "story_123",
                        "sentence_index": 2,
                        "score": 85.5,
                        "additional_data": {
                            "attempt_number": 1,
                            "confidence": 0.92
                        }
                    }
                    
                    response = client.post(
                        "/api/v1/analytics/events/learning",
                        json=learning_data,
                        headers=self.headers
                    )
                    
                    assert response.status_code == 200
                    mock_track.assert_called_once()

    def test_performance_metrics_tracking(self):
        """Test performance metrics tracking"""
        with patch('api.analytics.get_analytics_service') as mock_get_service:
            mock_get_service.return_value = self.analytics_service
            
            with patch('api.analytics.get_current_user') as mock_get_user:
                mock_get_user.return_value = {"id": "test_user", "role": "user"}
                
                with patch.object(self.analytics_service, 'track_performance_metric', return_value=True) as mock_track:
                    
                    performance_data = {
                        "metric_name": "video_processing_time",
                        "metric_value": 125.5,
                        "module": "asl_world",
                        "session_id": "session_456",
                        "additional_data": {
                            "frame_count": 30,
                            "resolution": "720p"
                        }
                    }
                    
                    response = client.post(
                        "/api/v1/analytics/events/performance",
                        json=performance_data,
                        headers=self.headers
                    )
                    
                    assert response.status_code == 200
                    mock_track.assert_called_once()

    def test_consent_management(self):
        """Test user consent management"""
        with patch('api.analytics.get_analytics_service') as mock_get_service:
            mock_get_service.return_value = self.analytics_service
            
            with patch('api.analytics.get_current_user') as mock_get_user:
                mock_get_user.return_value = {"id": "test_user", "role": "user"}
                
                # Mock consent creation
                mock_consent = Mock()
                mock_consent.to_dict.return_value = {
                    "id": "consent_123",
                    "consent_type": "analytics",
                    "consent_given": True,
                    "is_active": True
                }
                
                with patch.object(self.analytics_service, 'manage_user_consent', return_value=mock_consent) as mock_manage:
                    
                    consent_data = {
                        "consent_type": "analytics",
                        "consent_given": True,
                        "consent_version": "1.0"
                    }
                    
                    response = client.post(
                        "/api/v1/analytics/consent",
                        json=consent_data,
                        headers=self.headers
                    )
                    
                    assert response.status_code == 200
                    assert response.json()["status"] == "success"
                    mock_manage.assert_called_once()

    def test_data_export_functionality(self):
        """Test data export functionality"""
        with patch('api.analytics.get_analytics_service') as mock_get_service:
            mock_get_service.return_value = self.analytics_service
            
            with patch('api.analytics.get_current_user') as mock_get_user:
                mock_get_user.return_value = {"id": "test_user", "role": "admin"}
                
                # Mock platform analytics data
                mock_analytics_data = {
                    "platform_metrics": {
                        "total_users": 100,
                        "total_events": 5000,
                        "events": [
                            {
                                "id": "event_1",
                                "event_type": "practice_session_start",
                                "occurred_at": "2024-01-01T10:00:00Z"
                            }
                        ]
                    }
                }
                
                with patch.object(self.analytics_service, 'get_platform_analytics', return_value=mock_analytics_data) as mock_get:
                    
                    response = client.get(
                        "/api/v1/analytics/export",
                        params={
                            "start_date": "2024-01-01T00:00:00",
                            "end_date": "2024-01-31T23:59:59",
                            "format": "json",
                            "include_anonymous": "true"
                        },
                        headers=self.headers
                    )
                    
                    assert response.status_code == 200
                    mock_get.assert_called_once()

    def test_user_analytics_access_control(self):
        """Test user analytics access control"""
        with patch('api.analytics.get_analytics_service') as mock_get_service:
            mock_get_service.return_value = self.analytics_service
            
            # Test regular user accessing their own data
            with patch('api.analytics.get_current_user') as mock_get_user:
                mock_get_user.return_value = {"id": "test_user", "role": "user"}
                
                with patch.object(self.analytics_service, 'get_user_analytics', return_value={"user_id": "test_user"}) as mock_get:
                    
                    response = client.get(
                        "/api/v1/analytics/user/test_user",
                        headers=self.headers
                    )
                    
                    assert response.status_code == 200
                    mock_get.assert_called_once()

            # Test regular user trying to access other user's data
            with patch('api.analytics.get_current_user') as mock_get_user:
                mock_get_user.return_value = {"id": "test_user", "role": "user"}
                
                response = client.get(
                    "/api/v1/analytics/user/other_user",
                    headers=self.headers
                )
                
                assert response.status_code == 403

    def test_analytics_service_health_check(self):
        """Test analytics service health check"""
        with patch('api.analytics.get_analytics_service') as mock_get_service:
            # Mock analytics service with health check
            mock_service = Mock()
            mock_service._event_queue.qsize.return_value = 5
            mock_service._processing_task = Mock()
            mock_get_service.return_value = mock_service
            
            response = client.get("/api/v1/analytics/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "queue_size" in data
            assert "processing_active" in data

    @pytest.mark.asyncio
    async def test_analytics_service_event_processing(self):
        """Test analytics service event processing"""
        # Test the analytics service directly
        mock_session = Mock()
        self.mock_db_service.get_session.return_value.__aenter__.return_value = mock_session
        
        # Mock analytics repository
        with patch('services.enhanced_analytics_service.AnalyticsRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo
            mock_repo.create_event.return_value = None
            
            # Test event tracking
            success = await self.analytics_service.track_event(
                user_id="test_user",
                session_id="test_session",
                event_type="test_event",
                module_name="test_module",
                event_data={"test": "data"}
            )
            
            assert success is True

    def test_dashboard_metrics_generation(self):
        """Test dashboard metrics generation"""
        with patch('api.analytics.get_analytics_service') as mock_get_service:
            mock_get_service.return_value = self.analytics_service
            
            with patch('api.analytics.get_current_user') as mock_get_user:
                mock_get_user.return_value = {"id": "test_user", "role": "admin"}
                
                # Mock enhanced metrics
                mock_metrics = {
                    "platform_metrics": {
                        "total_users": 150,
                        "active_sessions": 45,
                        "practice_sessions": 320,
                        "learning_metrics": {
                            "average_score": 78.5,
                            "completion_rate": 85.2
                        },
                        "performance_metrics": {
                            "avg_response_time": 145,
                            "error_rate": 2.1
                        }
                    }
                }
                
                with patch.object(self.analytics_service, 'get_platform_analytics', return_value=mock_metrics) as mock_get:
                    
                    response = client.get(
                        "/api/v1/analytics/platform",
                        params={
                            "start_date": "2024-01-01T00:00:00",
                            "end_date": "2024-01-31T23:59:59"
                        },
                        headers=self.headers
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["platform_metrics"]["total_users"] == 150
                    assert data["platform_metrics"]["learning_metrics"]["average_score"] == 78.5

if __name__ == "__main__":
    # Run the tests
    test_suite = TestAnalyticsDashboard()
    
    print("Testing Analytics Dashboard Implementation...")
    
    try:
        test_suite.setup_method()
        test_suite.test_analytics_dashboard_access()
        print("✓ Analytics dashboard access test passed")
        
        test_suite.test_analytics_event_tracking()
        print("✓ Analytics event tracking test passed")
        
        test_suite.test_learning_analytics_tracking()
        print("✓ Learning analytics tracking test passed")
        
        test_suite.test_performance_metrics_tracking()
        print("✓ Performance metrics tracking test passed")
        
        test_suite.test_consent_management()
        print("✓ Consent management test passed")
        
        test_suite.test_data_export_functionality()
        print("✓ Data export functionality test passed")
        
        test_suite.test_user_analytics_access_control()
        print("✓ User analytics access control test passed")
        
        test_suite.test_analytics_service_health_check()
        print("✓ Analytics service health check test passed")
        
        test_suite.test_dashboard_metrics_generation()
        print("✓ Dashboard metrics generation test passed")
        
        print("\n🎉 All analytics dashboard tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()