#!/usr/bin/env python3
"""
Simple WebSocket test to debug connection issues
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_simple_connection():
    """Test simple WebSocket connection"""
    
    uri = "ws://localhost:8000/ws/video"
    
    try:
        logger.info("Connecting to WebSocket...")
        
        async with websockets.connect(uri) as websocket:
            logger.info("Connected successfully!")
            
            # Just wait and see what happens
            logger.info("Waiting for initial messages...")
            
            try:
                # Wait for any initial messages from server
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                logger.info(f"Received initial message: {message}")
                
                # Try to parse as JSON
                try:
                    data = json.loads(message)
                    logger.info(f"Message type: {data.get('type', 'unknown')}")
                    logger.info(f"Message content: {data}")
                except json.JSONDecodeError:
                    logger.info(f"Non-JSON message: {message}")
                
            except asyncio.TimeoutError:
                logger.info("No initial message received within 5 seconds")
            
            # Now send a simple ping
            logger.info("Sending ping...")
            ping_msg = {
                "type": "ping",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket.send(json.dumps(ping_msg))
            logger.info("Ping sent, waiting for response...")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                logger.info(f"Received response: {response}")
                
                try:
                    data = json.loads(response)
                    logger.info(f"Response type: {data.get('type', 'unknown')}")
                    logger.info(f"Response content: {data}")
                except json.JSONDecodeError:
                    logger.info(f"Non-JSON response: {response}")
                    
            except asyncio.TimeoutError:
                logger.warning("No response received within 10 seconds")
            
            # Keep connection alive for a bit
            logger.info("Keeping connection alive for 5 seconds...")
            await asyncio.sleep(5)
            
            logger.info("Test completed successfully")
            
    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f"Connection closed: {e}")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_connection())