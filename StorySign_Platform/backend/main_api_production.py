#!/usr/bin/env python3
"""
Production-ready StorySign API for Render deployment
"""

import os
import logging
from main_api_simple import app

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Production configuration
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment (Render sets this)
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    logger.info(f"Starting StorySign API in production mode on {host}:{port}")
    
    # Run with uvicorn in production mode
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )