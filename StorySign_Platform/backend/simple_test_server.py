#!/usr/bin/env python3
"""
Simple test server to verify Groq vision integration
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="StorySign Vision Test API",
    description="Simple API to test Groq vision integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class StoryGenerationRequest(BaseModel):
    frame_data: str
    custom_prompt: Optional[str] = None

# Response models
class StoryResponse(BaseModel):
    success: bool
    identified_object: Optional[str] = None
    story: Optional[dict] = None
    processing_time_ms: Optional[float] = None
    error_message: Optional[str] = None

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "StorySign Vision Test API",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "story_generation": "/api/v1/story/recognize_and_generate"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from config import get_config
        config = get_config()
        
        # Check Groq configuration
        groq_status = "configured" if config.groq.is_configured() else "not_configured"
        
        # Check vision service
        vision_status = "unknown"
        try:
            from local_vision_service import get_vision_service
            vision_service = await get_vision_service()
            is_healthy = await vision_service.check_health()
            vision_status = "healthy" if is_healthy else "unhealthy"
        except Exception as e:
            vision_status = f"error: {str(e)[:50]}"
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "groq_api": groq_status,
                "vision_service": vision_status
            },
            "configuration": {
                "service_type": config.local_vision.service_type,
                "model_name": config.local_vision.model_name,
                "groq_enabled": config.groq.enabled
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.post("/api/v1/story/recognize_and_generate")
async def recognize_and_generate_story(request: StoryGenerationRequest) -> StoryResponse:
    """
    Recognize object in image and generate a story
    """
    start_time = asyncio.get_event_loop().time()
    
    try:
        logger.info("🔍 Starting object recognition and story generation...")
        
        # Import services
        from local_vision_service import get_vision_service
        from config import get_config
        
        config = get_config()
        
        # Get vision service
        vision_service = await get_vision_service()
        
        # Check if service is healthy
        if not await vision_service.check_health():
            raise HTTPException(
                status_code=503,
                detail="Vision service is not available"
            )
        
        # Identify object in the image
        logger.info("🎯 Identifying object in image...")
        vision_result = await vision_service.identify_object(
            request.frame_data,
            request.custom_prompt
        )
        
        if not vision_result.success:
            raise HTTPException(
                status_code=400,
                detail=f"Object identification failed: {vision_result.error_message}"
            )
        
        identified_object = vision_result.object_name
        logger.info(f"✅ Object identified: '{identified_object}'")
        
        # Generate a simple story (for now, just create a basic story structure)
        story = {
            "title": f"The Story of the {identified_object.title()}",
            "sentences": [
                f"Once upon a time, there was a beautiful {identified_object}.",
                f"The {identified_object} lived in a magical place where anything could happen.",
                f"One day, the {identified_object} decided to go on an amazing adventure.",
                f"Along the way, the {identified_object} met many friendly creatures.",
                f"Together, they learned the importance of friendship and kindness.",
                f"And they all lived happily ever after."
            ],
            "difficulty": "beginner",
            "estimated_duration_minutes": 5
        }
        
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        logger.info(f"✅ Story generation completed in {processing_time:.1f}ms")
        
        return StoryResponse(
            success=True,
            identified_object=identified_object,
            story=story,
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        logger.error(f"❌ Story generation failed: {e}")
        
        return StoryResponse(
            success=False,
            error_message=str(e),
            processing_time_ms=processing_time
        )

if __name__ == "__main__":
    logger.info("🚀 Starting StorySign Vision Test Server...")
    
    uvicorn.run(
        "simple_test_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )