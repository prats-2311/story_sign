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

    async def generate_story(self, object_name: str) -> Optional[Dict[str, Any]]:
        """
        Generate a short, simple story based on the identified object using the Ollama Cloud API.
        Returns a dict with keys: title (str) and sentences (list[str]), or None on failure.
        """
        if not self.client:
            logger.error("Ollama client is not initialized. Cannot generate story.")
            return None

        prompt = (
            f"Generate a very simple, 3-sentence story for a child about a '{object_name}'. "
            f"The story must use basic words suitable for learning American Sign Language. "
            f"VERY IMPORTANT: Respond ONLY with a valid JSON object in the format: "
            f'{{"title": "The Story of the {object_name}", "sentences": ["sentence 1", "sentence 2", "sentence 3"]}}'
        )

        messages = [{"role": "user", "content": prompt}]
        logger.info(f"Generating story for object: '{object_name}' with model '{self.story_model}'")

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

            story_content = response.get('message', {}).get('content', '{}')
            story_json = json.loads(story_content)
            logger.info(f"Successfully generated story: {story_json.get('title')}")
            return story_json

        except ResponseError as e:
            logger.error(f"Ollama Cloud API error during story generation: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response from Ollama: {e}. Response was: {story_content}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during story generation: {e}")
            return None

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
            # For Ollama Cloud API, we just verify connectivity
            if self._using_cloud_api:
                if self.cloud_client:
                    try:
                        # Just use a simple request to verify the client works and auth is valid
                        loop = asyncio.get_event_loop()
                        # Run in a thread to avoid blocking
                        await loop.run_in_executor(None, lambda: self.cloud_client.list())
                        self._health_status = True
                        logger.info("Ollama Cloud API is accessible and authenticated")
                        return True
                    except Exception as e:
                        logger.warning(f"Ollama Cloud API health check failed: {e}")
                        self._health_status = False
                        return False
                else:
                    # Fallback to simple HTTP check if client isn't available
                    headers = {}
                    if self.config.api_key:
                        headers["Authorization"] = f"Bearer {self.config.api_key}"
                    try:
                        async with self.session.get(self.config.service_url, headers=headers) as response:
                            self._health_status = response.status in [200, 404]
                            if self._health_status:
                                logger.info("Ollama Cloud API is accessible")
                            else:
                                logger.warning(f"Ollama Cloud API health check failed with status: {response.status}")
                            return self._health_status
                    except Exception as e:
                        logger.warning(f"Ollama Cloud API connection failed: {e}")
                        self._health_status = False
                        return False
            # Check if service is running:
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
