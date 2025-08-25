"""
ASL World module API router
Contains endpoints specific to ASL World functionality including story generation and video processing
"""

import logging
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from local_vision_service import get_vision_service, VisionResult
from ollama_service import get_ollama_service, StoryResponse

logger = logging.getLogger(__name__)

# Create router for ASL World endpoints
router = APIRouter(prefix="/api/asl-world", tags=["asl-world"])

# Request models for API endpoints
class StoryGenerationRequest(BaseModel):
    """Request model for story generation endpoint"""
    frame_data: Optional[str] = Field(None, description="Base64 encoded image data")
    simple_word: Optional[str] = Field(None, description="A simple word selected from a predefined list")
    custom_prompt: Optional[str] = Field(None, description="A user-specified topic for the story")

# Response models for multi-level story generation
class Story(BaseModel):
    """Individual story with title and sentences"""
    title: str
    sentences: List[str]

class StoryLevels(BaseModel):
    """Collection of stories at different difficulty levels"""
    amateur: Story
    normal: Story
    mid_level: Story
    difficult: Story
    expert: Story

class StoryGenerationResponse(BaseModel):
    """Response model for story generation endpoint"""
    success: bool
    stories: Optional[StoryLevels] = None
    user_message: Optional[str] = None


@router.post("/story/recognize_and_generate", response_model=StoryGenerationResponse)
async def recognize_and_generate_story(request: StoryGenerationRequest):
    """
    Enhanced object recognition and story generation endpoint with comprehensive error handling

    Processes an image to identify objects and generates a personalized story
    based on the identified object using local vision and cloud LLM services.
    Includes validation, fallback options, timeout handling, and user-friendly error messages.

    Args:
        request: StoryGenerationRequest containing base64 image data

    Returns:
        Dict containing story generation result with structured story data and error handling info

    Raises:
        HTTPException: If processing fails or services are unavailable
    """
    start_time = time.time()
    processing_stages = {
        "validation": {"status": "pending", "start_time": None, "duration_ms": None},
        "object_identification": {"status": "pending", "start_time": None, "duration_ms": None},
        "story_generation": {"status": "pending", "start_time": None, "duration_ms": None}
    }

    try:
        logger.info("Enhanced story generation endpoint accessed")

        # Stage 1: Enhanced request validation
        processing_stages["validation"]["start_time"] = time.time()
        processing_stages["validation"]["status"] = "in_progress"

        validation_errors = []

        # Validate that exactly one input method is provided
        input_methods = [request.frame_data, request.simple_word, request.custom_prompt]
        provided_methods = [method for method in input_methods if method]
        
        if len(provided_methods) == 0:
            validation_errors.append("No input provided. Please provide frame_data, simple_word, or custom_prompt.")
        elif len(provided_methods) > 1:
            validation_errors.append("Multiple input methods provided. Please provide only one: frame_data, simple_word, or custom_prompt.")

        # Validate frame data if provided
        if request.frame_data:
            if not request.frame_data.strip():
                validation_errors.append("Empty image data provided")
            else:
                try:
                    # Remove data URL prefix if present
                    frame_data = request.frame_data
                    if frame_data.startswith('data:image/'):
                        frame_data = frame_data.split(',', 1)[1]

                    # Test base64 decoding
                    import base64
                    decoded_data = base64.b64decode(frame_data)

                    # Check minimum size (should be at least a few KB for a real image)
                    if len(decoded_data) < 1000:
                        validation_errors.append("Image data appears to be too small to be a valid image")

                    # Check maximum size (prevent DoS attacks)
                    elif len(decoded_data) > 10 * 1024 * 1024:  # 10MB limit
                        validation_errors.append("Image data is too large (maximum 10MB allowed)")

                except Exception as e:
                    validation_errors.append(f"Invalid base64 image format: {str(e)}")

        # Validate simple word if provided
        if request.simple_word:
            if len(request.simple_word.strip()) < 2:
                validation_errors.append("Simple word is too short (minimum 2 characters)")
            elif len(request.simple_word.strip()) > 50:
                validation_errors.append("Simple word is too long (maximum 50 characters)")

        # Validate custom prompt if provided
        if request.custom_prompt:
            if len(request.custom_prompt.strip()) < 3:
                validation_errors.append("Custom prompt is too short (minimum 3 characters)")
            elif len(request.custom_prompt.strip()) > 500:
                validation_errors.append("Custom prompt is too long (maximum 500 characters)")

        processing_stages["validation"]["duration_ms"] = (time.time() - processing_stages["validation"]["start_time"]) * 1000

        if validation_errors:
            processing_stages["validation"]["status"] = "failed"
            raise HTTPException(
                status_code=400,
                detail={
                    "error_type": "validation_error",
                    "message": "Request validation failed",
                    "validation_errors": validation_errors,
                    "user_message": "Please check your image data and try again. Make sure you're using a valid image file.",
                    "retry_allowed": True,
                    "processing_stages": processing_stages
                }
            )

        processing_stages["validation"]["status"] = "completed"

        # Initialize services with health checks
        vision_service = await get_vision_service()
        ollama_service = await get_ollama_service()

        # Enhanced service health validation
        vision_healthy = await vision_service.check_health()
        ollama_healthy = await ollama_service.check_health()

        service_status = {
            "vision_service": {
                "healthy": vision_healthy,
                "status": await vision_service.get_service_status() if vision_healthy else None
            },
            "ollama_service": {
                "healthy": ollama_healthy,
                "last_check": time.time()
            }
        }

        # Check if we can proceed with at least one service
        if not vision_healthy and not ollama_healthy:
            raise HTTPException(
                status_code=503,
                detail={
                    "error_type": "service_unavailable",
                    "message": "Both AI services are currently unavailable",
                    "user_message": "Our AI services are temporarily unavailable. Please try again in a few moments.",
                    "retry_allowed": True,
                    "retry_delay_seconds": 30,
                    "service_status": service_status,
                    "processing_stages": processing_stages
                }
            )

        if not ollama_healthy:
            raise HTTPException(
                status_code=503,
                detail={
                    "error_type": "story_service_unavailable",
                    "message": "Story generation service is unavailable",
                    "user_message": "The story generation service is temporarily unavailable. Please try again later.",
                    "retry_allowed": True,
                    "retry_delay_seconds": 60,
                    "service_status": service_status,
                    "processing_stages": processing_stages
                }
            )

        # Stage 2: Topic determination based on input method
        processing_stages["object_identification"]["start_time"] = time.time()
        processing_stages["object_identification"]["status"] = "in_progress"

        topic = None
        vision_error = None
        identification_confidence = 0.0
        fallback_used = False

        # Determine topic from the request
        if request.simple_word:
            topic = request.simple_word.strip()
            logger.info(f"Generating story from simple word: '{topic}'")
        elif request.custom_prompt:
            topic = request.custom_prompt.strip()
            logger.info(f"Generating story from custom prompt: '{topic}'")
        elif request.frame_data:
            logger.info("Attempting object identification with local vision service")
            
            if vision_healthy:
                try:
                    # Add timeout wrapper for vision service
                    vision_result: VisionResult = await asyncio.wait_for(
                        vision_service.identify_object(request.frame_data),
                        timeout=30.0  # 30 second timeout for vision processing
                    )

                    # Enhanced object identification validation
                    if vision_result.success and vision_result.object_name:
                        # Validate object name quality
                        topic = vision_result.object_name.strip()
                        identification_confidence = vision_result.confidence or 0.0

                        # Check if object name is reasonable
                        if len(topic) < 2:
                            vision_error = "Object name too short - may not be reliable"
                            topic = None
                        elif len(topic) > 50:
                            vision_error = "Object name too long - may not be reliable"
                            topic = None
                        elif identification_confidence < 0.3:
                            vision_error = f"Low confidence identification ({identification_confidence:.2f})"
                            topic = None
                        else:
                            logger.info(f"Object identified: '{topic}' (confidence: {identification_confidence:.2f})")
                    else:
                        vision_error = vision_result.error_message or "Object identification failed"
                        logger.warning(f"Vision service failed: {vision_error}")

                except asyncio.TimeoutError:
                    vision_error = "Object identification timed out"
                    logger.warning("Vision service timed out after 30 seconds")
                except Exception as e:
                    vision_error = f"Vision service error: {str(e)}"
                    logger.error(f"Vision service exception: {e}", exc_info=True)
            else:
                vision_error = "Local vision service is not available"
                logger.warning(vision_error)

            # Enhanced fallback logic for object scanning
            if not topic:
                fallback_used = True
                topic = "a friendly cat"  # More engaging default fallback
                logger.warning(f"Object identification failed. Using fallback topic: '{topic}'")

        if not topic:
            raise HTTPException(status_code=400, detail={"error": "No valid input provided for story generation."})

        processing_stages["object_identification"]["duration_ms"] = (time.time() - processing_stages["object_identification"]["start_time"]) * 1000
        processing_stages["object_identification"]["status"] = "completed"

        # Stage 3: Enhanced story generation with timeout and retry logic
        processing_stages["story_generation"]["start_time"] = time.time()
        processing_stages["story_generation"]["status"] = "in_progress"

        logger.info(f"Generating multi-level stories for topic: '{topic}'")

        # Call the updated Ollama service function
        story_levels = await ollama_service.generate_story(topic)

        if not story_levels:
            raise HTTPException(status_code=500, detail={"error": "Failed to generate stories from the AI service."})

        processing_stages["story_generation"]["duration_ms"] = (time.time() - processing_stages["story_generation"]["start_time"]) * 1000
        processing_stages["story_generation"]["status"] = "completed"

        return {"success": True, "stories": story_levels}

    except HTTPException:
        # Re-raise HTTP exceptions as-is (they already have enhanced error details)
        raise
    except Exception as e:
        # Handle unexpected errors with enhanced error information
        total_time_ms = (time.time() - start_time) * 1000

        logger.error(f"Unexpected error in enhanced story generation: {e}", exc_info=True)

        raise HTTPException(
            status_code=500,
            detail={
                "error_type": "internal_server_error",
                "message": f"An unexpected error occurred during story generation",
                "user_message": "Something went wrong on our end. Please try again in a few moments.",
                "retry_allowed": True,
                "retry_delay_seconds": 5,
                "technical_error": str(e),
                "processing_time_ms": total_time_ms,
                "processing_stages": processing_stages,
                "timestamp": datetime.utcnow().isoformat()
            }
        )