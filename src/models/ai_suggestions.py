"""
AI Suggestions Models
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field


class SuggestionType(str, Enum):
    """Types of AI suggestions"""
    ONTOLOGY_CLASS = "ontology_class"
    PROPERTY = "property"
    RELATIONSHIP = "relationship"
    MAPPING = "mapping"
    ENHANCEMENT = "enhancement"


class AISuggestionRequest(BaseModel):
    """Request for AI suggestions"""
    context: str = Field(..., description="Context or description for suggestions")
    suggestion_type: SuggestionType = Field(..., description="Type of suggestion needed")
    domain: Optional[str] = Field(default=None, description="Domain or industry context")
    existing_ontology: Optional[Dict[str, Any]] = Field(default=None, description="Existing ontology structure")
    max_suggestions: int = Field(default=5, description="Maximum number of suggestions")


class AISuggestion(BaseModel):
    """Individual AI suggestion"""
    id: str = Field(..., description="Unique suggestion ID")
    type: SuggestionType = Field(..., description="Type of suggestion")
    title: str = Field(..., description="Suggestion title")
    description: str = Field(..., description="Detailed description")
    confidence: float = Field(..., description="Confidence score (0-1)")
    implementation: Dict[str, Any] = Field(..., description="Implementation details")
    rationale: str = Field(..., description="Explanation of why this suggestion is relevant")
    tags: List[str] = Field(default_factory=list, description="Relevant tags")


class AISuggestionResponse(BaseModel):
    """Response containing AI suggestions"""
    request: AISuggestionRequest = Field(..., description="Original request")
    suggestions: List[AISuggestion] = Field(..., description="Generated suggestions")
    total_suggestions: int = Field(..., description="Total number of suggestions")
    generation_time_ms: float = Field(..., description="Time taken to generate suggestions")
    model_used: str = Field(..., description="AI model used for generation")
    timestamp: datetime = Field(default_factory=datetime.now, description="Generation timestamp")


class OntologyClassSuggestion(BaseModel):
    """Suggestion for ontology class"""
    class_name: str = Field(..., description="Suggested class name")
    namespace: str = Field(..., description="Suggested namespace")
    parent_class: Optional[str] = Field(default=None, description="Parent class if applicable")
    properties: List[str] = Field(default_factory=list, description="Suggested properties")
    description: str = Field(..., description="Class description")


class PropertySuggestion(BaseModel):
    """Suggestion for ontology property"""
    property_name: str = Field(..., description="Suggested property name")
    property_type: str = Field(..., description="Property type (ObjectProperty, DataProperty, etc.)")
    domain: Optional[str] = Field(default=None, description="Property domain")
    range: Optional[str] = Field(default=None, description="Property range")
    description: str = Field(..., description="Property description")


class RelationshipSuggestion(BaseModel):
    """Suggestion for relationships between entities"""
    source_entity: str = Field(..., description="Source entity")
    target_entity: str = Field(..., description="Target entity")
    relationship_type: str = Field(..., description="Type of relationship")
    description: str = Field(..., description="Relationship description")
    inverse_relationship: Optional[str] = Field(default=None, description="Inverse relationship if applicable")


class EnhancementSuggestion(BaseModel):
    """Suggestion for enhancing existing ontology"""
    target_element: str = Field(..., description="Element to enhance")
    enhancement_type: str = Field(..., description="Type of enhancement")
    description: str = Field(..., description="Enhancement description")
    implementation_steps: List[str] = Field(default_factory=list, description="Steps to implement")


# Demo suggestions for testing
DEMO_SUGGESTIONS = {
    "ontology_class": [
        AISuggestion(
            id="cls_001",
            type=SuggestionType.ONTOLOGY_CLASS,
            title="Customer Entity Class",
            description="A comprehensive class to represent customer entities with their attributes and relationships",
            confidence=0.92,
            implementation={
                "class_name": "Customer",
                "namespace": "business",
                "parent_class": "Person",
                "properties": ["email", "customerID", "registrationDate", "loyaltyStatus"]
            },
            rationale="Based on the data context, customers are central entities that need proper ontological representation",
            tags=["customer", "business", "entity"]
        ),
        AISuggestion(
            id="cls_002", 
            type=SuggestionType.ONTOLOGY_CLASS,
            title="Order Transaction Class",
            description="Represents order transactions with temporal and financial aspects",
            confidence=0.88,
            implementation={
                "class_name": "Order",
                "namespace": "business",
                "parent_class": "Transaction",
                "properties": ["orderID", "orderDate", "totalAmount", "status"]
            },
            rationale="Orders are key business events that connect customers to products and services",
            tags=["order", "transaction", "business"]
        )
    ],
    "property": [
        AISuggestion(
            id="prop_001",
            type=SuggestionType.PROPERTY,
            title="hasCustomer Object Property",
            description="Links orders to customers who placed them",
            confidence=0.95,
            implementation={
                "property_name": "hasCustomer",
                "property_type": "ObjectProperty",
                "domain": "Order",
                "range": "Customer"
            },
            rationale="Essential relationship between orders and customers for data lineage",
            tags=["relationship", "customer", "order"]
        )
    ],
    "relationship": [
        AISuggestion(
            id="rel_001",
            type=SuggestionType.RELATIONSHIP,
            title="Customer-Order Relationship",
            description="One-to-many relationship between customers and their orders",
            confidence=0.93,
            implementation={
                "source_entity": "Customer",
                "target_entity": "Order",
                "relationship_type": "hasOrder",
                "cardinality": "1:n"
            },
            rationale="Fundamental business relationship for tracking customer behavior",
            tags=["customer", "order", "business-logic"]
        )
    ]
} 