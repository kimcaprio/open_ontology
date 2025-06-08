#!/usr/bin/env python3
"""
Debug script to test Ollama model loading
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.llm_config import llm_config

async def main():
    print("=== Debug Ollama Model Loading ===")
    
    # Check Ollama availability
    print(f"Ollama available: {llm_config.is_ollama_available()}")
    print(f"Ollama base URL: {llm_config.ollama_base_url}")
    
    # Get current models
    current_models = llm_config.get_available_models()
    ollama_models = {k: v for k, v in current_models.items() if v.provider.value == "ollama"}
    print(f"Current Ollama models: {list(ollama_models.keys())}")
    
    # Try to fetch fresh models
    if llm_config.is_ollama_available():
        print("\nFetching fresh Ollama models...")
        try:
            fresh_models = await llm_config.fetch_ollama_models()
            print(f"Fresh models from API: {fresh_models}")
            
            print("\nUpdating model configuration...")
            await llm_config.update_ollama_models()
            
            # Check updated models
            updated_models = llm_config.get_available_models()
            updated_ollama_models = {k: v for k, v in updated_models.items() if v.provider.value == "ollama"}
            print(f"Updated Ollama models: {list(updated_ollama_models.keys())}")
            
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Ollama is not available")

if __name__ == "__main__":
    asyncio.run(main()) 