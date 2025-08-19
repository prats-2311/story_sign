#!/usr/bin/env python3
"""
Development server script for StorySign Backend
Provides hot reload functionality during development
"""

import uvicorn
import os
from pathlib import Path

def main():
    """Start the development server with hot reload"""
    # Get the directory where this script is located
    backend_dir = Path(__file__).parent
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Start uvicorn with hot reload
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(backend_dir)],
        log_level="info"
    )

if __name__ == "__main__":
    main()