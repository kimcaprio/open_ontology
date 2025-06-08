#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config.llm_config import llm_config, LLMProvider

async def test_ollama():
    try:
        print(f"Ollama base URL: {llm_config.ollama_base_url}")
        print(f"Ollama available: {llm_config.is_ollama_available()}")
        
        if llm_config.is_ollama_available():
            print("Fetching Ollama models...")
            models = await llm_config.fetch_ollama_models()
            print(f"Available models: {models}")
            
            print("Updating model configuration...")
            await llm_config.update_ollama_models()
            
            ollama_models = llm_config.get_models_by_provider(LLMProvider.OLLAMA)
            print(f"Configured Ollama models: {list(ollama_models.keys())}")
        else:
            print("Ollama server is not available")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ollama()) 