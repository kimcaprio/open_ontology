"""
Ontology Management Models
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field


class OntologyStatus(str, Enum):
    """Ontology status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PRODUCTION = "production"
    ARCHIVED = "archived"


class OntologyDomainType(str, Enum):
    """Ontology domain types"""
    CUSTOMER = "customer"
    PRODUCT = "product"
    FINANCIAL = "financial"
    OPERATIONS = "operations"
    ANALYTICS = "analytics"
    CUSTOM = "custom"


class OntologyEntityType(str, Enum):
    """Ontology entity types"""
    TABLE = "table"
    VIEW = "view" 
    STORED_PROCEDURE = "stored_procedure"
    FUNCTION = "function"


class OntologyRelationType(str, Enum):
    """Ontology relationship types"""
    FOREIGN_KEY = "foreign_key"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"
    COMPOSITION = "composition"
    AGGREGATION = "aggregation"
    INHERITANCE = "inheritance"


class OntologyProperty(BaseModel):
    """Ontology property model"""
    name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key: bool = False
    default_value: Optional[str] = None
    description: Optional[str] = None
    constraints: List[str] = []
    tags: List[str] = []


class OntologyEntity(BaseModel):
    """Ontology entity model"""
    id: str
    name: str
    type: OntologyEntityType
    description: Optional[str] = None
    properties: List[OntologyProperty] = []
    source_table: Optional[str] = None
    source_database: Optional[str] = None
    source_data_source: Optional[str] = None
    row_count: Optional[int] = None
    tags: List[str] = []
    position: Dict[str, float] = {"x": 0, "y": 0}  # For visualization
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OntologyRelationship(BaseModel):
    """Ontology relationship model"""
    id: str
    name: str
    type: OntologyRelationType
    source_entity_id: str
    target_entity_id: str
    source_property: Optional[str] = None  # For FK relationships
    target_property: Optional[str] = None  # For FK relationships
    description: Optional[str] = None
    cardinality: Optional[str] = None  # e.g., "1:N", "N:M"
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OntologyDomain(BaseModel):
    """Ontology domain model representing a business domain"""
    id: str
    name: str
    description: Optional[str] = None
    entities: List[OntologyEntity] = []
    relationships: List[OntologyRelationship] = []
    data_source_id: Optional[str] = None
    database_name: Optional[str] = None
    tags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_sync_at: Optional[datetime] = None


class OntologyStats(BaseModel):
    """Ontology statistics model"""
    total_domains: int = 0
    total_entities: int = 0
    total_relationships: int = 0
    total_properties: int = 0
    data_sources_covered: int = 0
    last_updated: Optional[datetime] = None


class OntologyVisualizationNode(BaseModel):
    """Node for visualization"""
    id: str
    label: str
    type: str
    properties: Dict[str, Any] = {}
    position: Dict[str, float] = {"x": 0, "y": 0}
    size: int = 1
    color: Optional[str] = None


class OntologyVisualizationEdge(BaseModel):
    """Edge for visualization"""
    id: str
    source: str
    target: str
    label: str
    type: str
    properties: Dict[str, Any] = {}


class OntologyVisualizationData(BaseModel):
    """Complete visualization data"""
    nodes: List[OntologyVisualizationNode] = []
    edges: List[OntologyVisualizationEdge] = []
    layout: str = "force"  # force, hierarchical, circular
    metadata: Dict[str, Any] = {}


class Ontology(BaseModel):
    """Ontology definition"""
    id: str = Field(..., description="Ontology ID")
    name: str = Field(..., description="Ontology name")
    description: Optional[str] = Field(default=None, description="Ontology description")
    domain: Optional[str] = Field(default=None, description="Ontology domain")
    status: OntologyStatus = Field(default=OntologyStatus.DRAFT, description="Ontology status")
    entities: List[OntologyEntity] = Field(default_factory=list, description="Ontology entities")
    relationships: List[OntologyRelationship] = Field(default_factory=list, description="Ontology relationships")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    created_by: Optional[str] = Field(default="system", description="Creator")


class CreateOntologyRequest(BaseModel):
    """Request to create new ontology"""
    name: str = Field(..., description="Ontology name")
    description: Optional[str] = Field(default=None, description="Ontology description")
    domain: Optional[str] = Field(default=None, description="Ontology domain")
    auto_generate: bool = Field(default=False, description="Auto-generate from data sources")
    data_sources: List[str] = Field(default_factory=list, description="Selected data sources for auto-generation")


class UpdateOntologyRequest(BaseModel):
    """Request to update ontology"""
    name: Optional[str] = Field(default=None, description="Ontology name")
    description: Optional[str] = Field(default=None, description="Ontology description")
    domain: Optional[str] = Field(default=None, description="Ontology domain")
    status: Optional[OntologyStatus] = Field(default=None, description="Ontology status")


class OntologyListResponse(BaseModel):
    """Response for ontology list"""
    ontologies: List[Ontology] = Field(..., description="List of ontologies")
    total: int = Field(..., description="Total number of ontologies")


# Demo ontologies
DEMO_ONTOLOGIES = [
    Ontology(
        id="customer-domain",
        name="Customer Domain",
        description="Customer entities and relationships",
        domain="customer",
        status=OntologyStatus.ACTIVE,
        entities=[
            OntologyEntity(
                id="customer_entity",
                name="Customer",
                type=OntologyEntityType.TABLE,
                description="Represents a customer in the system",
                properties=[
                    OntologyProperty(name="customer_id", data_type="int"),
                    OntologyProperty(name="email", data_type="varchar"),
                    OntologyProperty(name="first_name", data_type="varchar"),
                    OntologyProperty(name="last_name", data_type="varchar")
                ],
                source_table="customers"
            ),
            OntologyEntity(
                id="order_entity",
                name="Order",
                type=OntologyEntityType.TABLE,
                description="Represents an order placed by a customer",
                properties=[
                    OntologyProperty(name="order_id", data_type="int"),
                    OntologyProperty(name="customer_id", data_type="int"),
                    OntologyProperty(name="order_date", data_type="date"),
                    OntologyProperty(name="total_amount", data_type="decimal")
                ],
                source_table="orders"
            )
        ],
        relationships=[
            OntologyRelationship(
                id="customer_order_rel",
                name="places",
                type=OntologyRelationType.ONE_TO_MANY,
                source_entity_id="customer_entity",
                target_entity_id="order_entity",
                description="Customer places orders"
            )
        ],
        metadata={"entity_count": 12, "relationship_count": 8}
    ),
    Ontology(
        id="product-catalog",
        name="Product Catalog",
        description="Product hierarchy and attributes",
        domain="product",
        status=OntologyStatus.DRAFT,
        entities=[
            OntologyEntity(
                id="product_entity",
                name="Product",
                type=OntologyEntityType.TABLE,
                description="Represents a product in the catalog",
                properties=[
                    OntologyProperty(name="product_id", data_type="int"),
                    OntologyProperty(name="name", data_type="varchar"),
                    OntologyProperty(name="price", data_type="decimal"),
                    OntologyProperty(name="category", data_type="varchar")
                ],
                source_table="products"
            )
        ],
        relationships=[],
        metadata={"entity_count": 24, "relationship_count": 15}
    ),
    Ontology(
        id="financial-data",
        name="Financial Data",
        description="Financial entities and metrics",
        domain="financial",
        status=OntologyStatus.PRODUCTION,
        entities=[
            OntologyEntity(
                id="transaction_entity",
                name="Transaction",
                type=OntologyEntityType.TABLE,
                description="Represents a financial transaction",
                properties=[
                    OntologyProperty(name="transaction_id", data_type="int"),
                    OntologyProperty(name="amount", data_type="decimal"),
                    OntologyProperty(name="date", data_type="date"),
                    OntologyProperty(name="type", data_type="varchar")
                ],
                source_table="transactions"
            )
        ],
        relationships=[],
        metadata={"entity_count": 18, "relationship_count": 22}
    )
] 