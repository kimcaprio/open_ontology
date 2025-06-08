"""
AI Suggestions API endpoints
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks

from loguru import logger

from src.models.ai_suggestions import (
    AISuggestionRequest, AISuggestionResponse, AISuggestion
)
from src.services.ai_suggestions_service import ai_suggestions_service

router = APIRouter(tags=["ai-suggestions"])


@router.post("/ai-suggestions/generate", response_model=AISuggestionResponse)
async def generate_suggestions(request: AISuggestionRequest):
    """Generate AI suggestions for ontology development"""
    try:
        logger.info(f"Generating AI suggestions: {request.suggestion_type.value} for context: {request.context[:50]}...")
        
        response = await ai_suggestions_service.generate_suggestions(request)
        
        logger.info(f"Generated {response.total_suggestions} suggestions in {response.generation_time_ms:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Error generating AI suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-suggestions/types")
async def get_suggestion_types():
    """Get available AI suggestion types"""
    try:
        types = await ai_suggestions_service.get_suggestion_types()
        return {"suggestion_types": types}
    except Exception as e:
        logger.error(f"Error getting suggestion types: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ai-suggestions/apply/{suggestion_id}")
async def apply_suggestion(suggestion_id: str, background_tasks: BackgroundTasks):
    """Apply an AI suggestion to the ontology"""
    try:
        logger.info(f"Applying suggestion: {suggestion_id}")
        
        # Apply suggestion in background
        result = await ai_suggestions_service.apply_suggestion(suggestion_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error applying suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-suggestions/history", response_model=List[AISuggestionResponse])
async def get_suggestion_history():
    """Get history of generated suggestions"""
    try:
        history = ai_suggestions_service.get_suggestion_history()
        return history
    except Exception as e:
        logger.error(f"Error getting suggestion history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai-suggestions/demo/{suggestion_type}")
async def get_demo_suggestions(suggestion_type: str):
    """Get demo suggestions for testing"""
    try:
        from src.models.ai_suggestions import DEMO_SUGGESTIONS, SuggestionType
        
        # Validate suggestion type
        try:
            suggestion_enum = SuggestionType(suggestion_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid suggestion type: {suggestion_type}")
        
        suggestions = DEMO_SUGGESTIONS.get(suggestion_type, [])
        
        return {
            "suggestion_type": suggestion_type,
            "suggestions": [s.model_dump() for s in suggestions],
            "total": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"Error getting demo suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 