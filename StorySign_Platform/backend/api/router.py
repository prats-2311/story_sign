"""
Main API router that combines all module-specific routers
"""

from fastapi import APIRouter

from . import system, asl_world, harmony, reconnect, websocket, services_demo

# Create main API router
api_router = APIRouter()

# Include all module routers
api_router.include_router(system.router)
api_router.include_router(asl_world.router)
api_router.include_router(harmony.router)
api_router.include_router(reconnect.router)
api_router.include_router(websocket.router)
api_router.include_router(services_demo.router)