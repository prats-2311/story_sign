#!/usr/bin/env python3
"""
Local Vision Service for StorySign ASL Platform
Handles object identification using local vision models via Ollama or LM Studio
"""

import base64
import json
import logging
import asyncio
import aiohttp
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from config import get_config

logger = logging.getLogger(__name__)


@dataclass
class VisionResult:
    """Result from vision model object identification"""
    success: bool
    object_name: Optional[str] = None
    confidence: Optional[float] = None
    error_message: Optional[str] = None
    processing_time_ms: Optional[float] = None


class LocalVisionService:
    """Service for communicating with local vision models"""

    def __init__(self):
        """Initialize the local vision service"""
        self.config = get_config().local_vision
        self.session: Optional[aiohttp.ClientSession] = None
        self._health_status = False

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()

    async def initialize(self):
        """Initialize the service and create HTTP session"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            self.session = aiohttp.ClientSession(timeout=timeout)
            logger.info(f"Initialized local vision service with URL: {self.config.service_url}")

            # Check service health on initialization
            await self.check_health()

    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Local vision service session closed")

    async def check_health(self) -> bool:
        """
        Check if the local vision service is available and healthy

        Returns:
            bool: True if service is healthy, False otherwise
        """
        if not self.config.enabled:
            logger.info("Local vision service is disabled in configuration")
            self._health_status = False
            return False

        if not self.session:
            await self.initialize()

        try:
            if self.config.service_type == "groq":
                # Check Groq API configuration and connectivity
                groq_config = get_config().groq
                
                if not groq_config.is_configured():
                    self._health_status = False
                    logger.warning("Groq API is not properly configured (missing API key or disabled)")
                    return False

                # Test Groq API with a simple models request
                timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout for Groq health check
                headers = {
                    "Authorization": f"Bearer {groq_config.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with self.session.get(
                    f"{groq_config.base_url}/models", 
                    headers=headers, 
                    timeout=timeout
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model.get('id', '') for model in data.get('data', [])]
                        
                        # Check if our configured model is available
                        model_available = any(groq_config.model_name in model for model in models)
                        
                        if model_available:
                            self._health_status = True
                            logger.info(f"Groq API is healthy, model '{groq_config.model_name}' is available")
                            return True
                        else:
                            self._health_status = False
                            logger.warning(f"Model '{groq_config.model_name}' not found in available Groq models: {models}")
                            return False
                    else:
                        self._health_status = False
                        logger.warning(f"Groq API health check failed with status: {response.status}")
                        return False

            elif self.config.service_type == "ollama":
                # Check Ollama API with timeout
                timeout = aiohttp.ClientTimeout(total=5)  # 5 second timeout for health check
                async with self.session.get(f"{self.config.service_url}/api/tags", timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model.get('name', '') for model in data.get('models', [])]

                        # Check if our configured model is available
                        model_available = any(self.config.model_name in model for model in models)

                        if model_available:
                            self._health_status = True
                            logger.info(f"Ollama service is healthy, model '{self.config.model_name}' is available")
                            return True
                        else:
                            self._health_status = False
                            logger.warning(f"Model '{self.config.model_name}' not found in available models: {models}")
                            return False
                    else:
                        self._health_status = False
                        logger.warning(f"Ollama service health check failed with status: {response.status}")
                        return False

            elif self.config.service_type == "lm_studio":
                # Check LM Studio API with timeout
                timeout = aiohttp.ClientTimeout(total=5)  # 5 second timeout for health check
                async with self.session.get(f"{self.config.service_url}/v1/models", timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model.get('id', '') for model in data.get('data', [])]

                        # Check if our configured model is available
                        model_available = any(self.config.model_name in model for model in models)

                        if model_available:
                            self._health_status = True
                            logger.info(f"LM Studio service is healthy, model '{self.config.model_name}' is available")
                            return True
                        else:
                            self._health_status = False
                            logger.warning(f"Model '{self.config.model_name}' not found in available models: {models}")
                            return False
                    else:
                        self._health_status = False
                        logger.warning(f"LM Studio service health check failed with status: {response.status}")
                        return False

            else:
                self._health_status = False
                logger.error(f"Unknown service type: {self.config.service_type}")
                return False

        except asyncio.TimeoutError:
            self._health_status = False
            logger.warning(f"Vision service health check timed out for {self.config.service_url}")
            return False
        except aiohttp.ClientConnectorError as e:
            self._health_status = False
            logger.warning(f"Vision service connection failed: {e}. Service may not be running")
            return False
        except Exception as e:
            self._health_status = False
            logger.error(f"Vision service health check failed: {e}")
            return False

    def is_healthy(self) -> bool:
        """
        Get current health status without making a network call

        Returns:
            bool: Current health status
        """
        return self._health_status

    def _validate_identification_input(self, base64_image: str, custom_prompt: Optional[str]) -> Dict[str, Any]:
        """
        Enhanced validation of identification input parameters

        Args:
            base64_image: Base64 encoded image data
            custom_prompt: Optional custom prompt

        Returns:
            Dict with validation result
        """
        try:
            # Check if image data is provided
            if not base64_image:
                return {"valid": False, "error": "No image data provided"}

            if not base64_image.strip():
                return {"valid": False, "error": "Empty image data provided"}

            # Validate custom prompt if provided
            if custom_prompt:
                if len(custom_prompt) > 1000:
                    return {"valid": False, "error": "Custom prompt too long (maximum 1000 characters)"}

                # Check for potentially problematic content
                problematic_terms = ["ignore", "system", "prompt", "instruction", "override"]
                if any(term in custom_prompt.lower() for term in problematic_terms):
                    return {"valid": False, "error": "Custom prompt contains potentially problematic content"}

            # Validate base64 image format and content
            validation_result = self._validate_base64_image(base64_image)
            if not validation_result["valid"]:
                return {"valid": False, "error": validation_result["error"]}

            return {"valid": True, "error": None}

        except Exception as e:
            logger.error(f"Input validation error: {e}")
            return {"valid": False, "error": f"Input validation failed: {str(e)}"}

    def _validate_base64_image(self, base64_data: str) -> Dict[str, Any]:
        """
        Enhanced validation of base64 image data

        Args:
            base64_data: Base64 encoded image string

        Returns:
            Dict with validation result and details
        """
        try:
            # Remove data URL prefix if present
            clean_data = base64_data
            if clean_data.startswith('data:image/'):
                clean_data = clean_data.split(',', 1)[1]

            # Check base64 format
            if not clean_data:
                return {"valid": False, "error": "Empty base64 data after cleaning"}

            # Try to decode base64 data
            try:
                decoded = base64.b64decode(clean_data)
            except Exception as e:
                return {"valid": False, "error": f"Invalid base64 encoding: {str(e)}"}

            # Check size constraints
            if len(decoded) < 500:  # Too small to be a real image
                return {"valid": False, "error": f"Image data too small ({len(decoded)} bytes, minimum 500)"}

            if len(decoded) > 20 * 1024 * 1024:  # 20MB limit
                return {"valid": False, "error": f"Image data too large ({len(decoded)} bytes, maximum 20MB)"}

            # Check for common image file signatures
            image_signatures = [
                (b'\xff\xd8\xff', "JPEG"),
                (b'\x89PNG\r\n\x1a\n', "PNG"),
                (b'GIF87a', "GIF87a"),
                (b'GIF89a', "GIF89a"),
                (b'RIFF', "WebP"),  # WebP starts with RIFF
            ]

            detected_format = None
            for signature, format_name in image_signatures:
                if decoded.startswith(signature):
                    detected_format = format_name
                    break

            if not detected_format:
                return {"valid": False, "error": "Unrecognized image format (not JPEG, PNG, GIF, or WebP)"}

            return {"valid": True, "error": None, "format": detected_format, "size_bytes": len(decoded)}

        except Exception as e:
            logger.error(f"Base64 image validation failed: {e}")
            return {"valid": False, "error": f"Image validation error: {str(e)}"}

    def _validate_object_identification(self, object_name: str, confidence: Optional[float]) -> Dict[str, Any]:
        """
        Validate the quality of object identification result

        Args:
            object_name: Identified object name
            confidence: Confidence score

        Returns:
            Dict with validation result
        """
        try:
            if not object_name:
                return {"valid": False, "reason": "Empty object name"}

            # Clean and check object name
            clean_name = object_name.strip().lower()

            if len(clean_name) < 2:
                return {"valid": False, "reason": f"Object name too short: '{clean_name}'"}

            if len(clean_name) > 100:
                return {"valid": False, "reason": f"Object name too long: '{clean_name[:50]}...'"}

            # Check for reasonable content
            if clean_name.isdigit():
                return {"valid": False, "reason": "Object name is only numbers"}

            # Check for repeated characters (sign of poor generation)
            if len(set(clean_name.replace(' ', ''))) < 3:
                return {"valid": False, "reason": "Object name has too few unique characters"}

            # Check confidence if provided
            if confidence is not None:
                if confidence < 0.1:
                    return {"valid": False, "reason": f"Confidence too low: {confidence:.2f}"}
                elif confidence < 0.3:
                    return {"valid": False, "reason": f"Confidence below threshold: {confidence:.2f}"}

            # Check for common problematic responses
            problematic_responses = [
                "unknown", "unclear", "cannot", "unable", "error", "failed",
                "not sure", "maybe", "possibly", "might be", "could be",
                "i see", "this is", "appears to be", "looks like"
            ]

            if any(problem in clean_name for problem in problematic_responses):
                return {"valid": False, "reason": f"Object name contains uncertain language: '{clean_name}'"}

            # Check for reasonable word count (1-4 words is good for objects)
            words = clean_name.split()
            if len(words) > 5:
                return {"valid": False, "reason": f"Object name too verbose ({len(words)} words): '{clean_name}'"}

            return {"valid": True, "reason": "Object identification validation passed"}

        except Exception as e:
            logger.error(f"Object validation error: {e}")
            return {"valid": False, "reason": f"Validation error: {str(e)}"}

    def _prepare_vision_prompt(self, custom_prompt: Optional[str] = None) -> str:
        """
        Prepare the prompt for vision model

        Args:
            custom_prompt: Optional custom prompt, uses default if None

        Returns:
            str: Formatted prompt for the vision model
        """
        if custom_prompt:
            return custom_prompt

        return (
            "Look at this image and identify the main object or item that is most prominent. "
            "Respond with just the name of the object in 1-3 words. "
            "For example: 'red ball', 'coffee cup', 'book', 'flower', 'car', etc. "
            "Focus on concrete, physical objects that would be good for storytelling."
        )

    async def _make_vision_request(self, base64_image: str, prompt: str) -> Dict[str, Any]:
        """
        Make a request to the vision model (local or cloud)

        Args:
            base64_image: Base64 encoded image data
            prompt: Prompt for the vision model

        Returns:
            Dict containing the response from the vision model

        Raises:
            aiohttp.ClientError: If the request fails
        """
        if not self.session:
            await self.initialize()

        if self.config.service_type == "groq":
            # Use Groq API configuration
            groq_config = get_config().groq
            
            if not groq_config.is_configured():
                raise ValueError("Groq API is not properly configured")

            headers = {
                "Authorization": f"Bearer {groq_config.api_key}",
                "Content-Type": "application/json"
            }

            # Prepare the request payload for Groq Vision API (OpenAI-compatible)
            payload = {
                "model": groq_config.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                "temperature": groq_config.temperature,
                "max_tokens": groq_config.max_tokens,
                "stream": False
            }

            async with self.session.post(
                f"{groq_config.base_url}/chat/completions",
                json=payload,
                headers=headers
            ) as response:
                if response.status == 429:
                    # Rate limiting - raise specific error for retry logic
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=429,
                        message="Rate limited by Groq API"
                    )
                response.raise_for_status()
                return await response.json()

        elif self.config.service_type == "ollama":
            headers = {
                "Content-Type": "application/json"
            }

            # Prepare the request payload for Ollama API
            payload = {
                "model": self.config.model_name,
                "prompt": prompt,
                "images": [base64_image],
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for consistent object identification
                    "top_p": 0.9,
                    "num_predict": 50,  # Limit response length
                }
            }

            async with self.session.post(
                f"{self.config.service_url}/api/generate",
                json=payload,
                headers=headers
            ) as response:
                response.raise_for_status()
                return await response.json()

        elif self.config.service_type == "lm_studio":
            headers = {
                "Content-Type": "application/json"
            }

            # Prepare the request payload for LM Studio OpenAI-compatible API with vision content
            # Send both the prompt text and the base64 image as a data URL in the content array
            payload = {
                "model": self.config.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 50,
                "stream": False
            }

            async with self.session.post(
                f"{self.config.service_url}/v1/chat/completions",
                json=payload,
                headers=headers
            ) as response:
                response.raise_for_status()
                return await response.json()

        else:
            raise ValueError(f"Unsupported service type: {self.config.service_type}")

    def _parse_vision_response(self, response_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[float]]:
        """
        Parse the response from the vision model to extract object name

        Args:
            response_data: Raw response from the vision model

        Returns:
            Tuple of (object_name, confidence_score)
        """
        try:
            # Extract the response text based on service type
            response_text = ""

            if self.config.service_type == "groq":
                # Parse Groq API response (OpenAI-compatible format)
                choices = response_data.get('choices', [])
                if choices:
                    message = choices[0].get('message', {})
                    response_text = message.get('content', '').strip()
            elif self.config.service_type == "ollama":
                response_text = response_data.get('response', '').strip()
            elif self.config.service_type == "lm_studio":
                choices = response_data.get('choices', [])
                if choices:
                    message = choices[0].get('message', {})
                    response_text = message.get('content', '').strip()

            if not response_text:
                logger.warning("Empty response from vision model")
                return None, None

            # Clean up the response - remove common prefixes and suffixes
            response_text = response_text.lower()

            # Remove common response patterns
            prefixes_to_remove = [
                "i can see", "i see", "this is", "the image shows",
                "in the image", "the main object is", "the object is",
                "this appears to be", "it looks like", "there is",
                "some common objects", "common objects include"
            ]

            for prefix in prefixes_to_remove:
                if response_text.startswith(prefix):
                    response_text = response_text[len(prefix):].strip()

            # Remove articles and common words
            words_to_remove = ["a", "an", "the", "for", "storytelling", "purposes", "might", "be", "on", "table", "this"]
            words = response_text.split()
            filtered_words = [word.strip('.,!?:;') for word in words if word.strip('.,!?:;') not in words_to_remove]

            if filtered_words:
                object_name = " ".join(filtered_words[:3])  # Limit to 3 words max

                # Confidence scoring based on service type and response characteristics
                if self.config.service_type == "groq":
                    # Groq has high-quality vision models, start with higher confidence
                    confidence = 0.85
                    
                    # Check for uncertain language first (before filtering)
                    if any(word in response_text for word in ["maybe", "possibly", "might", "unclear"]):
                        confidence = 0.6  # Uncertain language reduces confidence
                    elif len(words) > 5:
                        confidence = 0.6  # Verbose responses are less confident
                    elif len(filtered_words) <= 2:
                        confidence = 0.9  # Short, clear responses are very confident
                else:
                    # Default confidence for local models
                    confidence = 0.7
                    
                    # Increase confidence for short, clear responses
                    if len(filtered_words) <= 2:
                        confidence = 0.8

                    # Decrease confidence for very long or uncertain responses
                    if len(words) > 5 or any(word in response_text for word in ["maybe", "possibly", "might", "unclear"]):
                        confidence = 0.5

                logger.info(f"Parsed object name: '{object_name}' with confidence: {confidence} (service: {self.config.service_type})")
                return object_name, confidence

            logger.warning(f"Could not parse object name from response: {response_text}")
            return None, None

        except Exception as e:
            logger.error(f"Error parsing vision response: {e}")
            return None, None

    async def identify_object(self, base64_image: str, custom_prompt: Optional[str] = None) -> VisionResult:
        """
        Identify the main object in a base64 encoded image with enhanced validation and error handling

        Args:
            base64_image: Base64 encoded image data
            custom_prompt: Optional custom prompt for the vision model

        Returns:
            VisionResult: Object identification result with detailed error information
        """
        start_time = asyncio.get_event_loop().time()

        # Check if service is enabled
        if not self.config.enabled:
            return VisionResult(
                success=False,
                error_message="Local vision service is disabled in configuration"
            )

        # Enhanced input validation
        validation_result = self._validate_identification_input(base64_image, custom_prompt)
        if not validation_result["valid"]:
            return VisionResult(
                success=False,
                error_message=validation_result["error"],
                processing_time_ms=(asyncio.get_event_loop().time() - start_time) * 1000
            )

        # Clean base64 data (remove data URL prefix if present)
        clean_image_data = base64_image
        if clean_image_data.startswith('data:image/'):
            clean_image_data = clean_image_data.split(',', 1)[1]

        # Enhanced service health check with retry
        health_check_attempts = 2
        service_healthy = False

        for health_attempt in range(health_check_attempts):
            service_healthy = await self.check_health()
            if service_healthy:
                break
            elif health_attempt < health_check_attempts - 1:
                logger.info(f"Service health check failed, retrying in 2 seconds...")
                await asyncio.sleep(2)

        if not service_healthy:
            return VisionResult(
                success=False,
                error_message=f"Local vision service is not available at {self.config.service_url}. Please check if the service is running.",
                processing_time_ms=(asyncio.get_event_loop().time() - start_time) * 1000
            )

        # Prepare prompt with validation
        prompt = self._prepare_vision_prompt(custom_prompt)

        # Enhanced identification with retries and better error handling
        last_error = None
        best_result = None

        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"Attempting object identification (attempt {attempt + 1}/{self.config.max_retries})")

                # Add timeout for individual requests
                try:
                    response_data = await asyncio.wait_for(
                        self._make_vision_request(clean_image_data, prompt),
                        timeout=self.config.timeout_seconds
                    )
                except asyncio.TimeoutError:
                    last_error = f"Vision request timed out after {self.config.timeout_seconds} seconds"
                    logger.warning(f"Vision request timeout (attempt {attempt + 1})")
                    continue

                # Parse and validate the response
                object_name, confidence = self._parse_vision_response(response_data)

                if object_name:
                    # Enhanced object name validation
                    validation_result = self._validate_object_identification(object_name, confidence)

                    if validation_result["valid"]:
                        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000

                        logger.info(f"Object successfully identified: '{object_name}' (confidence: {confidence:.2f})")

                        return VisionResult(
                            success=True,
                            object_name=object_name,
                            confidence=confidence,
                            processing_time_ms=processing_time
                        )
                    else:
                        # Keep track of best result even if not perfect
                        if not best_result or (confidence and confidence > best_result.get("confidence", 0)):
                            best_result = {
                                "object_name": object_name,
                                "confidence": confidence,
                                "validation_issue": validation_result["reason"]
                            }

                        last_error = f"Object identification validation failed: {validation_result['reason']}"
                        logger.warning(f"Validation failed for '{object_name}': {validation_result['reason']}")
                else:
                    last_error = "Could not parse object name from vision model response"

            except aiohttp.ClientResponseError as e:
                if e.status == 429:
                    # Rate limiting - use longer backoff for Groq API
                    last_error = f"Rate limited by API (status 429)"
                    logger.warning(f"Rate limited (attempt {attempt + 1}): {last_error}")
                    
                    # Longer wait for rate limiting
                    if attempt < self.config.max_retries - 1:
                        wait_time = min(30 + (2 ** attempt), 120)  # 30s base + exponential, cap at 2 minutes
                        logger.info(f"Rate limited, waiting {wait_time}s before retry...")
                        await asyncio.sleep(wait_time)
                        continue
                elif e.status == 401:
                    last_error = f"Authentication failed (status 401) - check API key"
                    logger.error(f"Authentication failed: {last_error}")
                    break  # Don't retry authentication errors
                elif e.status == 403:
                    last_error = f"Access forbidden (status 403) - check API permissions"
                    logger.error(f"Access forbidden: {last_error}")
                    break  # Don't retry permission errors
                else:
                    last_error = f"HTTP error {e.status}: {e.message}"
                    logger.warning(f"HTTP error (attempt {attempt + 1}): {last_error}")

            except aiohttp.ClientError as e:
                last_error = f"Network error: {e}"
                logger.warning(f"Vision request failed (attempt {attempt + 1}): {last_error}")

            except Exception as e:
                last_error = f"Unexpected error: {e}"
                logger.error(f"Unexpected error during vision request (attempt {attempt + 1}): {last_error}", exc_info=True)

                # For unexpected errors, don't retry
                break

            # Wait before retry with exponential backoff (if not already handled above)
            if attempt < self.config.max_retries - 1:
                wait_time = min(2 ** attempt, 10)  # Cap at 10 seconds
                logger.info(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)

        # All attempts failed - check if we have a best result to fall back to
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000

        if best_result and best_result["confidence"] and best_result["confidence"] > 0.2:
            # Use best result with lower confidence if it's reasonable
            logger.info(f"Using best available result: '{best_result['object_name']}' "
                       f"(confidence: {best_result['confidence']:.2f}, issue: {best_result['validation_issue']})")

            return VisionResult(
                success=True,
                object_name=best_result["object_name"],
                confidence=best_result["confidence"],
                processing_time_ms=processing_time,
                error_message=f"Used best available result despite: {best_result['validation_issue']}"
            )

        # Provide detailed error message for complete failure
        error_details = []
        error_details.append(f"Failed after {self.config.max_retries} attempts")
        if last_error:
            error_details.append(f"Last error: {last_error}")
        if best_result:
            error_details.append(f"Best attempt found '{best_result['object_name']}' but {best_result['validation_issue']}")

        return VisionResult(
            success=False,
            error_message=". ".join(error_details),
            processing_time_ms=processing_time
        )

    async def get_service_status(self) -> Dict[str, Any]:
        """
        Get detailed service status information

        Returns:
            Dict containing service status details
        """
        if self.config.service_type == "groq":
            # Use Groq configuration for status
            groq_config = get_config().groq
            status = {
                "enabled": self.config.enabled and groq_config.enabled,
                "service_url": groq_config.base_url,
                "service_type": self.config.service_type,
                "model_name": groq_config.model_name,
                "healthy": False,
                "available_models": [],
                "error": None,
                "api_configured": groq_config.is_configured()
            }
        else:
            status = {
                "enabled": self.config.enabled,
                "service_url": self.config.service_url,
                "service_type": self.config.service_type,
                "model_name": self.config.model_name,
                "healthy": False,
                "available_models": [],
                "error": None
            }

        if not self.config.enabled:
            status["error"] = "Service disabled in configuration"
            return status

        try:
            if not self.session:
                await self.initialize()

            if self.config.service_type == "groq":
                groq_config = get_config().groq
                
                if not groq_config.is_configured():
                    status["error"] = "Groq API not configured (missing API key or disabled)"
                    return status

                # Get available models from Groq
                headers = {
                    "Authorization": f"Bearer {groq_config.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with self.session.get(f"{groq_config.base_url}/models", headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        status["available_models"] = [model.get('id', '') for model in data.get('data', [])]
                        status["healthy"] = any(groq_config.model_name in model for model in status["available_models"])

                        if not status["healthy"]:
                            status["error"] = f"Model '{groq_config.model_name}' not found in available Groq models"
                    elif response.status == 401:
                        status["error"] = "Groq API authentication failed - check API key"
                    elif response.status == 403:
                        status["error"] = "Groq API access forbidden - check API permissions"
                    else:
                        status["error"] = f"Groq API returned status {response.status}"

            elif self.config.service_type == "ollama":
                # Get available models from Ollama
                async with self.session.get(f"{self.config.service_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        status["available_models"] = [model.get('name', '') for model in data.get('models', [])]
                        status["healthy"] = any(self.config.model_name in model for model in status["available_models"])

                        if not status["healthy"]:
                            status["error"] = f"Model '{self.config.model_name}' not found in available models"
                    else:
                        status["error"] = f"Ollama service returned status {response.status}"

            elif self.config.service_type == "lm_studio":
                # Get available models from LM Studio
                async with self.session.get(f"{self.config.service_url}/v1/models") as response:
                    if response.status == 200:
                        data = await response.json()
                        status["available_models"] = [model.get('id', '') for model in data.get('data', [])]
                        status["healthy"] = any(self.config.model_name in model for model in status["available_models"])

                        if not status["healthy"]:
                            status["error"] = f"Model '{self.config.model_name}' not found in available models"
                    else:
                        status["error"] = f"LM Studio service returned status {response.status}"

            else:
                status["error"] = f"Unknown service type: {self.config.service_type}"

        except Exception as e:
            status["error"] = str(e)

        return status


# Global service instance
_vision_service: Optional[LocalVisionService] = None


async def get_vision_service() -> LocalVisionService:
    """
    Get or create the global vision service instance

    Returns:
        LocalVisionService: The vision service instance
    """
    global _vision_service

    if _vision_service is None:
        _vision_service = LocalVisionService()
        await _vision_service.initialize()

    return _vision_service


async def cleanup_vision_service():
    """Clean up the global vision service instance"""
    global _vision_service

    if _vision_service:
        await _vision_service.cleanup()
        _vision_service = None
