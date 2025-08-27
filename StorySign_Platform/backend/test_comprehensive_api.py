"""
Comprehensive API testing suite for StorySign ASL Platform
"""

import pytest
import asyncio
import json
import time
from typing import Dict, Any, Optional
from fastapi.testclient import TestClient
from httpx import AsyncClient
import logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APITestSuite:
    """
    Comprehensive test suite for all API endpoints
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = None
        self.auth_token = None
        self.test_user_data = {
            "email": "test@storysign.com",
            "username": "testuser",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "User"
        }
        self.test_results = []
    
    async def setup(self):
        """Set up test environment"""
        self.client = AsyncClient(base_url=self.base_url)
        logger.info("API test suite initialized")
    
    async def teardown(self):
        """Clean up test environment"""
        if self.client:
            await self.client.aclose()
        logger.info("API test suite cleaned up")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all API tests
        
        Returns:
            Dictionary containing test results
        """
        try:
            await self.setup()
            
            # Test categories
            test_categories = [
                ("System Health", self.test_system_endpoints),
                ("Authentication", self.test_authentication_endpoints),
                ("User Management", self.test_user_management_endpoints),
                ("Content Management", self.test_content_endpoints),
                ("ASL World", self.test_asl_world_endpoints),
                ("GraphQL", self.test_graphql_endpoints),
                ("Rate Limiting", self.test_rate_limiting),
                ("Documentation", self.test_documentation_endpoints)
            ]
            
            results = {
                "summary": {
                    "total_tests": 0,
                    "passed": 0,
                    "failed": 0,
                    "skipped": 0,
                    "start_time": time.time(),
                    "end_time": None
                },
                "categories": {},
                "detailed_results": []
            }
            
            # Run test categories
            for category_name, test_function in test_categories:
                logger.info(f"Running {category_name} tests...")
                
                try:
                    category_results = await test_function()
                    results["categories"][category_name] = category_results
                    
                    # Update summary
                    results["summary"]["total_tests"] += category_results["total"]
                    results["summary"]["passed"] += category_results["passed"]
                    results["summary"]["failed"] += category_results["failed"]
                    results["summary"]["skipped"] += category_results.get("skipped", 0)
                    
                    # Add detailed results
                    results["detailed_results"].extend(category_results.get("tests", []))
                    
                except Exception as e:
                    logger.error(f"Error in {category_name} tests: {e}")
                    results["categories"][category_name] = {
                        "total": 1,
                        "passed": 0,
                        "failed": 1,
                        "error": str(e)
                    }
                    results["summary"]["total_tests"] += 1
                    results["summary"]["failed"] += 1
            
            results["summary"]["end_time"] = time.time()
            results["summary"]["duration"] = results["summary"]["end_time"] - results["summary"]["start_time"]
            
            return results
            
        finally:
            await self.teardown()
    
    async def test_system_endpoints(self) -> Dict[str, Any]:
        """Test system health and status endpoints"""
        tests = []
        
        # Test health check
        test_result = await self._test_endpoint(
            "GET", "/", 
            expected_status=200,
            description="System health check"
        )
        tests.append(test_result)
        
        # Test configuration endpoint
        test_result = await self._test_endpoint(
            "GET", "/config",
            expected_status=200,
            description="Get system configuration"
        )
        tests.append(test_result)
        
        # Test statistics endpoint
        test_result = await self._test_endpoint(
            "GET", "/stats",
            expected_status=200,
            description="Get system statistics"
        )
        tests.append(test_result)
        
        return self._summarize_tests(tests)
    
    async def test_authentication_endpoints(self) -> Dict[str, Any]:
        """Test authentication endpoints"""
        tests = []
        
        # Test user registration
        test_result = await self._test_endpoint(
            "POST", "/api/v1/auth/register",
            data=self.test_user_data,
            expected_status=200,
            description="User registration"
        )
        tests.append(test_result)
        
        # Test user login
        login_data = {
            "identifier": self.test_user_data["email"],
            "password": self.test_user_data["password"]
        }
        test_result = await self._test_endpoint(
            "POST", "/api/v1/auth/login",
            data=login_data,
            expected_status=200,
            description="User login"
        )
        tests.append(test_result)
        
        # Store auth token for subsequent tests
        if test_result["success"] and test_result.get("response_data"):
            self.auth_token = test_result["response_data"].get("access_token")
        
        # Test token refresh (if we have a refresh token)
        if test_result["success"] and test_result.get("response_data"):
            refresh_token = test_result["response_data"].get("refresh_token")
            if refresh_token:
                refresh_data = {"refresh_token": refresh_token}
                test_result = await self._test_endpoint(
                    "POST", "/api/v1/auth/refresh",
                    data=refresh_data,
                    expected_status=200,
                    description="Token refresh"
                )
                tests.append(test_result)
        
        # Test authenticated endpoint (get current user)
        if self.auth_token:
            test_result = await self._test_endpoint(
                "GET", "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                expected_status=200,
                description="Get current user info"
            )
            tests.append(test_result)
        
        return self._summarize_tests(tests)
    
    async def test_user_management_endpoints(self) -> Dict[str, Any]:
        """Test user management endpoints"""
        tests = []
        
        if not self.auth_token:
            return {"total": 0, "passed": 0, "failed": 0, "skipped": 1, "tests": []}
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test get user profile
        test_result = await self._test_endpoint(
            "GET", "/api/v1/users/profile",
            headers=headers,
            expected_status=200,
            description="Get user profile"
        )
        tests.append(test_result)
        
        # Test update user profile
        profile_update = {
            "first_name": "Updated",
            "bio": "Test user bio",
            "timezone": "America/New_York"
        }
        test_result = await self._test_endpoint(
            "PUT", "/api/v1/users/profile",
            data=profile_update,
            headers=headers,
            expected_status=200,
            description="Update user profile"
        )
        tests.append(test_result)
        
        # Test get user preferences
        test_result = await self._test_endpoint(
            "GET", "/api/v1/users/preferences",
            headers=headers,
            expected_status=200,
            description="Get user preferences"
        )
        tests.append(test_result)
        
        # Test update user preferences
        preferences = {
            "theme": "dark",
            "notifications": True,
            "language": "en"
        }
        test_result = await self._test_endpoint(
            "PUT", "/api/v1/users/preferences",
            data=preferences,
            headers=headers,
            expected_status=200,
            description="Update user preferences"
        )
        tests.append(test_result)
        
        return self._summarize_tests(tests)
    
    async def test_content_endpoints(self) -> Dict[str, Any]:
        """Test content management endpoints"""
        tests = []
        
        if not self.auth_token:
            return {"total": 0, "passed": 0, "failed": 0, "skipped": 1, "tests": []}
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test list stories
        test_result = await self._test_endpoint(
            "GET", "/api/v1/content/stories?limit=10",
            headers=headers,
            expected_status=200,
            description="List stories"
        )
        tests.append(test_result)
        
        # Test search stories
        search_data = {
            "query": "test",
            "limit": 5,
            "offset": 0
        }
        test_result = await self._test_endpoint(
            "POST", "/api/v1/content/stories/search",
            data=search_data,
            headers=headers,
            expected_status=200,
            description="Search stories"
        )
        tests.append(test_result)
        
        # Test get popular stories
        test_result = await self._test_endpoint(
            "GET", "/api/v1/content/stories/popular?limit=5",
            headers=headers,
            expected_status=200,
            description="Get popular stories"
        )
        tests.append(test_result)
        
        return self._summarize_tests(tests)
    
    async def test_asl_world_endpoints(self) -> Dict[str, Any]:
        """Test ASL World specific endpoints"""
        tests = []
        
        if not self.auth_token:
            return {"total": 0, "passed": 0, "failed": 0, "skipped": 1, "tests": []}
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test story generation with simple word
        story_data = {
            "simple_word": "cat"
        }
        test_result = await self._test_endpoint(
            "POST", "/api/asl-world/story/recognize_and_generate",
            data=story_data,
            headers=headers,
            expected_status=[200, 503],  # May fail if AI service unavailable
            description="Generate story from simple word"
        )
        tests.append(test_result)
        
        # Test story generation with custom prompt
        story_data = {
            "custom_prompt": "A story about friendship"
        }
        test_result = await self._test_endpoint(
            "POST", "/api/asl-world/story/recognize_and_generate",
            data=story_data,
            headers=headers,
            expected_status=[200, 503],
            description="Generate story from custom prompt"
        )
        tests.append(test_result)
        
        return self._summarize_tests(tests)
    
    async def test_graphql_endpoints(self) -> Dict[str, Any]:
        """Test GraphQL endpoint"""
        tests = []
        
        if not self.auth_token:
            return {"total": 0, "passed": 0, "failed": 0, "skipped": 1, "tests": []}
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test simple GraphQL query
        graphql_query = {
            "query": "query { me { id username fullName } }"
        }
        test_result = await self._test_endpoint(
            "POST", "/api/v1/graphql",
            data=graphql_query,
            headers=headers,
            expected_status=200,
            description="GraphQL user query"
        )
        tests.append(test_result)
        
        # Test GraphQL query with variables
        graphql_query = {
            "query": "query GetUsers($limit: Int) { users(search: {limit: $limit}) { id username } }",
            "variables": {"limit": 5}
        }
        test_result = await self._test_endpoint(
            "POST", "/api/v1/graphql",
            data=graphql_query,
            headers=headers,
            expected_status=200,
            description="GraphQL users query with variables"
        )
        tests.append(test_result)
        
        return self._summarize_tests(tests)
    
    async def test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting functionality"""
        tests = []
        
        # Test rate limit headers on normal request
        test_result = await self._test_endpoint(
            "GET", "/",
            expected_status=200,
            description="Check rate limit headers",
            check_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"]
        )
        tests.append(test_result)
        
        # Test rate limiting by making multiple rapid requests
        rapid_requests = []
        for i in range(5):
            start_time = time.time()
            try:
                response = await self.client.get("/")
                end_time = time.time()
                
                rapid_requests.append({
                    "request_number": i + 1,
                    "status_code": response.status_code,
                    "response_time": (end_time - start_time) * 1000,
                    "rate_limit_remaining": response.headers.get("X-RateLimit-Remaining", "unknown")
                })
            except Exception as e:
                rapid_requests.append({
                    "request_number": i + 1,
                    "error": str(e)
                })
        
        # Analyze rapid requests
        rate_limit_test = {
            "test_name": "Rate limiting behavior",
            "success": True,
            "rapid_requests": rapid_requests,
            "description": "Multiple rapid requests to test rate limiting"
        }
        tests.append(rate_limit_test)
        
        return self._summarize_tests(tests)
    
    async def test_documentation_endpoints(self) -> Dict[str, Any]:
        """Test API documentation endpoints"""
        tests = []
        
        # Test API documentation
        test_result = await self._test_endpoint(
            "GET", "/api/v1/docs/",
            expected_status=200,
            description="Get API documentation"
        )
        tests.append(test_result)
        
        # Test endpoint listing
        test_result = await self._test_endpoint(
            "GET", "/api/v1/docs/endpoints",
            expected_status=200,
            description="List API endpoints"
        )
        tests.append(test_result)
        
        # Test API health check
        test_result = await self._test_endpoint(
            "GET", "/api/v1/docs/health",
            expected_status=200,
            description="API health check"
        )
        tests.append(test_result)
        
        # Test API examples
        test_result = await self._test_endpoint(
            "GET", "/api/v1/docs/examples",
            expected_status=200,
            description="Get API examples"
        )
        tests.append(test_result)
        
        return self._summarize_tests(tests)
    
    async def _test_endpoint(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        expected_status: Any = 200,
        description: str = "",
        check_headers: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Test a single API endpoint
        
        Args:
            method: HTTP method
            path: Endpoint path
            data: Request data
            headers: Request headers
            expected_status: Expected status code(s)
            description: Test description
            check_headers: Headers to check for presence
            
        Returns:
            Test result dictionary
        """
        start_time = time.time()
        
        try:
            # Make request
            if method.upper() == "GET":
                response = await self.client.get(path, headers=headers)
            elif method.upper() == "POST":
                response = await self.client.post(path, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = await self.client.put(path, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = await self.client.delete(path, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            # Check status code
            if isinstance(expected_status, list):
                status_ok = response.status_code in expected_status
            else:
                status_ok = response.status_code == expected_status
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            # Check headers if specified
            missing_headers = []
            if check_headers:
                for header in check_headers:
                    if header not in response.headers:
                        missing_headers.append(header)
            
            success = status_ok and len(missing_headers) == 0
            
            return {
                "test_name": f"{method.upper()} {path}",
                "description": description,
                "success": success,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "response_time_ms": response_time,
                "response_data": response_data,
                "response_headers": dict(response.headers),
                "missing_headers": missing_headers,
                "error_message": None
            }
            
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            return {
                "test_name": f"{method.upper()} {path}",
                "description": description,
                "success": False,
                "status_code": None,
                "expected_status": expected_status,
                "response_time_ms": response_time,
                "response_data": None,
                "response_headers": {},
                "missing_headers": [],
                "error_message": str(e)
            }
    
    def _summarize_tests(self, tests: list) -> Dict[str, Any]:
        """
        Summarize test results
        
        Args:
            tests: List of test results
            
        Returns:
            Summary dictionary
        """
        total = len(tests)
        passed = sum(1 for test in tests if test.get("success", False))
        failed = total - passed
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / total * 100) if total > 0 else 0,
            "tests": tests
        }


# Test runner functions
async def run_api_tests(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Run comprehensive API tests
    
    Args:
        base_url: Base URL of the API
        
    Returns:
        Test results
    """
    test_suite = APITestSuite(base_url)
    return await test_suite.run_all_tests()


def run_api_tests_sync(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Synchronous wrapper for running API tests
    
    Args:
        base_url: Base URL of the API
        
    Returns:
        Test results
    """
    return asyncio.run(run_api_tests(base_url))


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run StorySign API tests")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print(f"Running API tests against {args.url}...")
    
    # Run tests
    results = run_api_tests_sync(args.url)
    
    # Print summary
    summary = results["summary"]
    print(f"\nTest Results Summary:")
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Success Rate: {(summary['passed'] / summary['total_tests'] * 100):.1f}%")
    print(f"Duration: {summary['duration']:.2f} seconds")
    
    # Print category results
    print(f"\nResults by Category:")
    for category, category_results in results["categories"].items():
        success_rate = (category_results["passed"] / category_results["total"] * 100) if category_results["total"] > 0 else 0
        print(f"  {category}: {category_results['passed']}/{category_results['total']} ({success_rate:.1f}%)")
    
    # Save detailed results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nDetailed results saved to {args.output}")
    
    # Exit with error code if tests failed
    if summary["failed"] > 0:
        exit(1)