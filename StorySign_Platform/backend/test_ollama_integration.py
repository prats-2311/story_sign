#!/usr/bin/env python3
"""
Integration test for Ollama service (requires running Ollama)
"""

import asyncio
from ollama_service import OllamaService

async def test_integration():
    """Test integration with real Ollama service if available"""
    print("Testing Ollama service integration...")
    
    service = OllamaService()
    
    try:
        await service.start()
        print("✓ Service session started")
        
        # Test health check
        health = await service.check_health()
        if health:
            print("✓ Ollama service is healthy and models are available")
            
            # Test story generation
            print("Testing story generation...")
            story_result = await service.generate_story("ball")
            
            if story_result.success:
                print(f"✓ Story generated successfully in {story_result.generation_time_ms:.1f}ms")
                print(f"  Title: {story_result.story['title']}")
                print(f"  Sentences: {len(story_result.story['sentences'])}")
                for i, sentence in enumerate(story_result.story['sentences'], 1):
                    print(f"    {i}. {sentence}")
            else:
                print(f"⚠ Story generation failed: {story_result.error}")
            
            # Test signing analysis
            print("\nTesting signing analysis...")
            landmark_buffer = [
                {"landmarks": {"hands": True}, "timestamp": 1000 + i * 33}
                for i in range(30)  # Simulate 1 second of data at 30fps
            ]
            
            analysis_result = await service.analyze_signing_attempt(
                landmark_buffer, 
                "Hello world"
            )
            
            if analysis_result.success:
                print(f"✓ Analysis completed in {analysis_result.analysis_time_ms:.1f}ms")
                print(f"  Feedback: {analysis_result.feedback}")
                print(f"  Confidence: {analysis_result.confidence_score}")
                print(f"  Suggestions: {analysis_result.suggestions}")
            else:
                print(f"⚠ Analysis failed: {analysis_result.error}")
        
        else:
            print("⚠ Ollama service not healthy - check if Ollama is running and models are installed")
            print("  To install required models, run:")
            print(f"    ollama pull {service.config.story_model}")
            print(f"    ollama pull {service.config.analysis_model}")
    
    except Exception as e:
        print(f"⚠ Integration test error: {e}")
        print("  Make sure Ollama is running on http://localhost:11434")
    
    finally:
        await service.stop()
        print("✓ Service session stopped")

if __name__ == "__main__":
    asyncio.run(test_integration())