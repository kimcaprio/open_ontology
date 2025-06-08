"""
Unified LLM Service
Uses LiteLLM to provide a consistent interface across multiple LLM providers
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional, AsyncGenerator, Type
import litellm
from litellm import completion, acompletion
from pydantic import BaseModel

from src.config.llm_config import llm_config, LLMProvider, LLMModelConfig

# Set up logging
logger = logging.getLogger(__name__)

# Configure LiteLLM
litellm.set_verbose = True  # Enable detailed logging
litellm.drop_params = True  # Drop unsupported parameters instead of raising errors


class LLMResponse(BaseModel):
    """Standardized LLM response"""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None


class UnifiedLLMService:
    """Unified service for interacting with multiple LLM providers via LiteLLM"""
    
    def __init__(self, default_model_key: Optional[str] = None):
        self.default_model_key = default_model_key or llm_config.default_model
        self._setup_provider_credentials()
    
    def _setup_provider_credentials(self):
        """Setup environment variables for all providers"""
        # Set environment variables for LiteLLM
        if llm_config.openai_api_key:
            os.environ["OPENAI_API_KEY"] = llm_config.openai_api_key
        
        if llm_config.anthropic_api_key:
            os.environ["ANTHROPIC_API_KEY"] = llm_config.anthropic_api_key
        
        if llm_config.aws_access_key_id:
            os.environ["AWS_ACCESS_KEY_ID"] = llm_config.aws_access_key_id
        if llm_config.aws_secret_access_key:
            os.environ["AWS_SECRET_ACCESS_KEY"] = llm_config.aws_secret_access_key
        if llm_config.aws_region:
            os.environ["AWS_REGION"] = llm_config.aws_region
        
        if llm_config.cohere_api_key:
            os.environ["COHERE_API_KEY"] = llm_config.cohere_api_key
        
        if llm_config.google_api_key:
            os.environ["GOOGLE_API_KEY"] = llm_config.google_api_key
        
        if llm_config.huggingface_api_key:
            os.environ["HUGGINGFACE_API_KEY"] = llm_config.huggingface_api_key
    
    def _build_model_name(self, model_config: LLMModelConfig) -> str:
        """Build the model name in LiteLLM format"""
        provider = model_config.provider
        model_name = model_config.model_name
        
        if provider == LLMProvider.OPENAI:
            return f"openai/{model_name}"
        elif provider == LLMProvider.ANTHROPIC:
            return f"anthropic/{model_name}"
        elif provider == LLMProvider.AWS_BEDROCK:
            return f"bedrock/{model_name}"
        elif provider == LLMProvider.GOOGLE:
            return f"gemini/{model_name}"
        elif provider == LLMProvider.COHERE:
            return f"cohere/{model_name}"
        elif provider == LLMProvider.OLLAMA:
            return f"ollama/{model_name}"
        elif provider == LLMProvider.VLLM:
            return f"vllm/{model_name}"
        elif provider == LLMProvider.HUGGINGFACE:
            return f"huggingface/{model_name}"
        else:
            return model_name
    
    def _prepare_litellm_kwargs(self, model_config: LLMModelConfig, **kwargs) -> Dict[str, Any]:
        """Prepare kwargs for LiteLLM call"""
        litellm_kwargs = kwargs.copy()
        
        # Set API base for local/custom providers
        if model_config.api_base_env_var:
            api_base = os.getenv(model_config.api_base_env_var)
            if api_base:
                litellm_kwargs["api_base"] = api_base
        
        # Add provider-specific parameters
        if model_config.additional_params:
            litellm_kwargs.update(model_config.additional_params)
        
        # Set default temperature if not provided
        if "temperature" not in litellm_kwargs:
            litellm_kwargs["temperature"] = model_config.temperature
        
        # Set max tokens if not provided
        if "max_tokens" not in litellm_kwargs and model_config.max_tokens:
            litellm_kwargs["max_tokens"] = model_config.max_tokens
        
        return litellm_kwargs
    
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        model_key: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a completion using the specified model"""
        try:
            # Get model configuration
            model_key = model_key or self.default_model_key
            model_config = llm_config.get_model_config(model_key)
            
            if not model_config:
                raise ValueError(f"Model configuration not found for key: {model_key}")
            
            # Build model name for LiteLLM
            model_name = self._build_model_name(model_config)
            
            # Prepare kwargs
            litellm_kwargs = self._prepare_litellm_kwargs(model_config, **kwargs)
            
            logger.info(f"Calling LiteLLM with model: {model_name}")
            
            # Make the API call
            response = await acompletion(
                model=model_name,
                messages=messages,
                **litellm_kwargs
            )
            
            # Extract response content
            content = response.choices[0].message.content
            
            # Build standardized response
            return LLMResponse(
                content=content,
                model=model_config.model_name,
                provider=model_config.provider.value,
                usage=response.usage.dict() if response.usage else None,
                finish_reason=response.choices[0].finish_reason
            )
            
        except Exception as e:
            logger.error(f"Error in generate_completion: {str(e)}")
            
            # Return fallback response
            return LLMResponse(
                content=f"Error generating response: {str(e)}",
                model=model_config.model_name if 'model_config' in locals() else "unknown",
                provider="error",
                finish_reason="error"
            )

    async def generate_structured_completion(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[BaseModel],
        model_key: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a structured completion using Pydantic model as response format"""
        try:
            # Get model configuration
            model_key = model_key or self.default_model_key
            model_config = llm_config.get_model_config(model_key)
            
            if not model_config:
                raise ValueError(f"Model configuration not found for key: {model_key}")
            
            # Build model name for LiteLLM
            model_name = self._build_model_name(model_config)
            
            # Prepare kwargs with structured response format
            litellm_kwargs = self._prepare_litellm_kwargs(model_config, **kwargs)
            
            # Use Pydantic model as response format for supported models
            if model_config.supports_json_mode or model_config.provider in [LLMProvider.OPENAI, LLMProvider.ANTHROPIC]:
                litellm_kwargs["response_format"] = response_model
            else:
                # Fallback: add JSON instruction to system message
                if messages and messages[0].get("role") == "system":
                    messages[0]["content"] += f"\n\nIMPORTANT: Respond ONLY with valid JSON following this schema:\n{response_model.model_json_schema()}"
                else:
                    messages.insert(0, {
                        "role": "system", 
                        "content": f"Respond ONLY with valid JSON following this schema:\n{response_model.model_json_schema()}"
                    })
            
            logger.info(f"Calling LiteLLM structured completion with model: {model_name}")
            
            # Make the API call
            response = await acompletion(
                model=model_name,
                messages=messages,
                **litellm_kwargs
            )
            
            # Extract response content
            content = response.choices[0].message.content
            
            # Try to parse as JSON and validate with Pydantic model
            try:
                parsed_json = json.loads(content)
                validated_response = response_model(**parsed_json)
                return validated_response.dict()
            except (json.JSONDecodeError, ValueError) as parse_error:
                logger.warning(f"Failed to parse structured response, attempting extraction: {parse_error}")
                # Try to extract JSON from response
                extracted_json = self._extract_json_from_text(content)
                if extracted_json:
                    try:
                        validated_response = response_model(**extracted_json)
                        return validated_response.dict()
                    except ValueError:
                        pass
                
                # Return error with raw content
                return {
                    "error": f"Failed to parse structured response: {parse_error}",
                    "raw_content": content
                }
            
        except Exception as e:
            logger.error(f"Error in generate_structured_completion: {str(e)}")
            return {
                "error": f"Error generating structured response: {str(e)}"
            }
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON object from text that may contain additional content"""
        try:
            # Look for JSON object patterns
            start_idx = text.find('{')
            if start_idx == -1:
                return None
            
            # Find matching closing brace
            brace_count = 0
            end_idx = start_idx
            
            for i, char in enumerate(text[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i
                        break
            
            if brace_count == 0:
                json_str = text[start_idx:end_idx + 1]
                return json.loads(json_str)
            
            return None
        except Exception:
            return None
    
    async def generate_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model_key: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming completion"""
        try:
            # Get model configuration
            model_key = model_key or self.default_model_key
            model_config = llm_config.get_model_config(model_key)
            
            if not model_config:
                raise ValueError(f"Model configuration not found for key: {model_key}")
            
            if not model_config.supports_streaming:
                # Fallback to non-streaming
                response = await self.generate_completion(messages, model_key, **kwargs)
                yield response.content
                return
            
            # Build model name for LiteLLM
            model_name = self._build_model_name(model_config)
            
            # Prepare kwargs
            litellm_kwargs = self._prepare_litellm_kwargs(model_config, **kwargs)
            litellm_kwargs["stream"] = True
            
            logger.info(f"Calling LiteLLM streaming with model: {model_name}")
            
            # Make the streaming API call
            response = await acompletion(
                model=model_name,
                messages=messages,
                **litellm_kwargs
            )
            
            # Yield content chunks
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            
        except Exception as e:
            logger.error(f"Error in generate_completion_stream: {str(e)}")
            yield f"Error generating streaming response: {str(e)}"
    
    async def generate_json_completion(
        self,
        messages: List[Dict[str, str]],
        model_key: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate a JSON response (for models that support it)"""
        try:
            # Get model configuration
            model_key = model_key or self.default_model_key
            model_config = llm_config.get_model_config(model_key)
            
            if not model_config:
                raise ValueError(f"Model configuration not found for key: {model_key}")
            
            # Add JSON mode if supported
            if model_config.supports_json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            
            # Generate completion
            response = await self.generate_completion(messages, model_key, **kwargs)
            
            # Try to parse as JSON
            try:
                return json.loads(response.content)
            except json.JSONDecodeError:
                # If JSON parsing fails, wrap in a JSON object
                return {"content": response.content, "raw_response": True}
                
        except Exception as e:
            logger.error(f"Error in generate_json_completion: {str(e)}")
            return {"error": f"Error generating JSON response: {str(e)}"}
    
    def get_available_models(self) -> Dict[str, LLMModelConfig]:
        """Get all available models"""
        return llm_config.get_available_models()
    
    def get_model_config(self, model_key: str) -> Optional[LLMModelConfig]:
        """Get configuration for a specific model"""
        return llm_config.get_model_config(model_key)
    
    def set_default_model(self, model_key: str):
        """Set the default model"""
        if model_key in llm_config.get_available_models():
            self.default_model_key = model_key
        else:
            raise ValueError(f"Model key '{model_key}' not found in available models")


# Global service instance
unified_llm_service = UnifiedLLMService() 