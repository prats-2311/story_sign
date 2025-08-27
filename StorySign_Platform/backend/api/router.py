"""
Main API router that combines all module-specific routers
"""

from fastapi import APIRouter

# Import core working modules
from . import system, asl_world, harmony, reconnect, websocket, services_demo

# Import new API modules (with error handling)
try:
    from . import auth, users, documentation, integrations, branding, sync
    NEW_API_AVAILABLE = True
except ImportError as e:
    print(f"Warning: New API modules not available: {e}")
    NEW_API_AVAILABLE = False

# Import existing feature modules (with error handling)
try:
    from . import collaborative, collaborative_websocket, plugins, analytics_simple, research
    FEATURE_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Some feature modules not available: {e}")
    FEATURE_MODULES_AVAILABLE = False

# Import modules with dependencies (with error handling)
try:
    from . import social, group_management
    SOCIAL_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Social modules not available: {e}")
    SOCIAL_MODULES_AVAILABLE = False

# Import GraphQL (with error handling)
try:
    from .graphql_endpoint import graphql_app
    GRAPHQL_AVAILABLE = True
except ImportError as e:
    print(f"Warning: GraphQL not available: {e}")
    GRAPHQL_AVAILABLE = False

# Create main API router
api_router = APIRouter()

# Include core system routers (always available)
api_router.include_router(system.router)
api_router.include_router(asl_world.router)
api_router.include_router(harmony.router)
api_router.include_router(reconnect.router)
api_router.include_router(websocket.router)
api_router.include_router(services_demo.router)

# Include new API modules if available
if NEW_API_AVAILABLE:
    api_router.include_router(auth.router)
    api_router.include_router(users.router)
    api_router.include_router(documentation.router)
    api_router.include_router(integrations.router, tags=["integrations"])
    api_router.include_router(branding.router, prefix="/branding", tags=["branding"])
    api_router.include_router(sync.router, prefix="/sync", tags=["synchronization"])

# Include feature modules if available
if FEATURE_MODULES_AVAILABLE:
    api_router.include_router(collaborative.router, prefix="/collaborative", tags=["collaborative"])
    api_router.include_router(collaborative_websocket.router, prefix="/collaborative", tags=["collaborative-websocket"])
    api_router.include_router(plugins.router, prefix="/plugins", tags=["plugins"])
    api_router.include_router(analytics_simple.router, prefix="/analytics", tags=["analytics"])
    api_router.include_router(research.router, prefix="/research", tags=["research"])

# Include social modules if available
if SOCIAL_MODULES_AVAILABLE:
    api_router.include_router(social.router, prefix="/social", tags=["social"])
    api_router.include_router(group_management.router, prefix="/groups", tags=["group-management"])

# Include GraphQL if available
if GRAPHQL_AVAILABLE:
    api_router.include_router(graphql_app, prefix="", tags=["graphql"])