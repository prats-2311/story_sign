"""
Main API router that combines all module-specific routers
"""

from fastapi import APIRouter

from . import system, asl_world, harmony, reconnect, websocket, services_demo, collaborative, plugins

# Create main API router
api_router = APIRouter()

# Include all module routers
api_router.include_router(system.router)
api_router.include_router(asl_world.router)
api_router.include_router(harmony.router)
api_router.include_router(reconnect.router)
api_router.include_router(websocket.router)
api_router.include_router(services_demo.router)
api_router.include_router(collaborative.router, prefix="/collaborative", tags=["collaborative"])
api_router.include_router(plugins.router, prefix="/plugins", tags=["plugins"])