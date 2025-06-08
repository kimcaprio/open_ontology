"""
LLM Configuration Management
Supports multiple LLM providers including OpenAI, Claude, AWS Bedrock, Ollama, and vLLM
"""

import os
from enum import Enum
from typing import Dict, Optional, Any, List
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import aiohttp
import asyncio
import logging
import requests


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AWS_BEDROCK = "aws_bedrock"
    OLLAMA = "ollama"
    VLLM = "vllm"
    HUGGINGFACE = "huggingface"
    COHERE = "cohere"
    GOOGLE = "google"


class LLMModelConfig(BaseModel):
    """Configuration for a specific LLM model"""
    provider: LLMProvider
    model_name: str
    display_name: str
    api_key_env_var: Optional[str] = None
    api_base_env_var: Optional[str] = None
    additional_params: Dict[str, Any] = Field(default_factory=dict)
    max_tokens: Optional[int] = None
    temperature: float = 0.1
    supports_streaming: bool = True
    supports_json_mode: bool = False


class LLMConfig(BaseSettings):
    """LLM Configuration Settings"""
    
    # Default provider and model
    default_provider: LLMProvider = LLMProvider.OPENAI
    default_model: str = "gpt-4o-mini"
    
    # Available models configuration
    available_models: Dict[str, LLMModelConfig] = Field(default_factory=dict)
    
    # Provider API keys (read from environment)
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    cohere_api_key: Optional[str] = Field(default=None, env="COHERE_API_KEY")
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    huggingface_api_key: Optional[str] = Field(default=None, env="HUGGINGFACE_API_KEY")
    
    # Ollama configuration
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    
    # vLLM configuration
    vllm_base_url: Optional[str] = Field(default=None, env="VLLM_BASE_URL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def model_post_init(self, __context: Any) -> None:
        """Initialize available models after settings are loaded"""
        if not self.available_models:
            self.available_models = self._get_default_models()
            
        # Try to load Ollama models synchronously on initialization
        if self.is_ollama_available():
            try:
                import requests
                # Use synchronous requests for initialization
                response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    
                    # Update available models with real Ollama models
                    for model_name in models:
                        # Clean model name for key
                        clean_name = model_name.split(":")[0]  # Remove tag like ":latest"
                        key = f"ollama-{clean_name}"
                        
                        self.available_models[key] = LLMModelConfig(
                            provider=LLMProvider.OLLAMA,
                            model_name=model_name,
                            display_name=f"{clean_name.title()} (Ollama)",
                            api_base_env_var="OLLAMA_BASE_URL",
                            max_tokens=4096
                        )
                    
                    model_keys = [f'ollama-{m.split(":")[0]}' for m in models]
                    print(f"Loaded {len(models)} Ollama models: {model_keys}")
                    
            except Exception as e:
                logging.warning(f"Could not load Ollama models on initialization: {e}")
    
    def _get_default_models(self) -> Dict[str, LLMModelConfig]:
        """Get default model configurations"""
        models = {}
        
        # OpenAI models
        if self.openai_api_key:
            models.update({
                "gpt-4o": LLMModelConfig(
                    provider=LLMProvider.OPENAI,
                    model_name="gpt-4o",
                    display_name="GPT-4o (OpenAI)",
                    api_key_env_var="OPENAI_API_KEY",
                    max_tokens=4096,
                    supports_json_mode=True
                ),
                "gpt-4o-mini": LLMModelConfig(
                    provider=LLMProvider.OPENAI,
                    model_name="gpt-4o-mini",
                    display_name="GPT-4o Mini (OpenAI)",
                    api_key_env_var="OPENAI_API_KEY",
                    max_tokens=4096,
                    supports_json_mode=True
                ),
                "gpt-3.5-turbo": LLMModelConfig(
                    provider=LLMProvider.OPENAI,
                    model_name="gpt-3.5-turbo",
                    display_name="GPT-3.5 Turbo (OpenAI)",
                    api_key_env_var="OPENAI_API_KEY",
                    max_tokens=4096,
                    supports_json_mode=True
                )
            })
        
        # Anthropic models
        if self.anthropic_api_key:
            models.update({
                "claude-3-5-sonnet-20241022": LLMModelConfig(
                    provider=LLMProvider.ANTHROPIC,
                    model_name="claude-3-5-sonnet-20241022",
                    display_name="Claude 3.5 Sonnet (Anthropic)",
                    api_key_env_var="ANTHROPIC_API_KEY",
                    max_tokens=4096
                ),
                "claude-3-5-haiku-20241022": LLMModelConfig(
                    provider=LLMProvider.ANTHROPIC,
                    model_name="claude-3-5-haiku-20241022",
                    display_name="Claude 3.5 Haiku (Anthropic)",
                    api_key_env_var="ANTHROPIC_API_KEY",
                    max_tokens=4096
                )
            })
        
        # AWS Bedrock models
        if self.aws_access_key_id and self.aws_secret_access_key:
            models.update({
                "bedrock-claude-3-5-sonnet": LLMModelConfig(
                    provider=LLMProvider.AWS_BEDROCK,
                    model_name="anthropic.claude-3-5-sonnet-20241022-v2:0",
                    display_name="Claude 3.5 Sonnet (AWS Bedrock)",
                    additional_params={"region": self.aws_region},
                    max_tokens=4096
                ),
                "bedrock-claude-3-haiku": LLMModelConfig(
                    provider=LLMProvider.AWS_BEDROCK,
                    model_name="anthropic.claude-3-haiku-20240307-v1:0",
                    display_name="Claude 3 Haiku (AWS Bedrock)",
                    additional_params={"region": self.aws_region},
                    max_tokens=4096
                )
            })
        
        # Google models
        if self.google_api_key:
            models.update({
                "gemini-1.5-pro": LLMModelConfig(
                    provider=LLMProvider.GOOGLE,
                    model_name="gemini-1.5-pro",
                    display_name="Gemini 1.5 Pro (Google)",
                    api_key_env_var="GOOGLE_API_KEY",
                    max_tokens=4096
                ),
                "gemini-1.5-flash": LLMModelConfig(
                    provider=LLMProvider.GOOGLE,
                    model_name="gemini-1.5-flash",
                    display_name="Gemini 1.5 Flash (Google)",
                    api_key_env_var="GOOGLE_API_KEY",
                    max_tokens=4096
                )
            })
        
        # Cohere models
        if self.cohere_api_key:
            models.update({
                "command-r-plus": LLMModelConfig(
                    provider=LLMProvider.COHERE,
                    model_name="command-r-plus",
                    display_name="Command R+ (Cohere)",
                    api_key_env_var="COHERE_API_KEY",
                    max_tokens=4096
                ),
                "command-r": LLMModelConfig(
                    provider=LLMProvider.COHERE,
                    model_name="command-r",
                    display_name="Command R (Cohere)",
                    api_key_env_var="COHERE_API_KEY",
                    max_tokens=4096
                )
            })
        
        # Ollama models (local) - Start with empty and will be populated dynamically
        # models.update({
        #     "ollama-llama3.1": LLMModelConfig(
        #         provider=LLMProvider.OLLAMA,
        #         model_name="llama3.1",
        #         display_name="Llama 3.1 (Ollama)",
        #         api_base_env_var="OLLAMA_BASE_URL",
        #         max_tokens=4096
        #     ),
        #     "ollama-llama3.2": LLMModelConfig(
        #         provider=LLMProvider.OLLAMA,
        #         model_name="llama3.2",
        #         display_name="Llama 3.2 (Ollama)",
        #         api_base_env_var="OLLAMA_BASE_URL",
        #         max_tokens=4096
        #     ),
        #     "ollama-mistral": LLMModelConfig(
        #         provider=LLMProvider.OLLAMA,
        #         model_name="mistral",
        #         display_name="Mistral (Ollama)",
        #         api_base_env_var="OLLAMA_BASE_URL",
        #         max_tokens=4096
        #     ),
        #     "ollama-codellama": LLMModelConfig(
        #         provider=LLMProvider.OLLAMA,
        #         model_name="codellama",
        #         display_name="Code Llama (Ollama)",
        #         api_base_env_var="OLLAMA_BASE_URL",
        #         max_tokens=4096
        #     )
        # })
        
        # vLLM models
        if self.vllm_base_url:
            models.update({
                "vllm-custom": LLMModelConfig(
                    provider=LLMProvider.VLLM,
                    model_name="custom-model",
                    display_name="Custom Model (vLLM)",
                    api_base_env_var="VLLM_BASE_URL",
                    max_tokens=4096
                )
            })
        
        return models
    
    def get_model_config(self, model_key: str) -> Optional[LLMModelConfig]:
        """Get configuration for a specific model"""
        return self.available_models.get(model_key)
    
    def get_available_models(self) -> Dict[str, LLMModelConfig]:
        """Get all available models"""
        return self.available_models
    
    def get_models_by_provider(self, provider: LLMProvider) -> Dict[str, LLMModelConfig]:
        """Get models filtered by provider"""
        return {
            key: model for key, model in self.available_models.items()
            if model.provider == provider
        }
    
    async def fetch_ollama_models(self) -> List[str]:
        """Fetch available models from local Ollama server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get("models", [])
                        return [model["name"] for model in models]
                    else:
                        logging.warning(f"Failed to fetch Ollama models: HTTP {response.status}")
                        return []
        except Exception as e:
            logging.warning(f"Error fetching Ollama models: {str(e)}")
            return []
    
    async def update_ollama_models(self):
        """Update available Ollama models dynamically"""
        try:
            available_models = await self.fetch_ollama_models()
            
            # Remove existing Ollama models
            self.available_models = {
                k: v for k, v in self.available_models.items() 
                if v.provider != LLMProvider.OLLAMA
            }
            
            # Add available Ollama models
            for model_name in available_models:
                clean_name = model_name.split(":")[0]  # Remove tag suffix if present
                model_key = f"ollama-{clean_name.replace('/', '-')}"
                
                self.available_models[model_key] = LLMModelConfig(
                    provider=LLMProvider.OLLAMA,
                    model_name=model_name,
                    display_name=f"{clean_name.title()} (Ollama)",
                    api_base_env_var="OLLAMA_BASE_URL",
                    max_tokens=4096
                )
            
            logging.info(f"Updated Ollama models: {list(available_models)}")
            
        except Exception as e:
            logging.error(f"Error updating Ollama models: {str(e)}")
    
    def is_ollama_available(self) -> bool:
        """Check if Ollama server is available"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False


# Global configuration instance
llm_config = LLMConfig()

# Load Ollama models immediately after instance creation
if llm_config.is_ollama_available():
    try:
        import requests
        response = requests.get(f"{llm_config.ollama_base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            
            # Clear any existing Ollama models and add real ones
            llm_config.available_models = {
                k: v for k, v in llm_config.available_models.items() 
                if v.provider != LLMProvider.OLLAMA
            }
            
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
            print(f"Loaded {len(models)} real Ollama models: {model_keys}")
    except Exception as e:
        print(f"Could not load Ollama models: {e}") 