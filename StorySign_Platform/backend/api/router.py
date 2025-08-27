"""
Main API router that combines all module-specific routers
"""

from fastapi import APIRouter

from . import (
    system, asl_world, harmony, reconnect, websocket, services_demo, 
    collaborative, collaborative_websocket, plugins, analytics_simple, 
    research, content, social, group_management,
    auth, users, documentation
)
from .graphql_endpoint import graphql_app

# Create main API router
api_router = APIRouter()

# Include authentication and user management routers
api_router.include_router(auth.router)
api_router.include_router(users.router)

# Include system and core routers
api_router.include_router(system.router)
api_router.include_router(documentation.router)

# Include module-specific routers
api_router.include_router(asl_world.router)
api_router.include_router(harmony.router)
api_router.include_router(reconnect.router)
api_router.include_router(websocket.router)
api_router.include_router(services_demo.router)

# Include feature routers
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(collaborative.router, prefix="/collaborative", tags=["collaborative"])
api_router.include_router(collaborative_websocket.router, prefix="/collaborative", tags=["collaborative-websocket"])
api_router.include_router(social.router, prefix="/social", tags=["social"])
api_router.include_router(group_management.router, prefix="/groups", tags=["group-management"])
api_router.include_router(plugins.router, prefix="/plugins", tags=["plugins"])
api_router.include_router(analytics_simple.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(research.router, prefix="/research", tags=["research"])

# Include GraphQL router
api_router.include_router(graphql_app, prefix="", tags=["graphql"])