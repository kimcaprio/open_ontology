#!/usr/bin/env python3
"""
Test live model updates while server is running
"""

import sys
import os
import requests
import json

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config.llm_config import llm_config, LLMProvider, LLMModelConfig

def test_live_update():
    print("=== Testing Live Model Update ===")
    
    # Check current models
    current_models = llm_config.get_available_models()
    ollama_models = {k: v for k, v in current_models.items() if v.provider.value == "ollama"}
    print(f"Current Ollama models in config: {list(ollama_models.keys())}")
    
    # Check API response
    try:
        response = requests.get("http://localhost:8001/api/v1/analysis/llm-models")
        if response.status_code == 200:
            data = response.json()
            api_ollama_models = [m for m in data["available_models"] if m["provider"] == "ollama"]
            print(f"API Ollama models: {[m['key'] for m in api_ollama_models]}")
        else:
            print(f"API error: {response.status_code}")
    except Exception as e:
        print(f"API call failed: {e}")
    
    # Try to update models directly
    print("\nUpdating models directly...")
    if llm_config.is_ollama_available():
        try:
            # Get fresh models from Ollama
            response = requests.get(f"{llm_config.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                print(f"Fresh models from Ollama API: {models}")
                
                # Clear existing Ollama models
                llm_config.available_models = {
                    k: v for k, v in llm_config.available_models.items() 
                    if v.provider != LLMProvider.OLLAMA
                }
                
                # Add fresh models
                for model_name in models:
                    clean_name = model_name.split(":")[0]
                    key = f"ollama-{clean_name}"
                    
                    llm_config.available_models[key] = LLMModelConfig(
                        provider=LLMProvider.OLLAMA,
                        model_name=model_name,
                        display_name=f"{clean_name.title()} (Ollama)",
                        api_base_env_var="OLLAMA_BASE_URL",
                        max_tokens=4096
                    )
                
                model_keys = [f'ollama-{m.split(":")[0]}' for m in models]
                print(f"Updated config with: {model_keys}")
                
                # Check updated models
                updated_models = llm_config.get_available_models()
                updated_ollama_models = {k: v for k, v in updated_models.items() if v.provider.value == "ollama"}
                print(f"Config now has: {list(updated_ollama_models.keys())}")
                
        except Exception as e:
            print(f"Update failed: {e}")
    
    # Check API again
    print("\nChecking API after update...")
    try:
        response = requests.get("http://localhost:8001/api/v1/analysis/llm-models")
        if response.status_code == 200:
            data = response.json()
            api_ollama_models = [m for m in data["available_models"] if m["provider"] == "ollama"]
            print(f"API Ollama models after update: {[m['key'] for m in api_ollama_models]}")
        else:
            print(f"API error: {response.status_code}")
    except Exception as e:
        print(f"API call failed: {e}")

if __name__ == "__main__":
    test_live_update() 