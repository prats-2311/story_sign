#!/usr/bin/env python3
"""
Ollama LLM Service Integration for StorySign ASL Platform
Provides story generation and signing analysis functionality using Ollama LLM services
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import aiohttp
from aiohttp import ClientTimeout, ClientError

from config import get_config

logger = logging.getLogger(__name__)


@dataclass
class StoryResponse:
    """Response structure for story generation"""
    success: bool
    story: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    generation_time_ms: Optional[float] = None


@dataclass
class AnalysisResponse:
    """Response structure for signing analysis"""
    success: bool
    feedback: Optional[str] = None
    confidence_score: Optional[float] = None
    suggestions: Optional[List[str]] = None
    error: Optional[str] = None
    analysis_time_ms: Optional[float] = None


class OllamaService:
    """
    Ollama LLM service integration for story generation and signing analysis
    Provides async processing to prevent blocking video stream
    """
    
    def __init__(self):
        """Initialize Ollama service with configuration"""
        self.config = get_config().ollama
        self.session: Optional[aiohttp.ClientSession] = None
        self._health_status = False
        self._last_health_check = 0
        self._health_check_interval = 30  # seconds
        
        logger.info(f"Initialized Ollama service with URL: {self.config.service_url}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()
    
    async def start(self):
        """Start the Ollama service session"""
        if self.session is None:
            timeout = ClientTimeout(total=self.config.timeout_seconds)
            self.session = aiohttp.ClientSession(timeout=timeout)
            logger.info("Ollama service session started")
    
    async def stop(self):
        """Stop the Ollama service session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Ollama service session stopped")
    
    async def _make_request(self, endpoint: str, payload: Dict[str, Any], model: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Make async request to Ollama service with retry logic
        
        Args:
            endpoint: API endpoint path
            payload: Request payload
            model: Model name to use
            
        Returns:
            Tuple of (success, response_data, error_message)
        """
        if not self.session:
            await self.start()
        
        url = f"{self.config.service_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Add model to payload
        payload["model"] = model
        
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"Making request to {url} (attempt {attempt + 1}/{self.config.max_retries})")
                
                async with self.session.post(url, json=payload) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        logger.debug(f"Successful response from {url}")
                        return True, response_data, None
                    else:
                        error_text = await response.text()
                        logger.warning(f"HTTP {response.status} from {url}: {error_text}")
                        
                        if response.status == 404:
                            return False, None, f"Model '{model}' not found. Please ensure it's installed in Ollama."
                        elif response.status >= 500:
                            # Server error, retry
                            if attempt < self.config.max_retries - 1:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                continue
                        
                        return False, None, f"HTTP {response.status}: {error_text}"
            
            except asyncio.TimeoutError:
                logger.warning(f"Timeout on request to {url} (attempt {attempt + 1})")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return False, None, f"Request timeout after {self.config.timeout_seconds} seconds"
            
            except ClientError as e:
                logger.warning(f"Client error on request to {url}: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return False, None, f"Connection error: {str(e)}"
            
            except Exception as e:
                logger.error(f"Unexpected error on request to {url}: {e}")
                return False, None, f"Unexpected error: {str(e)}"
        
        return False, None, f"Failed after {self.config.max_retries} attempts"
    
    async def check_health(self) -> bool:
        """
        Check if Ollama service is healthy and models are available
        
        Returns:
            bool: True if service is healthy
        """
        current_time = time.time()
        
        # Use cached health status if recent
        if current_time - self._last_health_check < self._health_check_interval:
            return self._health_status
        
        try:
            if not self.session:
                await self.start()
            
            # Check if service is running
            url = f"{self.config.service_url.rstrip('/')}/api/tags"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model.get('name', '') for model in data.get('models', [])]
                    
                    # Check if required models are available
                    story_model_available = any(self.config.story_model in model for model in models)
                    analysis_model_available = any(self.config.analysis_model in model for model in models)
                    
                    if not story_model_available:
                        logger.warning(f"Story model '{self.config.story_model}' not found in Ollama")
                    if not analysis_model_available:
                        logger.warning(f"Analysis model '{self.config.analysis_model}' not found in Ollama")
                    
                    self._health_status = story_model_available and analysis_model_available
                else:
                    logger.warning(f"Ollama health check failed: HTTP {response.status}")
                    self._health_status = False
        
        except Exception as e:
            logger.warning(f"Ollama health check error: {e}")
            self._health_status = False
        
        self._last_health_check = current_time
        return self._health_status
    
    async def generate_story(self, object_name: str) -> StoryResponse:
        """
        Generate a personalized story based on identified object with enhanced error handling
        
        Args:
            object_name: Name of the object identified by vision service
            
        Returns:
            StoryResponse: Story generation result with detailed error information
        """
        if not self.config.enabled:
            return StoryResponse(
                success=False,
                error="Ollama service is disabled in configuration"
            )
        
        start_time = time.time()
        
        try:
            # Validate object name
            if not object_name or not object_name.strip():
                return StoryResponse(
                    success=False,
                    error="No object name provided for story generation",
                    generation_time_ms=(time.time() - start_time) * 1000
                )
            
            # Clean and validate object name
            clean_object_name = object_name.strip().lower()
            if len(clean_object_name) > 100:
                clean_object_name = clean_object_name[:100]
                logger.warning(f"Object name truncated to 100 characters: {clean_object_name}")
            
            # Create story generation prompt
            prompt = self._create_story_prompt(clean_object_name)
            
            payload = {
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,
                    "stop": ["</story>", "\n\n---", "END_STORY"],
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }
            
            logger.info(f"Generating story for object: '{clean_object_name}'")
            
            # Enhanced request with better error handling
            success, response_data, error = await self._make_request(
                "api/generate", 
                payload, 
                self.config.story_model
            )
            
            if not success:
                # Provide more specific error messages
                if "not found" in (error or "").lower():
                    error_msg = f"Story generation model '{self.config.story_model}' is not available. Please check Ollama configuration."
                elif "timeout" in (error or "").lower():
                    error_msg = "Story generation timed out. The AI service may be overloaded."
                elif "connection" in (error or "").lower():
                    error_msg = "Cannot connect to story generation service. Please check if Ollama is running."
                else:
                    error_msg = error or "Failed to generate story"
                
                return StoryResponse(
                    success=False,
                    error=error_msg,
                    generation_time_ms=(time.time() - start_time) * 1000
                )
            
            # Enhanced story parsing with validation
            story_data = self._parse_story_response(response_data, clean_object_name)
            
            # Validate generated story quality
            validation_result = self._validate_story_quality(story_data)
            if not validation_result["valid"]:
                logger.warning(f"Generated story failed quality validation: {validation_result['reason']}")
                return StoryResponse(
                    success=False,
                    error=f"Generated story quality issue: {validation_result['reason']}",
                    generation_time_ms=(time.time() - start_time) * 1000
                )
            
            generation_time = (time.time() - start_time) * 1000
            
            logger.info(f"Story generated successfully in {generation_time:.1f}ms")
            
            return StoryResponse(
                success=True,
                story=story_data,
                generation_time_ms=generation_time
            )
        
        except asyncio.TimeoutError:
            error_msg = f"Story generation timed out after {self.config.timeout_seconds} seconds"
            logger.error(error_msg)
            return StoryResponse(
                success=False,
                error=error_msg,
                generation_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            error_msg = f"Story generation error: {str(e)}"
            logger.error(f"Error generating story: {e}", exc_info=True)
            return StoryResponse(
                success=False,
                error=error_msg,
                generation_time_ms=(time.time() - start_time) * 1000
            )
    
    async def analyze_signing_attempt(self, landmark_buffer: List[Dict], target_sentence: str) -> AnalysisResponse:
        """
        Analyze signing attempt and provide contextual feedback
        
        Args:
            landmark_buffer: List of landmark data collected during signing
            target_sentence: The sentence the user was trying to sign
            
        Returns:
            AnalysisResponse: Analysis result with feedback
        """
        if not self.config.enabled:
            return AnalysisResponse(
                success=False,
                error="Ollama service is disabled in configuration"
            )
        
        start_time = time.time()
        
        try:
            # Create analysis prompt
            prompt = self._create_analysis_prompt(landmark_buffer, target_sentence)
            
            payload = {
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more consistent analysis
                    "num_predict": min(500, self.config.max_tokens),  # Shorter responses for feedback
                    "stop": ["</analysis>", "\n\n---"]
                }
            }
            
            logger.info(f"Analyzing signing attempt for: '{target_sentence}'")
            
            success, response_data, error = await self._make_request(
                "api/generate", 
                payload, 
                self.config.analysis_model
            )
            
            if not success:
                return AnalysisResponse(
                    success=False,
                    error=error or "Failed to analyze signing",
                    analysis_time_ms=(time.time() - start_time) * 1000
                )
            
            # Parse analysis from response
            analysis_data = self._parse_analysis_response(response_data)
            
            analysis_time = (time.time() - start_time) * 1000
            
            logger.info(f"Signing analysis completed in {analysis_time:.1f}ms")
            
            return AnalysisResponse(
                success=True,
                feedback=analysis_data.get("feedback"),
                confidence_score=analysis_data.get("confidence_score"),
                suggestions=analysis_data.get("suggestions", []),
                analysis_time_ms=analysis_time
            )
        
        except Exception as e:
            logger.error(f"Error analyzing signing: {e}")
            return AnalysisResponse(
                success=False,
                error=f"Signing analysis error: {str(e)}",
                analysis_time_ms=(time.time() - start_time) * 1000
            )
    
    def _create_story_prompt(self, object_name: str) -> str:
        """
        Create prompt for story generation based on object
        
        Args:
            object_name: Identified object name
            
        Returns:
            str: Formatted prompt for story generation
        """
        return f"""Create a short, engaging story suitable for ASL practice featuring a {object_name}. 

Requirements:
- Write exactly 5 sentences
- Use simple, clear language appropriate for sign language practice
- Make the story engaging and fun
- Focus on actions and visual elements that translate well to ASL
- Each sentence should be on its own line
- Do not include quotation marks or dialogue

Example format:
The red ball bounced happily in the park.
Children gathered around to watch the ball.
The ball rolled down a gentle hill.
A friendly dog chased after the ball.
Everyone smiled and clapped for the ball.

Now create a story about the {object_name}:"""
    
    def _create_analysis_prompt(self, landmark_buffer: List[Dict], target_sentence: str) -> str:
        """
        Create prompt for signing analysis
        
        Args:
            landmark_buffer: Landmark data from signing attempt
            target_sentence: Target sentence being signed
            
        Returns:
            str: Formatted prompt for analysis
        """
        # Simplify landmark data for analysis (extract key movement patterns)
        movement_summary = self._summarize_movement_data(landmark_buffer)
        
        return f"""Analyze this ASL signing attempt and provide helpful feedback.

Target sentence: "{target_sentence}"

Movement data summary:
- Duration: {movement_summary['duration_ms']}ms
- Hand movements detected: {movement_summary['hand_movements']}
- Average hand positions: {movement_summary['avg_positions']}
- Movement smoothness: {movement_summary['smoothness']}

Provide constructive feedback in this format:
FEEDBACK: [2-3 sentences of specific, encouraging feedback about the signing attempt]
CONFIDENCE: [score from 0.0 to 1.0 indicating signing quality]
SUGGESTIONS: [2-3 specific tips for improvement]

Focus on:
- Hand positioning and clarity
- Movement smoothness and timing
- Sign space consistency
- Overall signing flow

Be encouraging and specific in your feedback."""
    
    def _summarize_movement_data(self, landmark_buffer: List[Dict]) -> Dict[str, Any]:
        """
        Summarize landmark data for analysis prompt
        
        Args:
            landmark_buffer: Raw landmark data
            
        Returns:
            Dict: Summarized movement data
        """
        if not landmark_buffer:
            return {
                "duration_ms": 0,
                "hand_movements": "none detected",
                "avg_positions": "no data",
                "smoothness": "no data"
            }
        
        # Calculate basic movement metrics
        duration_ms = len(landmark_buffer) * 33.33  # Assuming ~30fps
        
        # Count frames with hand landmarks
        frames_with_hands = sum(1 for frame in landmark_buffer 
                               if frame.get('landmarks', {}).get('hands'))
        
        hand_movement_ratio = frames_with_hands / len(landmark_buffer) if landmark_buffer else 0
        
        return {
            "duration_ms": int(duration_ms),
            "hand_movements": f"{hand_movement_ratio:.1%} of frames",
            "avg_positions": "center-right signing space" if hand_movement_ratio > 0.5 else "limited movement",
            "smoothness": "good" if len(landmark_buffer) > 30 else "brief"
        }
    
    def _parse_story_response(self, response_data: Dict, object_name: str) -> Dict[str, Any]:
        """
        Parse story generation response into structured format
        
        Args:
            response_data: Raw response from Ollama
            object_name: Original object name
            
        Returns:
            Dict: Structured story data
        """
        story_text = response_data.get("response", "").strip()
        
        # Split into sentences and clean up
        sentences = [
            sentence.strip() 
            for sentence in story_text.split('\n') 
            if sentence.strip() and not sentence.strip().startswith(('Example:', 'Now create'))
        ]
        
        # Filter out any remaining prompt text or instructions
        filtered_sentences = []
        for sentence in sentences:
            # Skip lines that look like instructions or examples
            if any(word in sentence.lower() for word in ['create', 'example', 'format:', 'requirements:']):
                continue
            # Skip empty lines or very short lines
            if len(sentence.strip()) < 10:
                continue
            filtered_sentences.append(sentence.strip())
        
        # Take first 5 sentences or pad if needed
        if len(filtered_sentences) < 5:
            # Generate fallback sentences if needed
            while len(filtered_sentences) < 5:
                fallback_sentences = [
                    f"The {object_name} was very special.",
                    f"Everyone loved the {object_name}.",
                    f"The {object_name} brought joy to all.",
                    f"People gathered around the {object_name}.",
                    f"The {object_name} made everyone happy."
                ]
                if len(filtered_sentences) < len(fallback_sentences):
                    filtered_sentences.append(fallback_sentences[len(filtered_sentences)])
                else:
                    break
        
        final_sentences = filtered_sentences[:5]
        
        # Create title
        title = f"The Adventure of the {object_name.title()}"
        
        return {
            "title": title,
            "sentences": final_sentences,
            "identified_object": object_name
        }
    
    def _validate_story_quality(self, story_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the quality of generated story content
        
        Args:
            story_data: Parsed story data
            
        Returns:
            Dict with validation result and reason
        """
        try:
            # Check if story has required fields
            if not isinstance(story_data, dict):
                return {"valid": False, "reason": "Story data is not a dictionary"}
            
            if "sentences" not in story_data:
                return {"valid": False, "reason": "Story missing sentences"}
            
            sentences = story_data["sentences"]
            if not isinstance(sentences, list):
                return {"valid": False, "reason": "Story sentences is not a list"}
            
            # Check sentence count
            if len(sentences) < 3:
                return {"valid": False, "reason": f"Story too short ({len(sentences)} sentences, minimum 3)"}
            
            if len(sentences) > 10:
                return {"valid": False, "reason": f"Story too long ({len(sentences)} sentences, maximum 10)"}
            
            # Check sentence quality
            for i, sentence in enumerate(sentences):
                if not isinstance(sentence, str):
                    return {"valid": False, "reason": f"Sentence {i+1} is not a string"}
                
                sentence = sentence.strip()
                if len(sentence) < 10:
                    return {"valid": False, "reason": f"Sentence {i+1} too short ({len(sentence)} characters)"}
                
                if len(sentence) > 200:
                    return {"valid": False, "reason": f"Sentence {i+1} too long ({len(sentence)} characters)"}
                
                # Check for reasonable content (not just repeated characters or nonsense)
                words = sentence.split()
                if len(words) < 3:
                    return {"valid": False, "reason": f"Sentence {i+1} has too few words ({len(words)})"}
                
                # Check for repeated words (sign of poor generation)
                unique_words = set(word.lower().strip('.,!?;:') for word in words)
                if len(unique_words) < len(words) * 0.6:  # Less than 60% unique words
                    return {"valid": False, "reason": f"Sentence {i+1} has too many repeated words"}
            
            # Check story title if present
            if "title" in story_data:
                title = story_data["title"]
                if isinstance(title, str) and title.strip():
                    if len(title.strip()) > 100:
                        return {"valid": False, "reason": "Story title too long"}
            
            # All checks passed
            return {"valid": True, "reason": "Story quality validation passed"}
            
        except Exception as e:
            logger.error(f"Error during story quality validation: {e}")
            return {"valid": False, "reason": f"Validation error: {str(e)}"}
    
    def _parse_analysis_response(self, response_data: Dict) -> Dict[str, Any]:
        """
        Parse signing analysis response into structured format
        
        Args:
            response_data: Raw response from Ollama
            
        Returns:
            Dict: Structured analysis data
        """
        analysis_text = response_data.get("response", "").strip()
        
        # Initialize default values
        feedback = "Good signing attempt! Keep practicing to improve your ASL skills."
        confidence_score = 0.7
        suggestions = ["Practice hand positioning", "Focus on smooth movements"]
        
        try:
            # Parse structured response
            lines = analysis_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('FEEDBACK:'):
                    feedback = line.replace('FEEDBACK:', '').strip()
                elif line.startswith('CONFIDENCE:'):
                    confidence_text = line.replace('CONFIDENCE:', '').strip()
                    # Extract numeric value
                    try:
                        confidence_score = float(confidence_text.split()[0])
                        confidence_score = max(0.0, min(1.0, confidence_score))  # Clamp to 0-1
                    except (ValueError, IndexError):
                        pass
                elif line.startswith('SUGGESTIONS:'):
                    suggestions_text = line.replace('SUGGESTIONS:', '').strip()
                    # Split suggestions by common delimiters
                    if suggestions_text:
                        suggestions = [
                            s.strip() 
                            for s in suggestions_text.replace(';', ',').split(',')
                            if s.strip()
                        ]
        
        except Exception as e:
            logger.warning(f"Error parsing analysis response: {e}")
            # Use defaults
        
        return {
            "feedback": feedback,
            "confidence_score": confidence_score,
            "suggestions": suggestions[:3]  # Limit to 3 suggestions
        }


# Global service instance
_ollama_service: Optional[OllamaService] = None


async def get_ollama_service() -> OllamaService:
    """
    Get global Ollama service instance
    
    Returns:
        OllamaService: Configured service instance
    """
    global _ollama_service
    
    if _ollama_service is None:
        _ollama_service = OllamaService()
        await _ollama_service.start()
    
    return _ollama_service


async def cleanup_ollama_service():
    """Cleanup global Ollama service instance"""
    global _ollama_service
    
    if _ollama_service:
        await _ollama_service.stop()
        _ollama_service = None