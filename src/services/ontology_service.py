"""
Ontology Service - Converts catalog metadata to ontology representation
"""

import uuid
import math
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict

from src.models.ontology import (
    OntologyDomain, OntologyEntity, OntologyRelationship, OntologyProperty,
    OntologyEntityType, OntologyRelationType, OntologyStats,
    OntologyVisualizationData, OntologyVisualizationNode, OntologyVisualizationEdge
)
from src.services.catalog_service import catalog_service
from src.config.logging_config import get_service_logger

class OntologyService:
    """Service for managing ontology data from catalog sources"""
    
    def __init__(self):
        self.logger = get_service_logger("ontology")
        self.ontology_domains = {}  # In-memory storage
        
    async def get_ontology_stats(self) -> OntologyStats:
        """Get ontology statistics"""
        try:
            total_domains = len(self.ontology_domains)
            total_entities = sum(len(domain.entities) for domain in self.ontology_domains.values())
            total_relationships = sum(len(domain.relationships) for domain in self.ontology_domains.values())
            total_properties = sum(
                sum(len(entity.properties) for entity in domain.entities)
                for domain in self.ontology_domains.values()
            )
            
            # Get unique data sources
            data_sources = set()
            for domain in self.ontology_domains.values():
                if domain.data_source_id:
                    data_sources.add(domain.data_source_id)
            
            return OntologyStats(
                total_domains=total_domains,
                total_entities=total_entities,
                total_relationships=total_relationships,
                total_properties=total_properties,
                data_sources_covered=len(data_sources),
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get ontology stats: {str(e)}")
            raise
    
    async def get_ontology_domains(self) -> List[OntologyDomain]:
        """Get all ontology domains"""
        try:
            return list(self.ontology_domains.values())
        except Exception as e:
            self.logger.error(f"Failed to get ontology domains: {str(e)}")
            raise
    
    async def get_ontology_domain(self, domain_id: str) -> Optional[OntologyDomain]:
        """Get specific ontology domain"""
        try:
            return self.ontology_domains.get(domain_id)
        except Exception as e:
            self.logger.error(f"Failed to get ontology domain {domain_id}: {str(e)}")
            raise
    
    async def sync_from_catalog(self, data_source_id: Optional[str] = None) -> Dict[str, Any]:
        """Sync ontology from catalog data"""
        try:
            self.logger.info("Starting ontology sync from catalog")
            
            # Get catalog tree
            catalog_tree = await catalog_service.get_catalog_tree()
            
            domains_created = 0
            entities_created = 0
            relationships_created = 0
            
            for data_source in catalog_tree.data_sources:
                # Skip if specific data source requested
                if data_source_id and data_source.id != data_source_id:
                    continue
                
                for database in data_source.databases:
                    # Create domain for each database
                    domain = await self._create_domain_from_database(data_source, database)
                    self.ontology_domains[domain.id] = domain
                    
                    domains_created += 1
                    entities_created += len(domain.entities)
                    relationships_created += len(domain.relationships)
            
            result = {
                "success": True,
                "message": "Ontology sync completed",
                "stats": {
                    "domains_created": domains_created,
                    "entities_created": entities_created,
                    "relationships_created": relationships_created
                }
            }
            
            self.logger.success(f"Ontology sync completed: {domains_created} domains, {entities_created} entities")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to sync ontology from catalog: {str(e)}")
            return {
                "success": False,
                "message": f"Sync failed: {str(e)}"
            }
    
    async def _create_domain_from_database(self, data_source, database) -> OntologyDomain:
        """Create ontology domain from catalog database"""
        domain_id = f"{data_source.id}_{database.name}"
        
        # Convert tables to entities
        entities = []
        entity_map = {}  # table_name -> entity_id
        
        for table in database.tables:
            entity = await self._create_entity_from_table(data_source, database, table)
            entities.append(entity)
            entity_map[table.name] = entity.id
        
        # Detect relationships from foreign keys
        relationships = await self._detect_relationships(data_source, database, entities, entity_map)
        
        # Add Chinook-specific business relationships
        if database.name.lower() in ['chinook', 'ontology_dev']:
            relationships.extend(await self._add_chinook_business_relationships(entity_map))
        
        return OntologyDomain(
            id=domain_id,
            name=f"{data_source.name} - {database.name}",
            description=f"Ontology domain for {database.name} database from {data_source.name}",
            entities=entities,
            relationships=relationships,
            data_source_id=data_source.id,
            database_name=database.name,
            tags=[data_source.type, "auto-generated"],
            last_sync_at=datetime.utcnow()
        )
    
    async def _create_entity_from_table(self, data_source, database, table) -> OntologyEntity:
        """Create ontology entity from catalog table"""
        entity_id = f"{data_source.id}_{database.name}_{table.name}"
        
        # Convert columns to properties
        properties = []
        for column in table.columns:
            prop = OntologyProperty(
                name=column.name,
                data_type=column.data_type,
                nullable=column.nullable,
                primary_key=column.primary_key,
                foreign_key=column.foreign_key,
                default_value=column.default_value,
                description=column.description,
                tags=column.tags
            )
            properties.append(prop)
        
        # Determine entity position for visualization (circular layout)
        position = self._calculate_entity_position(len(properties))
        
        return OntologyEntity(
            id=entity_id,
            name=table.name,
            type=OntologyEntityType.TABLE,
            description=table.description or f"Entity representing {table.name} table",
            properties=properties,
            source_table=table.name,
            source_database=database.name,
            source_data_source=data_source.id,
            row_count=table.row_count,
            tags=table.tags + [database.name, data_source.name],
            position=position
        )
    
    async def _detect_relationships(self, data_source, database, entities, entity_map) -> List[OntologyRelationship]:
        """Detect relationships from foreign key constraints"""
        relationships = []
        
        # Build table structure map
        table_map = {table.name: table for table in database.tables}
        
        for entity in entities:
            table_name = entity.source_table
            table = table_map.get(table_name)
            
            if not table:
                continue
            
            # Check for foreign key relationships
            for column in table.columns:
                if column.foreign_key:
                    # Try to detect referenced table from column name patterns
                    referenced_table = self._infer_referenced_table(column.name, table_map.keys())
                    
                    if referenced_table and referenced_table in entity_map:
                        rel_id = f"{entity.id}_{entity_map[referenced_table]}_{column.name}"
                        
                        relationship = OntologyRelationship(
                            id=rel_id,
                            name=f"{table_name}_references_{referenced_table}",
                            type=OntologyRelationType.FOREIGN_KEY,
                            source_entity_id=entity.id,
                            target_entity_id=entity_map[referenced_table],
                            source_property=column.name,
                            target_property="id",  # Assume primary key is 'id'
                            description=f"{table_name} references {referenced_table}",
                            cardinality="N:1"
                        )
                        relationships.append(relationship)
        
        return relationships
    
    async def _add_chinook_business_relationships(self, entity_map) -> List[OntologyRelationship]:
        """Add Chinook-specific business relationships"""
        relationships = []
        
        # Define Chinook relationships
        chinook_relationships = [
            ("Artist", "Album", "creates", "1:N"),
            ("Album", "Track", "contains", "1:N"),
            ("Customer", "Invoice", "places", "1:N"),
            ("Invoice", "InvoiceLine", "contains", "1:N"),
            ("Track", "InvoiceLine", "sold_in", "1:N"),
            ("Genre", "Track", "categorizes", "1:N"),
            ("MediaType", "Track", "defines_format", "1:N"),
            ("Employee", "Customer", "supports", "1:N"),
            ("Playlist", "PlaylistTrack", "contains", "1:N"),
            ("Track", "PlaylistTrack", "included_in", "1:N")
        ]
        
        for source_table, target_table, relation_name, cardinality in chinook_relationships:
            # Find entity IDs
            source_entity_id = None
            target_entity_id = None
            
            for table_name, entity_id in entity_map.items():
                if table_name.lower() == source_table.lower():
                    source_entity_id = entity_id
                elif table_name.lower() == target_table.lower():
                    target_entity_id = entity_id
            
            if source_entity_id and target_entity_id:
                rel_id = f"{source_entity_id}_{target_entity_id}_{relation_name}"
                
                # Determine relationship type from cardinality
                if cardinality == "1:N":
                    rel_type = OntologyRelationType.ONE_TO_MANY
                elif cardinality == "N:1":
                    rel_type = OntologyRelationType.MANY_TO_ONE
                elif cardinality == "N:M":
                    rel_type = OntologyRelationType.MANY_TO_MANY
                else:
                    rel_type = OntologyRelationType.FOREIGN_KEY
                
                relationship = OntologyRelationship(
                    id=rel_id,
                    name=relation_name,
                    type=rel_type,
                    source_entity_id=source_entity_id,
                    target_entity_id=target_entity_id,
                    description=f"{source_table} {relation_name} {target_table}",
                    cardinality=cardinality,
                    tags=["business_rule", "chinook"]
                )
                relationships.append(relationship)
        
        return relationships
    
    def _infer_referenced_table(self, column_name: str, table_names: List[str]) -> Optional[str]:
        """Infer referenced table from foreign key column name"""
        # Common patterns: CustomerId -> Customer, ArtistId -> Artist
        if column_name.lower().endswith('id'):
            base_name = column_name[:-2]  # Remove 'Id'
            
            # Look for exact match
            for table_name in table_names:
                if table_name.lower() == base_name.lower():
                    return table_name
            
            # Look for partial match
            for table_name in table_names:
                if base_name.lower() in table_name.lower():
                    return table_name
        
        return None
    
    def _calculate_entity_position(self, property_count: int) -> Dict[str, float]:
        """Calculate entity position for visualization"""
        # Simple circular layout based on property count
        angle = (property_count * 137.5) % 360  # Golden angle distribution
        radius = 200 + (property_count * 10)  # Vary radius by complexity
        
        x = radius * math.cos(math.radians(angle))
        y = radius * math.sin(math.radians(angle))
        
        return {"x": x, "y": y}
    
    async def get_visualization_data(self, domain_id: str) -> Optional[OntologyVisualizationData]:
        """Get visualization data for a specific domain"""
        try:
            domain = self.ontology_domains.get(domain_id)
            if not domain:
                return None
            
            # Convert entities to nodes
            nodes = []
            for entity in domain.entities:
                node = OntologyVisualizationNode(
                    id=entity.id,
                    label=entity.name,
                    type=entity.type.value,
                    properties={
                        "table_name": entity.source_table,
                        "row_count": entity.row_count,
                        "property_count": len(entity.properties),
                        "tags": entity.tags
                    },
                    position=entity.position,
                    size=max(1, len(entity.properties) // 3),  # Size based on complexity
                    color=self._get_entity_color(entity.type)
                )
                nodes.append(node)
            
            # Convert relationships to edges
            edges = []
            for relationship in domain.relationships:
                edge = OntologyVisualizationEdge(
                    id=relationship.id,
                    source=relationship.source_entity_id,
                    target=relationship.target_entity_id,
                    label=relationship.name,
                    type=relationship.type.value,
                    properties={
                        "cardinality": relationship.cardinality,
                        "description": relationship.description,
                        "tags": relationship.tags
                    }
                )
                edges.append(edge)
            
            return OntologyVisualizationData(
                nodes=nodes,
                edges=edges,
                layout="force",
                metadata={
                    "domain_name": domain.name,
                    "entity_count": len(nodes),
                    "relationship_count": len(edges),
                    "data_source": domain.data_source_id,
                    "database": domain.database_name
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get visualization data for {domain_id}: {str(e)}")
            return None
    
    def _get_entity_color(self, entity_type: OntologyEntityType) -> str:
        """Get color for entity type"""
        color_map = {
            OntologyEntityType.TABLE: "#3498db",      # Blue
            OntologyEntityType.VIEW: "#2ecc71",       # Green
            OntologyEntityType.STORED_PROCEDURE: "#e74c3c",  # Red
            OntologyEntityType.FUNCTION: "#f39c12"    # Orange
        }
        return color_map.get(entity_type, "#95a5a6")  # Default gray

    # === AI SUGGESTIONS SERVICE METHODS ===
    
    async def add_entity_to_domain(
        self, 
        domain_id: str, 
        entity_name: str, 
        entity_description: Optional[str] = None,
        entity_properties: Optional[List[str]] = None,
        entity_type: str = "table",
        is_ai_suggested: bool = False
    ) -> Dict[str, Any]:
        """Add a new entity to a domain"""
        try:
            self.logger.info(f"Adding entity '{entity_name}' to domain {domain_id}")
            
            domain = self.ontology_domains.get(domain_id)
            if not domain:
                return {"success": False, "message": "Domain not found"}
            
            # Check for duplicate entity names
            existing_entity = next((e for e in domain.entities if e.name.lower() == entity_name.lower()), None)
            if existing_entity:
                return {"success": False, "message": f"Entity '{entity_name}' already exists in domain"}
            
            # Create entity ID
            entity_id = f"{domain_id}_{entity_name.lower().replace(' ', '_')}"
            
            # Convert properties list to OntologyProperty objects
            properties = []
            if entity_properties:
                for prop_name in entity_properties:
                    prop = OntologyProperty(
                        name=prop_name,
                        data_type="varchar",  # Default type
                        nullable=True,
                        primary_key=(prop_name.lower() == "id"),
                        description=f"AI-suggested property: {prop_name}"
                    )
                    properties.append(prop)
            
            # Determine entity type
            try:
                ontology_entity_type = OntologyEntityType(entity_type.lower())
            except ValueError:
                ontology_entity_type = OntologyEntityType.TABLE
            
            # Calculate position for new entity
            position = self._calculate_entity_position(len(domain.entities))
            
            # Create new entity
            new_entity = OntologyEntity(
                id=entity_id,
                name=entity_name,
                type=ontology_entity_type,
                description=entity_description or f"AI-suggested entity: {entity_name}",
                properties=properties,
                source_table=entity_name.lower().replace(' ', '_'),
                source_database=domain.database_name,
                source_data_source=domain.data_source_id,
                tags=["ai-suggested"] if is_ai_suggested else [],
                position=position
            )
            
            # Add entity to domain
            domain.entities.append(new_entity)
            domain.updated_at = datetime.utcnow()
            
            # Update domain in storage
            self.ontology_domains[domain_id] = domain
            
            self.logger.success(f"Entity '{entity_name}' added successfully to domain {domain_id}")
            
            return {
                "success": True,
                "message": f"Entity '{entity_name}' added successfully",
                "entity_id": entity_id,
                "stats": {
                    "entities_count": len(domain.entities),
                    "relationships_count": len(domain.relationships)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to add entity to domain {domain_id}: {str(e)}")
            return {"success": False, "message": f"Failed to add entity: {str(e)}"}
    
    async def update_entity(
        self, 
        domain_id: str, 
        entity_id: str, 
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing entity"""
        try:
            self.logger.info(f"Updating entity {entity_id} in domain {domain_id}")
            
            domain = self.ontology_domains.get(domain_id)
            if not domain:
                return {"success": False, "message": "Domain not found"}
            
            # Find entity
            entity = next((e for e in domain.entities if e.id == entity_id), None)
            if not entity:
                return {"success": False, "message": "Entity not found"}
            
            # Apply updates
            if "name" in updates:
                entity.name = updates["name"]
            if "description" in updates:
                entity.description = updates["description"]
            if "properties" in updates and updates["properties"]:
                # Convert property names to OntologyProperty objects
                new_properties = []
                for prop_name in updates["properties"]:
                    prop = OntologyProperty(
                        name=prop_name,
                        data_type="varchar",
                        nullable=True,
                        description=f"Updated property: {prop_name}"
                    )
                    new_properties.append(prop)
                entity.properties = new_properties
            
            domain.updated_at = datetime.utcnow()
            self.ontology_domains[domain_id] = domain
            
            self.logger.success(f"Entity {entity_id} updated successfully")
            
            return {
                "success": True,
                "message": "Entity updated successfully",
                "stats": {
                    "entities_count": len(domain.entities),
                    "relationships_count": len(domain.relationships)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to update entity {entity_id}: {str(e)}")
            return {"success": False, "message": f"Failed to update entity: {str(e)}"}
    
    async def add_relationship_to_domain(
        self,
        domain_id: str,
        relationship_name: str,
        relationship_description: Optional[str] = None,
        source_entity_id: str = None,
        target_entity_id: str = None,
        cardinality: str = "one-to-many",
        is_ai_suggested: bool = False
    ) -> Dict[str, Any]:
        """Add a new relationship to a domain"""
        try:
            self.logger.info(f"Adding relationship '{relationship_name}' to domain {domain_id}")
            
            domain = self.ontology_domains.get(domain_id)
            if not domain:
                return {"success": False, "message": "Domain not found"}
            
            # Validate entities exist
            source_entity = next((e for e in domain.entities if e.id == source_entity_id), None)
            target_entity = next((e for e in domain.entities if e.id == target_entity_id), None)
            
            if not source_entity:
                return {"success": False, "message": "Source entity not found"}
            if not target_entity:
                return {"success": False, "message": "Target entity not found"}
            
            # Check for duplicate relationships
            existing_rel = next((r for r in domain.relationships 
                               if r.source_entity_id == source_entity_id 
                               and r.target_entity_id == target_entity_id 
                               and r.name.lower() == relationship_name.lower()), None)
            if existing_rel:
                return {"success": False, "message": f"Relationship '{relationship_name}' already exists between these entities"}
            
            # Create relationship ID
            relationship_id = f"{source_entity_id}_{target_entity_id}_{relationship_name.lower().replace(' ', '_')}"
            
            # Determine relationship type from cardinality
            rel_type_map = {
                "one-to-one": OntologyRelationType.ONE_TO_ONE,
                "one-to-many": OntologyRelationType.ONE_TO_MANY,
                "many-to-one": OntologyRelationType.MANY_TO_ONE,
                "many-to-many": OntologyRelationType.MANY_TO_MANY
            }
            rel_type = rel_type_map.get(cardinality.lower(), OntologyRelationType.ONE_TO_MANY)
            
            # Create new relationship
            new_relationship = OntologyRelationship(
                id=relationship_id,
                name=relationship_name,
                type=rel_type,
                source_entity_id=source_entity_id,
                target_entity_id=target_entity_id,
                description=relationship_description or f"AI-suggested relationship: {relationship_name}",
                cardinality=cardinality,
                tags=["ai-suggested"] if is_ai_suggested else []
            )
            
            # Add relationship to domain
            domain.relationships.append(new_relationship)
            domain.updated_at = datetime.utcnow()
            
            # Update domain in storage
            self.ontology_domains[domain_id] = domain
            
            self.logger.success(f"Relationship '{relationship_name}' added successfully to domain {domain_id}")
            
            return {
                "success": True,
                "message": f"Relationship '{relationship_name}' added successfully",
                "relationship_id": relationship_id,
                "stats": {
                    "entities_count": len(domain.entities),
                    "relationships_count": len(domain.relationships)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to add relationship to domain {domain_id}: {str(e)}")
            return {"success": False, "message": f"Failed to add relationship: {str(e)}"}
    
    async def delete_entity(self, domain_id: str, entity_id: str) -> Dict[str, Any]:
        """Delete an entity from a domain"""
        try:
            self.logger.info(f"Deleting entity {entity_id} from domain {domain_id}")
            
            domain = self.ontology_domains.get(domain_id)
            if not domain:
                return {"success": False, "message": "Domain not found"}
            
            # Find and remove entity
            entity_index = next((i for i, e in enumerate(domain.entities) if e.id == entity_id), None)
            if entity_index is None:
                return {"success": False, "message": "Entity not found"}
            
            # Remove entity
            removed_entity = domain.entities.pop(entity_index)
            
            # Remove all relationships involving this entity
            domain.relationships = [r for r in domain.relationships 
                                 if r.source_entity_id != entity_id and r.target_entity_id != entity_id]
            
            domain.updated_at = datetime.utcnow()
            self.ontology_domains[domain_id] = domain
            
            self.logger.success(f"Entity {entity_id} deleted successfully")
            
            return {
                "success": True,
                "message": f"Entity '{removed_entity.name}' deleted successfully",
                "stats": {
                    "entities_count": len(domain.entities),
                    "relationships_count": len(domain.relationships)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to delete entity {entity_id}: {str(e)}")
            return {"success": False, "message": f"Failed to delete entity: {str(e)}"}
    
    async def delete_relationship(self, domain_id: str, relationship_id: str) -> Dict[str, Any]:
        """Delete a relationship from a domain"""
        try:
            self.logger.info(f"Deleting relationship {relationship_id} from domain {domain_id}")
            
            domain = self.ontology_domains.get(domain_id)
            if not domain:
                return {"success": False, "message": "Domain not found"}
            
            # Find and remove relationship
            rel_index = next((i for i, r in enumerate(domain.relationships) if r.id == relationship_id), None)
            if rel_index is None:
                return {"success": False, "message": "Relationship not found"}
            
            # Remove relationship
            removed_relationship = domain.relationships.pop(rel_index)
            
            domain.updated_at = datetime.utcnow()
            self.ontology_domains[domain_id] = domain
            
            self.logger.success(f"Relationship {relationship_id} deleted successfully")
            
            return {
                "success": True,
                "message": f"Relationship '{removed_relationship.name}' deleted successfully",
                "stats": {
                    "entities_count": len(domain.entities),
                    "relationships_count": len(domain.relationships)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to delete relationship {relationship_id}: {str(e)}")
            return {"success": False, "message": f"Failed to delete relationship: {str(e)}"}

# Global service instance
ontology_service = OntologyService() 