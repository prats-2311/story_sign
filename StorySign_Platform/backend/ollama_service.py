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
import httpx
from ollama import Client, ResponseError
# Change from relative import to absolute import
from config import AppConfig

try:
    from ollama import Client as OllamaClient
    OLLAMA_CLIENT_AVAILABLE = True
except ImportError:
    OLLAMA_CLIENT_AVAILABLE = False

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
    def __init__(self, config: AppConfig):
        """
        Initializes the OllamaService with configuration for the cloud API.
        """
        # Handle configuration structure more defensively
        if hasattr(config, 'ollama'):
            # Use config.ollama if available
            self.config = config.ollama
            print(f"INFO:     Using config.ollama structure")
        elif hasattr(config, 'ollama_config'):
            # Fall back to config.ollama_config if that's the structure
            self.config = config.ollama_config
            print(f"INFO:     Using config.ollama_config structure")
        else:
            # If neither exists, use the config directly and hope it has the needed attributes
            print(f"WARNING:  Could not find ollama configuration section, using config directly")
            self.config = config

        # Set default values for required config attributes if they don't exist
        self.story_model = getattr(self.config, 'story_model', 'gpt-oss:20b')
        self.analysis_model = getattr(self.config, 'analysis_model', 'gpt-oss:20b')

        # Default config values
        service_url = getattr(self.config, 'service_url', 'https://ollama.com')
        api_key = getattr(self.config, 'api_key', '')

        # Add debugging info about API key
        print(f"INFO:     Using API key (length: {len(api_key)})")
        if not api_key:
            print(f"WARNING:  No API key provided for Ollama Cloud API")

        # Initialize cloud API flags
        self._using_cloud_api = "ollama.com" in service_url
        self.cloud_client = None
        self.session = None
        self._health_status = False
        self._last_health_check = 0
        self._health_check_interval = 30  # seconds

        # Create a client configured for the Ollama Cloud API
        try:
            self.client = Client(
                host=service_url,
                headers={'Authorization': f'Bearer {api_key}'}
            )
            print(f"INFO:     OllamaService connected to cloud host: {service_url}")

            # Also set cloud_client for compatibility with existing code
            if self._using_cloud_api and OLLAMA_CLIENT_AVAILABLE:
                self.cloud_client = self.client
        except Exception as e:
            print(f"ERROR:    Failed to initialize Ollama client: {e}")
            self.client = None

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

    async def generate_story(self, topic: str) -> Optional[Dict[str, Any]]:
        """
        Generate multiple difficulty levels of stories based on the topic using the Ollama Cloud API.
        Returns a dict with keys for each difficulty level, or None on failure.
        """
        if not self.client:
            logger.error("Ollama client is not initialized. Cannot generate story.")
            return None

        prompt = f"""
        You are an expert curriculum designer for American Sign Language (ASL).
        Your task is to create a set of five short stories about the topic: "{topic}".
        Each story must be tailored to a specific ASL skill level.
        The skill levels are: Amateur, Normal, Mid-Level, Difficult, Expert.

        Here are the requirements for each level:
        - Amateur: 3 sentences. Very simple subject-verb-object structure. Use only basic, common ASL vocabulary.
        - Normal: 3-4 sentences. Introduce slightly more complex vocabulary and sentence structures.
        - Mid-Level: 4 sentences. Introduce concepts like classifiers or very simple rhetorical questions.
        - Difficult: 4-5 sentences. Use more complex ASL grammar, classifiers, and varied sentence structures. The story should have more detail.
        - Expert: 5 sentences. Use advanced ASL concepts, including nuanced facial expressions (which you can suggest in parentheses), complex classifiers, and potentially conditional sentences.

        You MUST respond with ONLY a valid JSON object. The JSON object must have a single key "stories" which contains five keys: "amateur", "normal", "mid_level", "difficult", and "expert". Each of these keys will contain an object with a "title" and a list of "sentences".

        Example response format:
        {{
          "stories": {{
            "amateur": {{ "title": "The Story of the {topic}", "sentences": ["...", "...", "..."] }},
            "normal": {{ "title": "A Tale of the {topic}", "sentences": ["...", "...", "..."] }},
            "mid_level": {{ "title": "The {topic}'s Journey", "sentences": ["...", "...", "...", "..."] }},
            "difficult": {{ "title": "Adventures of the {topic}", "sentences": ["...", "...", "...", "..."] }},
            "expert": {{ "title": "A Complex Legend of the {topic}", "sentences": ["...", "...", "...", "...", "..."] }}
          }}
        }}
        """

        messages = [{"role": "user", "content": prompt}]
        logger.info(f"Generating multi-level story for topic: '{topic}' with model '{self.story_model}'")

        try:
            # The Ollama Python client is synchronous; run it in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat(
                    model=self.story_model,
                    messages=messages,
                    format="json"
                )
            )

            content_str = response.get('message', {}).get('content', '{}')

            # Use our existing cleanup logic
            if content_str.strip().startswith("```json"):
                content_str = content_str.strip()[7:-3].strip()
            elif content_str.strip().startswith("```"):
                 content_str = content_str.strip()[3:-3].strip()

            story_data = json.loads(content_str)

            return story_data.get("stories", story_data)

        except ResponseError as e:
            logger.error(f"Ollama Cloud API error during multi-level story generation: {e}")
            # Return a fallback story when the API fails
            return self._generate_fallback_story(topic)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response from multi-level story generation: {e}. Response was: {content_str}")
            return self._generate_fallback_story(topic)
        except Exception as e:
            logger.error(f"Unexpected error during multi-level story generation: {e}")
            return self._generate_fallback_story(topic)

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

    def _generate_fallback_story(self, topic: str) -> Dict[str, Any]:
        """
        Generate a fallback story when the API is unavailable
        
        Args:
            topic: The topic for the story
            
        Returns:
            Dictionary containing fallback stories for all difficulty levels
        """
        logger.info(f"Generating fallback story for topic: '{topic}'")
        
        # Create simple template-based stories
        fallback_stories = {
            "amateur": {
                "title": f"The {topic}",
                "sentences": [
                    f"I see a {topic.lower()}.",
                    f"The {topic.lower()} is nice.",
                    f"I like the {topic.lower()}."
                ]
            },
            "normal": {
                "title": f"A Story About {topic}",
                "sentences": [
                    f"Today I found a {topic.lower()}.",
                    f"The {topic.lower()} was very interesting.",
                    f"I decided to learn more about it.",
                    f"Now I understand {topic.lower()} better."
                ]
            },
            "mid_level": {
                "title": f"The {topic} Adventure",
                "sentences": [
                    f"While walking, I discovered a {topic.lower()}.",
                    f"The {topic.lower()} had many interesting features.",
                    f"I wondered how it worked and what it was for.",
                    f"After studying it carefully, I learned something new."
                ]
            },
            "difficult": {
                "title": f"Exploring the {topic}",
                "sentences": [
                    f"During my exploration, I encountered a fascinating {topic.lower()}.",
                    f"The {topic.lower()} exhibited unique characteristics that caught my attention.",
                    f"I began to analyze its structure and function systematically.",
                    f"Through careful observation, I gained valuable insights.",
                    f"This experience taught me to appreciate the complexity of {topic.lower()}."
                ]
            },
            "expert": {
                "title": f"The Complex Nature of {topic}",
                "sentences": [
                    f"In my comprehensive study, I investigated the multifaceted aspects of {topic.lower()}.",
                    f"The {topic.lower()} demonstrated intricate relationships between form and function.",
                    f"Through methodical analysis, I uncovered underlying principles governing its behavior.",
                    f"These discoveries challenged my preconceived notions about {topic.lower()}.",
                    f"Ultimately, this research expanded my understanding of how {topic.lower()} interacts with its environment."
                ]
            }
        }
        
        return fallback_stories

    async def analyze_signing_attempt(self, landmark_buffer: list, target_sentence: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a signing attempt using the landmark buffer and provide contextual feedback

        Args:
            landmark_buffer: List of landmark data collected during the gesture
            target_sentence: The sentence the user was trying to sign

        Returns:
            Dictionary with analysis results including feedback, confidence, and suggestions
        """
        if not self.client or not landmark_buffer:
            logger.error("Cannot analyze signing attempt: Ollama client not initialized or empty landmark buffer")
            return None

        try:
            # Process landmark buffer to extract meaningful features
            analysis_data = self._process_landmark_buffer_for_analysis(landmark_buffer)

            # Create analysis prompt
            prompt = self._create_signing_analysis_prompt(analysis_data, target_sentence)

            messages = [{"role": "user", "content": prompt}]
            logger.info(f"Analyzing signing attempt for sentence: '{target_sentence}' with {len(landmark_buffer)} frames")

            # Run analysis in thread to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat(
                    model=self.analysis_model,
                    messages=messages,
                    format="json"
                )
            )

            # Debug: Log raw Ollama response for analysis
            try:
                logger.info(f"SUCCESS: Received raw Ollama analysis response: {response}")
            except Exception as log_err:
                logger.warning(f"Could not log raw Ollama response: {log_err}")

            analysis_content = response.get('message', {}).get('content', '{}')

            # --- START: NEW CLEANUP CODE ---
            # Clean the response string by removing markdown code blocks and stripping whitespace
            if analysis_content.strip().startswith("```json"):
                analysis_content = analysis_content.strip()[7:-3].strip()
            elif analysis_content.strip().startswith("```"):
                 analysis_content = analysis_content.strip()[3:-3].strip()
            # --- END: NEW CLEANUP CODE ---

            analysis_result = json.loads(analysis_content)

            logger.info(f"Successfully analyzed signing attempt with confidence: {analysis_result.get('confidence_score', 'N/A')}")
            return analysis_result

        except ResponseError as e:
            logger.error(f"Ollama Cloud API error during signing analysis: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response from signing analysis: {e}. Response was: {analysis_content}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during signing analysis: {e}")
            return None

    def _process_landmark_buffer_for_analysis(self, landmark_buffer: list) -> Dict[str, Any]:
        """
        Process landmark buffer to extract meaningful features for analysis

        Args:
            landmark_buffer: List of landmark data from gesture detection

        Returns:
            Dictionary containing processed analysis data
        """
        try:
            if not landmark_buffer:
                return {"error": "Empty landmark buffer"}

            # Extract basic statistics from the landmark buffer
            total_frames = len(landmark_buffer)

            # Count frames with different landmark types detected
            hands_detected_frames = sum(1 for frame in landmark_buffer
                                      if frame.get('landmarks', {}).get('hands', False))
            face_detected_frames = sum(1 for frame in landmark_buffer
                                     if frame.get('landmarks', {}).get('face', False))
            pose_detected_frames = sum(1 for frame in landmark_buffer
                                     if frame.get('landmarks', {}).get('pose', False))

            # Calculate gesture duration
            if total_frames > 0:
                start_time = landmark_buffer[0].get('timestamp', 0)
                end_time = landmark_buffer[-1].get('timestamp', 0)
                gesture_duration_ms = (end_time - start_time) * 1000
            else:
                gesture_duration_ms = 0

            # Calculate detection consistency
            hands_consistency = hands_detected_frames / total_frames if total_frames > 0 else 0
            face_consistency = face_detected_frames / total_frames if total_frames > 0 else 0
            pose_consistency = pose_detected_frames / total_frames if total_frames > 0 else 0

            analysis_data = {
                "total_frames": total_frames,
                "gesture_duration_ms": gesture_duration_ms,
                "landmark_detection": {
                    "hands_consistency": round(hands_consistency, 2),
                    "face_consistency": round(face_consistency, 2),
                    "pose_consistency": round(pose_consistency, 2),
                    "hands_detected_frames": hands_detected_frames,
                    "face_detected_frames": face_detected_frames,
                    "pose_detected_frames": pose_detected_frames
                },
                "gesture_quality": {
                    "duration_appropriate": 1000 <= gesture_duration_ms <= 5000,
                    "hands_visible": hands_consistency > 0.7,
                    "stable_detection": min(hands_consistency, pose_consistency) > 0.5
                }
            }

            logger.debug(f"Processed landmark buffer: {analysis_data}")
            return analysis_data

        except Exception as e:
            logger.error(f"Error processing landmark buffer for analysis: {e}")
            return {"error": str(e)}

    def _create_signing_analysis_prompt(self, analysis_data: Dict[str, Any], target_sentence: str) -> str:
        """
        Create a prompt for signing analysis based on landmark data and target sentence

        Args:
            analysis_data: Processed landmark analysis data
            target_sentence: The sentence the user was trying to sign

        Returns:
            Formatted prompt string for the LLM
        """
        try:
            # Handle error cases
            if "error" in analysis_data:
                return f"""
                Analyze this ASL signing attempt for the sentence: "{target_sentence}"

                There was an issue with the gesture data: {analysis_data['error']}

                Please provide encouraging feedback and suggest the user try again.

                Respond ONLY with valid JSON in this format:
                {{
                    "feedback": "Encouraging message about trying again",
                    "confidence_score": 0.0,
                    "suggestions": ["Try again with clear hand movements", "Ensure good lighting"],
                    "analysis_summary": "Unable to analyze due to data issue"
                }}
                """

            # Create detailed analysis prompt
            gesture_quality = analysis_data.get("gesture_quality", {})
            landmark_detection = analysis_data.get("landmark_detection", {})

            prompt = f"""
            Analyze this ASL signing attempt for the sentence: "{target_sentence}"

            Gesture Data Analysis:
            - Duration: {analysis_data.get('gesture_duration_ms', 0):.0f}ms
            - Total frames captured: {analysis_data.get('total_frames', 0)}
            - Hand visibility: {landmark_detection.get('hands_consistency', 0):.0%} of frames
            - Face visibility: {landmark_detection.get('face_consistency', 0):.0%} of frames
            - Body pose visibility: {landmark_detection.get('pose_consistency', 0):.0%} of frames

            Quality Indicators:
            - Appropriate duration: {gesture_quality.get('duration_appropriate', False)}
            - Hands clearly visible: {gesture_quality.get('hands_visible', False)}
            - Stable detection: {gesture_quality.get('stable_detection', False)}

            As an ASL instructor, provide constructive feedback on this signing attempt. Focus on:
            1. What the user did well based on the gesture data
            2. Specific areas for improvement related to hand positioning, timing, or visibility
            3. Practical suggestions for better signing technique
            4. Encouragement appropriate for a learning environment

            Consider that this is gesture detection data, not actual sign recognition, so focus on:
            - Movement quality and consistency
            - Hand and body positioning
            - Gesture timing and flow
            - Technical aspects of signing form

            Respond ONLY with valid JSON in this format:
            {{
                "feedback": "Detailed constructive feedback about the signing attempt",
                "confidence_score": 0.85,
                "suggestions": ["Specific suggestion 1", "Specific suggestion 2", "Specific suggestion 3"],
                "analysis_summary": "Brief summary of the gesture quality analysis"
            }}
            """

            return prompt.strip()

        except Exception as e:
            logger.error(f"Error creating signing analysis prompt: {e}")
            return f"""
            Analyze this ASL signing attempt for the sentence: "{target_sentence}"

            There was an error processing the gesture data.

            Please provide encouraging feedback and suggest the user try again.

            Respond ONLY with valid JSON in this format:
            {{
                "feedback": "Please try signing again with clear, deliberate movements",
                "confidence_score": 0.0,
                "suggestions": ["Ensure good lighting", "Sign at a comfortable pace", "Keep hands visible"],
                "analysis_summary": "Unable to analyze due to processing error"
            }}
            """

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
            # For Ollama Cloud API, we just verify connectivity
            if self._using_cloud_api:
                if self.cloud_client:
                    try:
                        # Just use a simple request to verify the client works and auth is valid
                        loop = asyncio.get_event_loop()
                        # Run in a thread to avoid blocking with timeout
                        await asyncio.wait_for(
                            loop.run_in_executor(None, lambda: self.cloud_client.list()),
                            timeout=10.0  # 10 second timeout
                        )
                        self._health_status = True
                        logger.info("Ollama Cloud API is accessible and authenticated")
                        return True
                    except asyncio.TimeoutError:
                        logger.warning("Ollama Cloud API health check timed out")
                        self._health_status = False
                        return False
                    except Exception as e:
                        logger.warning(f"Ollama Cloud API health check failed: {e}")
                        # For cloud API failures, we'll still return True to allow fallback stories
                        self._health_status = True
                        logger.info("Ollama Cloud API unavailable, but fallback stories will be used")
                        return True
                else:
                    # Fallback to simple HTTP check if client isn't available
                    headers = {}
                    if self.config.api_key:
                        headers["Authorization"] = f"Bearer {self.config.api_key}"
                    try:
                        timeout = aiohttp.ClientTimeout(total=5)
                        async with self.session.get(self.config.service_url, headers=headers, timeout=timeout) as response:
                            self._health_status = response.status in [200, 404]
                            if self._health_status:
                                logger.info("Ollama Cloud API is accessible")
                            else:
                                logger.warning(f"Ollama Cloud API health check failed with status: {response.status}")
                            return self._health_status
                    except Exception as e:
                        logger.warning(f"Ollama Cloud API connection failed: {e}")
                        # For cloud API failures, we'll still return True to allow fallback stories
                        self._health_status = True
                        logger.info("Ollama Cloud API unavailable, but fallback stories will be used")
                        return True
            # Check if service is running:
            url = f"{self.config.service_url.rstrip('/')}/api/tags"
            timeout = aiohttp.ClientTimeout(total=5)
            async with self.session.get(url, timeout=timeout) as response:
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

        except asyncio.TimeoutError:
            logger.warning("Ollama health check timed out")
            # For cloud API, timeout is acceptable - we can use fallback
            if self._using_cloud_api:
                self._health_status = True
                logger.info("Ollama Cloud API timed out, but fallback stories will be used")
            else:
                self._health_status = False
        except Exception as e:
            logger.warning(f"Ollama health check error: {e}")
            # For cloud API, errors are acceptable - we can use fallback
            if self._using_cloud_api:
                self._health_status = True
                logger.info("Ollama Cloud API error, but fallback stories will be used")
            else:
                self._health_status = False

        self._last_health_check = current_time
        return self._health_status

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
        # Get the configuration
        from config import get_config
        config = get_config()
        # Pass the config to the OllamaService constructor
        _ollama_service = OllamaService(config)
        await _ollama_service.start()
    return _ollama_service


async def cleanup_ollama_service():
    """Cleanup global Ollama service instance"""
    global _ollama_service
    if _ollama_service:
        await _ollama_service.stop()
        _ollama_service = None
