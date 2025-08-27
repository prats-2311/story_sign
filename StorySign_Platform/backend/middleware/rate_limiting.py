"""
Rate limiting middleware for API endpoints
"""

import logging
import time
import asyncio
from typing import Dict, Optional, Callable, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class RateLimit:
    """Rate limit configuration"""
    requests: int  # Number of requests allowed
    window: int    # Time window in seconds
    burst: int     # Burst allowance


@dataclass
class RateLimitState:
    """Rate limit state for a client"""
    requests: deque
    last_request: float
    blocked_until: float = 0.0


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Advanced rate limiting middleware with multiple strategies
    """
    
    def __init__(
        self,
        app,
        default_rate_limit: Optional[RateLimit] = None,
        endpoint_limits: Optional[Dict[str, RateLimit]] = None,
        user_limits: Optional[Dict[str, RateLimit]] = None,
        ip_limits: Optional[Dict[str, RateLimit]] = None,
        cleanup_interval: int = 300  # 5 minutes
    ):
        super().__init__(app)
        
        # Default rate limits
        self.default_rate_limit = default_rate_limit or RateLimit(
            requests=100,  # 100 requests
            window=3600,   # per hour
            burst=20       # with burst of 20
        )
        
        # Endpoint-specific limits
        self.endpoint_limits = endpoint_limits or {
            "/api/v1/auth/login": RateLimit(5, 300, 2),      # 5 per 5 min, burst 2
            "/api/v1/auth/register": RateLimit(3, 3600, 1),  # 3 per hour, burst 1
            "/api/v1/auth/refresh": RateLimit(10, 300, 5),   # 10 per 5 min, burst 5
            "/api/v1/asl-world/story/recognize_and_generate": RateLimit(20, 3600, 5),  # 20 per hour
            "/api/v1/graphql": RateLimit(200, 3600, 50),     # 200 per hour, burst 50
        }
        
        # User-specific limits (by role)
        self.user_limits = user_limits or {
            "admin": RateLimit(1000, 3600, 100),    # Admins get higher limits
            "educator": RateLimit(500, 3600, 50),   # Educators get moderate limits
            "learner": RateLimit(200, 3600, 30),    # Learners get standard limits
            "guest": RateLimit(50, 3600, 10),       # Guests get lower limits
        }
        
        # IP-specific limits
        self.ip_limits = ip_limits or {}
        
        # State storage
        self.client_states: Dict[str, RateLimitState] = {}
        self.blocked_ips: Dict[str, float] = {}  # IP -> blocked_until timestamp
        
        # Cleanup
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = time.time()
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "rate_limited_ips": set(),
            "rate_limited_users": set()
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through rate limiting middleware
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response from next handler or rate limit error
        """
        start_time = time.time()
        
        try:
            # Update statistics
            self.stats["total_requests"] += 1
            
            # Periodic cleanup
            await self._cleanup_if_needed()
            
            # Get client identifier
            client_id = self._get_client_identifier(request)
            
            # Check if IP is blocked
            if self._is_ip_blocked(request):
                self.stats["blocked_requests"] += 1
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "ip_blocked",
                        "message": "IP address is temporarily blocked due to rate limit violations",
                        "retry_after": self._get_ip_block_retry_after(request)
                    }
                )
            
            # Get applicable rate limit
            rate_limit = self._get_rate_limit(request)
            
            # Check rate limit
            allowed, retry_after = await self._check_rate_limit(client_id, rate_limit)
            
            if not allowed:
                self.stats["blocked_requests"] += 1
                
                # Track rate limited clients
                if hasattr(request.state, 'current_user') and request.state.current_user:
                    self.stats["rate_limited_users"].add(request.state.current_user.id)
                
                client_ip = self._get_client_ip(request)
                if client_ip:
                    self.stats["rate_limited_ips"].add(client_ip)
                
                # Consider blocking IP for repeated violations
                await self._consider_ip_blocking(request)
                
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "rate_limit_exceeded",
                        "message": f"Rate limit exceeded: {rate_limit.requests} requests per {rate_limit.window} seconds",
                        "retry_after": retry_after,
                        "limit": rate_limit.requests,
                        "window": rate_limit.window
                    }
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            remaining = await self._get_remaining_requests(client_id, rate_limit)
            response.headers["X-RateLimit-Limit"] = str(rate_limit.requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + rate_limit.window))
            response.headers["X-RateLimit-Window"] = str(rate_limit.window)
            
            return response
            
        except HTTPException as e:
            # Add rate limit headers to error response
            if e.status_code == 429:
                return JSONResponse(
                    status_code=429,
                    content=e.detail,
                    headers={
                        "Retry-After": str(e.detail.get("retry_after", 60)),
                        "X-RateLimit-Limit": str(self._get_rate_limit(request).requests),
                        "X-RateLimit-Remaining": "0"
                    }
                )
            raise
        except Exception as e:
            logger.error(f"Rate limiting middleware error: {e}")
            # Continue processing on middleware errors
            response = await call_next(request)
            return response
        finally:
            # Log processing time
            processing_time = time.time() - start_time
            logger.debug(f"Rate limit middleware processed {request.url.path} in {processing_time:.3f}s")
    
    def _get_client_identifier(self, request: Request) -> str:
        """
        Get unique client identifier for rate limiting
        
        Args:
            request: FastAPI request
            
        Returns:
            Unique client identifier
        """
        # Prefer user ID if authenticated
        if hasattr(request.state, 'current_user') and request.state.current_user:
            return f"user:{request.state.current_user.id}"
        
        # Fall back to IP address
        client_ip = self._get_client_ip(request)
        if client_ip:
            return f"ip:{client_ip}"
        
        # Last resort: session or random identifier
        session_id = request.headers.get("X-Session-ID", "anonymous")
        return f"session:{session_id}"
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """
        Get client IP address from request
        
        Args:
            request: FastAPI request
            
        Returns:
            Client IP address or None
        """
        # Check for forwarded headers (load balancer/proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Direct connection
        if request.client:
            return request.client.host
        
        return None
    
    def _get_rate_limit(self, request: Request) -> RateLimit:
        """
        Get applicable rate limit for request
        
        Args:
            request: FastAPI request
            
        Returns:
            Applicable rate limit configuration
        """
        # Check endpoint-specific limits first
        path = request.url.path
        for endpoint_pattern, limit in self.endpoint_limits.items():
            if path.startswith(endpoint_pattern):
                return limit
        
        # Check user role limits
        if hasattr(request.state, 'current_user') and request.state.current_user:
            user_role = getattr(request.state.current_user, 'role', 'learner')
            if user_role in self.user_limits:
                return self.user_limits[user_role]
        
        # Check IP-specific limits
        client_ip = self._get_client_ip(request)
        if client_ip and client_ip in self.ip_limits:
            return self.ip_limits[client_ip]
        
        # Return default limit
        return self.default_rate_limit
    
    async def _check_rate_limit(self, client_id: str, rate_limit: RateLimit) -> Tuple[bool, int]:
        """
        Check if request is within rate limit
        
        Args:
            client_id: Client identifier
            rate_limit: Rate limit configuration
            
        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        current_time = time.time()
        
        # Get or create client state
        if client_id not in self.client_states:
            self.client_states[client_id] = RateLimitState(
                requests=deque(),
                last_request=current_time
            )
        
        state = self.client_states[client_id]
        
        # Check if client is currently blocked
        if state.blocked_until > current_time:
            return False, int(state.blocked_until - current_time)
        
        # Clean old requests outside the window
        window_start = current_time - rate_limit.window
        while state.requests and state.requests[0] < window_start:
            state.requests.popleft()
        
        # Check burst limit (requests in last minute)
        burst_window_start = current_time - 60  # 1 minute burst window
        recent_requests = sum(1 for req_time in state.requests if req_time > burst_window_start)
        
        if recent_requests >= rate_limit.burst:
            # Block for burst cooldown
            state.blocked_until = current_time + 60  # 1 minute cooldown
            return False, 60
        
        # Check window limit
        if len(state.requests) >= rate_limit.requests:
            # Calculate retry after based on oldest request
            oldest_request = state.requests[0]
            retry_after = int(oldest_request + rate_limit.window - current_time)
            return False, max(retry_after, 1)
        
        # Allow request and record it
        state.requests.append(current_time)
        state.last_request = current_time
        
        return True, 0
    
    async def _get_remaining_requests(self, client_id: str, rate_limit: RateLimit) -> int:
        """
        Get remaining requests for client
        
        Args:
            client_id: Client identifier
            rate_limit: Rate limit configuration
            
        Returns:
            Number of remaining requests
        """
        if client_id not in self.client_states:
            return rate_limit.requests
        
        state = self.client_states[client_id]
        current_time = time.time()
        window_start = current_time - rate_limit.window
        
        # Count requests in current window
        current_requests = sum(1 for req_time in state.requests if req_time > window_start)
        
        return max(0, rate_limit.requests - current_requests)
    
    def _is_ip_blocked(self, request: Request) -> bool:
        """
        Check if IP is currently blocked
        
        Args:
            request: FastAPI request
            
        Returns:
            True if IP is blocked, False otherwise
        """
        client_ip = self._get_client_ip(request)
        if not client_ip:
            return False
        
        blocked_until = self.blocked_ips.get(client_ip, 0)
        return blocked_until > time.time()
    
    def _get_ip_block_retry_after(self, request: Request) -> int:
        """
        Get retry after time for blocked IP
        
        Args:
            request: FastAPI request
            
        Returns:
            Retry after seconds
        """
        client_ip = self._get_client_ip(request)
        if not client_ip:
            return 0
        
        blocked_until = self.blocked_ips.get(client_ip, 0)
        return max(0, int(blocked_until - time.time()))
    
    async def _consider_ip_blocking(self, request: Request):
        """
        Consider blocking IP for repeated rate limit violations
        
        Args:
            request: FastAPI request
        """
        client_ip = self._get_client_ip(request)
        if not client_ip:
            return
        
        # Count recent violations for this IP
        current_time = time.time()
        ip_violations = 0
        
        # Check all client states for this IP
        for client_id, state in self.client_states.items():
            if client_id.startswith(f"ip:{client_ip}"):
                # Count violations in last hour
                violations_window = current_time - 3600  # 1 hour
                violations = sum(1 for req_time in state.requests if req_time > violations_window)
                if violations > 50:  # Threshold for blocking
                    ip_violations += 1
        
        # Block IP if too many violations
        if ip_violations >= 3:  # Block after 3 violation patterns
            block_duration = 3600  # Block for 1 hour
            self.blocked_ips[client_ip] = current_time + block_duration
            logger.warning(f"Blocked IP {client_ip} for {block_duration} seconds due to rate limit violations")
    
    async def _cleanup_if_needed(self):
        """
        Perform periodic cleanup of old state data
        """
        current_time = time.time()
        
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        self.last_cleanup = current_time
        
        # Clean up old client states
        inactive_threshold = current_time - 7200  # 2 hours
        inactive_clients = [
            client_id for client_id, state in self.client_states.items()
            if state.last_request < inactive_threshold
        ]
        
        for client_id in inactive_clients:
            del self.client_states[client_id]
        
        # Clean up expired IP blocks
        expired_blocks = [
            ip for ip, blocked_until in self.blocked_ips.items()
            if blocked_until < current_time
        ]
        
        for ip in expired_blocks:
            del self.blocked_ips[ip]
        
        logger.info(f"Rate limit cleanup: removed {len(inactive_clients)} inactive clients, "
                   f"{len(expired_blocks)} expired IP blocks")
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Get rate limiting statistics
        
        Returns:
            Dictionary of statistics
        """
        current_time = time.time()
        
        return {
            "total_requests": self.stats["total_requests"],
            "blocked_requests": self.stats["blocked_requests"],
            "block_rate": (
                self.stats["blocked_requests"] / max(1, self.stats["total_requests"])
            ) * 100,
            "active_clients": len(self.client_states),
            "blocked_ips": len(self.blocked_ips),
            "rate_limited_ips_count": len(self.stats["rate_limited_ips"]),
            "rate_limited_users_count": len(self.stats["rate_limited_users"]),
            "current_time": current_time
        }
    
    def reset_client_limits(self, client_id: str) -> bool:
        """
        Reset rate limits for a specific client (admin function)
        
        Args:
            client_id: Client identifier to reset
            
        Returns:
            True if client was found and reset, False otherwise
        """
        if client_id in self.client_states:
            del self.client_states[client_id]
            return True
        return False
    
    def block_ip(self, ip_address: str, duration: int = 3600):
        """
        Manually block an IP address (admin function)
        
        Args:
            ip_address: IP address to block
            duration: Block duration in seconds
        """
        self.blocked_ips[ip_address] = time.time() + duration
        logger.info(f"Manually blocked IP {ip_address} for {duration} seconds")
    
    def unblock_ip(self, ip_address: str) -> bool:
        """
        Manually unblock an IP address (admin function)
        
        Args:
            ip_address: IP address to unblock
            
        Returns:
            True if IP was blocked and unblocked, False otherwise
        """
        if ip_address in self.blocked_ips:
            del self.blocked_ips[ip_address]
            logger.info(f"Manually unblocked IP {ip_address}")
            return True
        return False