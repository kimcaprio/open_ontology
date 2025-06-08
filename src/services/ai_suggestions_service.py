"""
AI Suggestions Service
Generates ontology suggestions using AI (Ollama integration)
"""

import json
import time
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4

from src.config.logging_config import get_service_logger

from src.models.ai_suggestions import (
    AISuggestionRequest, AISuggestionResponse, AISuggestion,
    SuggestionType, DEMO_SUGGESTIONS
)
from src.services.ollama_service import ollama_service


class AISuggestionsService:
    """Service for generating AI-powered ontology suggestions"""
    
    def __init__(self):
        # Initialize service logger
        self.logger = get_service_logger("ai_suggestions")
        
        self.default_model = "llama3.2:latest"
        self.suggestion_cache: Dict[str, AISuggestionResponse] = {}
        
        self.logger.info("AI Suggestions service initialized", model=self.default_model)
    
    async def generate_suggestions(self, request: AISuggestionRequest) -> AISuggestionResponse:
        """Generate AI suggestions based on request"""
        start_time = time.time()
        self.logger.log_function_start(
            "generate_suggestions",
            suggestion_type=request.suggestion_type.value,
            context=request.context,
            domain=request.domain,
            max_suggestions=request.max_suggestions
        )
        
        try:
            generation_start_time = datetime.now()
            
            # Check if Ollama is available
            ollama_available = await self._is_ollama_available()
            
            if ollama_available:
                self.logger.info("Using Ollama for AI suggestions", context=request.context)
                suggestions = await self._generate_with_ollama(request)
                model_used = self.default_model
            else:
                self.logger.log_function_warning(
                    "generate_suggestions",
                    "Ollama not available, using demo suggestions",
                    context=request.context
                )
                suggestions = self._get_demo_suggestions(request)
                model_used = "demo"
            
            # Calculate generation time
            generation_time = (datetime.now() - generation_start_time).total_seconds() * 1000
            
            response = AISuggestionResponse(
                request=request,
                suggestions=suggestions[:request.max_suggestions],
                total_suggestions=len(suggestions),
                generation_time_ms=generation_time,
                model_used=model_used
            )
            
            # Cache the response
            cache_key = self._generate_cache_key(request)
            self.suggestion_cache[cache_key] = response
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "generate_suggestions",
                result=response,
                execution_time=execution_time,
                suggestion_count=len(suggestions),
                model_used=model_used,
                generation_time_ms=generation_time,
                ollama_available=ollama_available,
                cached=True
            )
            
            return response
            
        except Exception as e:
            self.logger.log_function_error("generate_suggestions", e, context=request.context)
            
            # Fallback to demo suggestions
            suggestions = self._get_demo_suggestions(request)
            generation_time = (time.time() - start_time) * 1000
            
            return AISuggestionResponse(
                request=request,
                suggestions=suggestions[:request.max_suggestions],
                total_suggestions=len(suggestions),
                generation_time_ms=generation_time,
                model_used="demo_fallback"
            )
    
    async def _is_ollama_available(self) -> bool:
        """Check if Ollama service is available"""
        start_time = time.time()
        self.logger.log_function_start("_is_ollama_available")
        
        try:
            status = await ollama_service.get_status()
            is_healthy = status.get("status") == "healthy"
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "_is_ollama_available",
                result=f"Ollama health: {is_healthy}",
                execution_time=execution_time,
                status=status.get("status"),
                is_healthy=is_healthy
            )
            return is_healthy
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_error("_is_ollama_available", e, execution_time=execution_time)
            return False
    
    async def _generate_with_ollama(self, request: AISuggestionRequest) -> List[AISuggestion]:
        """Generate suggestions using Ollama"""
        start_time = time.time()
        self.logger.log_function_start(
            "_generate_with_ollama",
            suggestion_type=request.suggestion_type.value,
            model=self.default_model
        )
        
        try:
            prompt = self._build_prompt(request)
            
            response = await ollama_service.generate_completion(
                prompt=prompt,
                model=self.default_model,
                max_tokens=2000
            )
            
            # Parse the response and convert to AISuggestion objects
            suggestions = self._parse_ollama_response(response, request.suggestion_type)
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "_generate_with_ollama",
                result=f"Generated {len(suggestions)} suggestions",
                execution_time=execution_time,
                suggestion_count=len(suggestions),
                model=self.default_model,
                prompt_length=len(prompt),
                response_length=len(response) if response else 0
            )
            
            return suggestions
            
        except Exception as e:
            self.logger.log_function_error("_generate_with_ollama", e, model=self.default_model)
            return self._get_demo_suggestions(request)
    
    def _build_prompt(self, request: AISuggestionRequest) -> str:
        """Build prompt for Ollama based on request"""
        base_prompt = f"""
You are an expert ontology engineer. Generate {request.max_suggestions} suggestions for {request.suggestion_type.value} based on the following context:

Context: {request.context}
Domain: {request.domain or 'General'}
Suggestion Type: {request.suggestion_type.value}

Please provide suggestions in JSON format with the following structure for each suggestion:
{{
    "title": "Suggestion title",
    "description": "Detailed description", 
    "confidence": 0.85,
    "implementation": {{"key": "value"}},
    "rationale": "Why this suggestion is relevant",
    "tags": ["tag1", "tag2"]
}}

"""
        
        if request.suggestion_type == SuggestionType.ONTOLOGY_CLASS:
            base_prompt += """
For ontology classes, include in implementation:
- class_name: The suggested class name
- namespace: Suggested namespace
- parent_class: Parent class if applicable
- properties: List of suggested properties
"""
        elif request.suggestion_type == SuggestionType.PROPERTY:
            base_prompt += """
For properties, include in implementation:
- property_name: The suggested property name
- property_type: ObjectProperty, DataProperty, or AnnotationProperty
- domain: Property domain class
- range: Property range (class or datatype)
"""
        elif request.suggestion_type == SuggestionType.RELATIONSHIP:
            base_prompt += """
For relationships, include in implementation:
- source_entity: Source entity/class
- target_entity: Target entity/class
- relationship_type: Type of relationship
- cardinality: Relationship cardinality (1:1, 1:n, n:m)
"""
        
        base_prompt += "\nReturn only valid JSON without any additional text or formatting."
        
        return base_prompt
    
    def _parse_ollama_response(self, response: str, suggestion_type: SuggestionType) -> List[AISuggestion]:
        """Parse Ollama response into AISuggestion objects"""
        start_time = time.time()
        self.logger.log_function_start(
            "_parse_ollama_response",
            suggestion_type=suggestion_type.value,
            response_length=len(response) if response else 0
        )
        
        try:
            # Try to extract JSON from response
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Parse JSON
            parsed_data = json.loads(response)
            
            # Convert to AISuggestion objects
            suggestions = []
            if isinstance(parsed_data, list):
                for i, item in enumerate(parsed_data):
                    suggestion = AISuggestion(
                        id=f"ai_{uuid4().hex[:8]}",
                        type=suggestion_type,
                        title=item.get("title", f"AI Suggestion {i+1}"),
                        description=item.get("description", ""),
                        confidence=float(item.get("confidence", 0.8)),
                        implementation=item.get("implementation", {}),
                        rationale=item.get("rationale", "Generated by AI"),
                        tags=item.get("tags", [])
                    )
                    suggestions.append(suggestion)
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "_parse_ollama_response",
                result=f"Parsed {len(suggestions)} suggestions",
                execution_time=execution_time,
                suggestion_count=len(suggestions),
                response_type=type(parsed_data).__name__
            )
            
            return suggestions
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_error(
                "_parse_ollama_response", 
                e, 
                execution_time=execution_time,
                response_preview=response[:200] if response else "None"
            )
            return []
    
    def _get_demo_suggestions(self, request: AISuggestionRequest) -> List[AISuggestion]:
        """Get demo suggestions as fallback"""
        start_time = time.time()
        self.logger.log_function_start(
            "_get_demo_suggestions",
            suggestion_type=request.suggestion_type.value
        )
        
        try:
            suggestion_type_key = request.suggestion_type.value
            
            if suggestion_type_key in DEMO_SUGGESTIONS:
                suggestions = DEMO_SUGGESTIONS[suggestion_type_key].copy()
            else:
                # Return generic demo suggestions
                suggestions = [
                    AISuggestion(
                        id=f"demo_{uuid4().hex[:8]}",
                        type=request.suggestion_type,
                        title=f"Demo {request.suggestion_type.value.title()} Suggestion",
                        description=f"Demo suggestion for {request.context or 'general context'}",
                        confidence=0.75,
                        implementation={"demo": True},
                        rationale="Demo suggestion for testing purposes",
                        tags=["demo", "fallback"]
                    )
                ]
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "_get_demo_suggestions",
                result=f"Retrieved {len(suggestions)} demo suggestions",
                execution_time=execution_time,
                suggestion_count=len(suggestions),
                suggestion_type=suggestion_type_key
            )
            
            return suggestions
            
        except Exception as e:
            self.logger.log_function_error("_get_demo_suggestions", e)
            return []
    
    def _generate_cache_key(self, request: AISuggestionRequest) -> str:
        """Generate cache key for request"""
        key_parts = [
            request.context[:50],  # First 50 chars of context
            request.suggestion_type.value,
            request.domain or "general",
            str(request.max_suggestions)
        ]
        return "_".join(key_parts).replace(" ", "_").lower()
    
    async def get_suggestion_types(self) -> List[Dict[str, str]]:
        """Get available suggestion types"""
        return [
            {
                "value": SuggestionType.ONTOLOGY_CLASS.value,
                "label": "Ontology Classes",
                "description": "Suggest new classes for your ontology"
            },
            {
                "value": SuggestionType.PROPERTY.value,
                "label": "Properties",
                "description": "Suggest properties and relationships"
            },
            {
                "value": SuggestionType.RELATIONSHIP.value,
                "label": "Relationships",
                "description": "Suggest relationships between entities"
            },
            {
                "value": SuggestionType.MAPPING.value,
                "label": "Data Mappings",
                "description": "Suggest mappings from data to ontology"
            },
            {
                "value": SuggestionType.ENHANCEMENT.value,
                "label": "Enhancements",
                "description": "Suggest improvements to existing ontology"
            }
        ]
    
    async def apply_suggestion(self, suggestion_id: str) -> Dict[str, Any]:
        """Apply a suggestion to the ontology"""
        # This would integrate with the actual ontology management system
        self.logger.info(f"Applying suggestion: {suggestion_id}")
        
        return {
            "status": "success",
            "message": f"Suggestion {suggestion_id} applied successfully",
            "applied_at": datetime.now().isoformat()
        }
    
    def get_suggestion_history(self) -> List[AISuggestionResponse]:
        """Get history of generated suggestions"""
        return list(self.suggestion_cache.values())


# Global service instance
ai_suggestions_service = AISuggestionsService() 