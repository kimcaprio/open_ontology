"""
Ollama AI Service for ontology analysis and data insights
"""

import json
from typing import Dict, List, Optional, Any
import httpx
from loguru import logger

from src.config import Settings


class OllamaService:
    """Ollama AI service for ontology and data analysis"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = settings.ollama_endpoint
        self.model = settings.ollama_model
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def health_check(self) -> bool:
        """Check Ollama service health"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    async def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Generate response using Ollama model"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            return None
    
    async def analyze_schema(self, schema_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze database schema and suggest ontology mappings"""
        system_prompt = """You are an expert data architect specializing in ontology design. 
        Analyze the provided database schema and suggest appropriate ontology entities, 
        relationships, and semantic mappings. Respond in JSON format."""
        
        prompt = f"""
        Analyze this database schema and provide ontology recommendations:
        
        Schema: {json.dumps(schema_data, indent=2)}
        
        Please provide:
        1. Suggested entity types and their properties
        2. Relationships between entities
        3. Semantic mappings to standard vocabularies (if applicable)
        4. Data quality recommendations
        
        Format your response as JSON with the following structure:
        {{
            "entities": [
                {{
                    "name": "EntityName",
                    "type": "Class",
                    "properties": ["prop1", "prop2"],
                    "description": "Description of the entity"
                }}
            ],
            "relationships": [
                {{
                    "subject": "Entity1",
                    "predicate": "hasRelationTo",
                    "object": "Entity2",
                    "description": "Description of relationship"
                }}
            ],
            "recommendations": [
                "Recommendation 1",
                "Recommendation 2"
            ]
        }}
        """
        
        response = await self.generate_response(prompt, system_prompt)
        if response:
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON response from Ollama")
                return {"error": "Invalid JSON response", "raw_response": response}
        return None
    
    async def suggest_data_classification(self, column_data: List[str]) -> Optional[Dict[str, Any]]:
        """Suggest data classification for column values"""
        system_prompt = """You are a data classification expert. Analyze the provided data samples 
        and suggest appropriate data types, sensitivity levels, and classification categories."""
        
        sample_data = column_data[:10]  # Limit to first 10 samples
        
        prompt = f"""
        Analyze these data samples and suggest classification:
        
        Data samples: {sample_data}
        
        Provide classification in JSON format:
        {{
            "data_type": "string|number|date|boolean|email|phone|etc",
            "sensitivity_level": "public|internal|confidential|restricted",
            "category": "personal_data|financial|technical|etc",
            "patterns": ["detected patterns"],
            "recommendations": ["data handling recommendations"]
        }}
        """
        
        response = await self.generate_response(prompt, system_prompt)
        if response:
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                logger.error("Failed to parse classification response")
                return {"error": "Invalid JSON response", "raw_response": response}
        return None
    
    async def generate_ontology_description(self, entity_name: str, properties: List[str]) -> Optional[str]:
        """Generate natural language description for ontology entity"""
        prompt = f"""
        Generate a clear, concise description for an ontology entity with the following details:
        
        Entity Name: {entity_name}
        Properties: {', '.join(properties)}
        
        The description should explain what this entity represents and how it relates to other entities in a data ontology.
        Keep it under 200 words and make it suitable for technical documentation.
        """
        
        return await self.generate_response(prompt)
    
    async def suggest_entity_relationships(self, entities: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """Suggest relationships between ontology entities"""
        system_prompt = """You are an ontology expert. Analyze the provided entities and suggest 
        meaningful relationships between them. Focus on semantic relationships that would be valuable 
        for data discovery and analysis."""
        
        prompt = f"""
        Analyze these ontology entities and suggest relationships:
        
        Entities: {json.dumps(entities, indent=2)}
        
        Suggest relationships in JSON format:
        {{
            "relationships": [
                {{
                    "subject": "EntityName1",
                    "predicate": "relationshipType",
                    "object": "EntityName2",
                    "confidence": 0.8,
                    "reasoning": "Why this relationship makes sense"
                }}
            ]
        }}
        
        Common relationship types: hasProperty, isPartOf, relatedTo, dependsOn, contains, etc.
        """
        
        response = await self.generate_response(prompt, system_prompt)
        if response:
            try:
                result = json.loads(response)
                return result.get("relationships", [])
            except json.JSONDecodeError:
                logger.error("Failed to parse relationships response")
                return []
        return []
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def get_status(self) -> Dict[str, Any]:
        """Get Ollama service status"""
        is_healthy = await self.health_check()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "endpoint": self.base_url,
            "model": self.model
        }
    
    async def generate_completion(self, prompt: str, model: Optional[str] = None, max_tokens: int = 1000) -> str:
        """Generate completion using specified model"""
        model_to_use = model or self.model
        
        try:
            payload = {
                "model": model_to_use,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens
                }
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"Failed to generate completion: {e}")
            return ""


# Global service instance
from src.config import get_settings
ollama_service = OllamaService(get_settings()) 