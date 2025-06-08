"""
Natural Language to SQL Service
Converts natural language queries to SQL using the Unified LLM Service
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from src.services.unified_llm_service import unified_llm_service, LLMResponse

# Set up logging
logger = logging.getLogger(__name__)

class SQLQueryResponse(BaseModel):
    """Structured response for SQL generation"""
    sql_query: str = Field(description="The generated SQL query only")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    suggested_catalog: Optional[str] = Field(default=None, description="Suggested catalog if not specified")
    suggested_schema: Optional[str] = Field(default=None, description="Suggested schema if not specified")
    tables_used: List[str] = Field(default_factory=list, description="List of tables used in the query")

class NaturalLanguageQueryResponse(BaseModel):
    sql_query: str
    explanation: str
    confidence: float
    suggested_catalog: Optional[str] = None
    suggested_schema: Optional[str] = None

class NL2SQLService:
    """Service for converting natural language to SQL using Unified LLM Service"""
    
    def __init__(self, default_model_key: Optional[str] = None):
        self.default_model_key = default_model_key
    
    async def convert_natural_language_to_sql(
        self,
        natural_query: str,
        catalog_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        model_key: Optional[str] = None
    ) -> NaturalLanguageQueryResponse:
        """
        Convert natural language query to SQL
        """
        try:
            # Create prompt with context
            messages = self._create_nl2sql_messages(
                natural_query=natural_query,
                catalog_context=catalog_context,
                conversation_history=conversation_history or []
            )
            
            # Get LLM response using unified service with structured format
            model_key = model_key or self.default_model_key
            response = await unified_llm_service.generate_structured_completion(
                messages=messages,
                response_model=SQLQueryResponse,
                model_key=model_key,
                temperature=0.1,
                max_tokens=1500
            )
            
            # Parse response
            parsed_response = self._parse_structured_response(response, natural_query)
            
            return parsed_response
            
        except Exception as e:
            logger.error(f"Error in convert_natural_language_to_sql: {str(e)}")
            # Return fallback response
            return NaturalLanguageQueryResponse(
                sql_query="SELECT 'Error converting natural language to SQL' as error",
                explanation=f"Failed to convert query due to error: {str(e)}",
                confidence=0.0,
                suggested_catalog=None,
                suggested_schema=None
            )
    
    def _create_nl2sql_messages(
        self,
        natural_query: str,
        catalog_context: Optional[Dict[str, Any]] = None,
        conversation_history: List[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        """Create messages for natural language to SQL conversion"""
        
        # Enhanced system message with comprehensive schema awareness
        system_content = """You are an expert SQL query generator for Trino/Presto distributed databases with Unity Catalog support.
Your ONLY task is to convert natural language queries to valid SQL statements based on the provided schema information.

CRITICAL RULES:
1. Generate ONLY the SQL query - no explanations, no comments, no additional text
2. Use proper Trino/Presto SQL syntax
3. ALWAYS use fully qualified table names (catalog.schema.table) when schema context is available
4. Add appropriate LIMIT clauses for potentially large result sets (default LIMIT 100)
5. Use proper JOIN syntax and WHERE clauses as needed
6. Confidence score should reflect query clarity and available schema match
7. If no exact table match, suggest the closest available table and adjust confidence accordingly
8. For aggregation queries, use appropriate GROUP BY and ORDER BY clauses
9. Handle date/time queries with proper Trino date functions
10. Use CASE statements for conditional logic when needed

RESPONSE FORMAT - Respond ONLY with this JSON structure:
{
    "sql_query": "SELECT column1, column2 FROM catalog.schema.table WHERE condition LIMIT 100",
    "confidence": 0.95,
    "suggested_catalog": "catalog_name_if_needed",
    "suggested_schema": "schema_name_if_needed", 
    "tables_used": ["table1", "table2"]
}

COMMON PATTERNS:
- Count queries: SELECT COUNT(*) FROM catalog.schema.table
- Top N queries: SELECT * FROM catalog.schema.table ORDER BY column DESC LIMIT N
- Aggregation: SELECT group_col, COUNT(*), SUM(amount) FROM table GROUP BY group_col ORDER BY COUNT(*) DESC
- Date filters: WHERE date_column >= CURRENT_DATE - INTERVAL '7' DAY
- JOINs: SELECT t1.*, t2.* FROM table1 t1 JOIN table2 t2 ON t1.id = t2.foreign_id
- Text search: WHERE LOWER(column) LIKE LOWER('%search_term%')
"""
        
        messages = [{"role": "system", "content": system_content}]
        
        # Add conversation history if available (limited to last 3 exchanges)
        if conversation_history:
            for entry in conversation_history[-3:]:
                if entry.get('user'):
                    messages.append({"role": "user", "content": entry['user']})
                if entry.get('assistant'):
                    messages.append({"role": "assistant", "content": entry['assistant']})
        
        # Create comprehensive user message with schema context
        user_content = f'Convert to SQL: "{natural_query}"\n\n'
        
        # Handle different types of catalog context
        if catalog_context:
            if "catalogs" in catalog_context and catalog_context["catalogs"]:
                # Full schema context from get_full_schema_context()
                user_content += self._format_full_schema_context(catalog_context)
                
            elif "catalog" in catalog_context and "schema" in catalog_context:
                # Specific catalog/schema context with table details
                user_content += self._format_specific_schema_context(catalog_context)
                
            elif "available_catalogs" in catalog_context:
                # Basic catalog listing
                user_content += self._format_catalog_list_context(catalog_context)
                
        else:
            user_content += """
NO SCHEMA INFORMATION AVAILABLE
- Use generic table names and suggest appropriate catalog/schema
- Set confidence score lower (0.3-0.5) due to lack of schema information
- Suggest catalog='memory' and schema='default' for basic queries
"""
        
        messages.append({"role": "user", "content": user_content})
        
        return messages
    
    def _format_full_schema_context(self, catalog_context: Dict[str, Any]) -> str:
        """Format full schema context for LLM (from get_full_schema_context)"""
        context_lines = [
            "=== AVAILABLE DATABASE SCHEMA ===",
            f"Total: {catalog_context.get('total_catalogs', 0)} catalogs, "
            f"{catalog_context.get('total_schemas', 0)} schemas, "
            f"{catalog_context.get('total_tables', 0)} tables\n"
        ]
        
        for catalog in catalog_context.get("catalogs", []):
            context_lines.append(f"📁 CATALOG: {catalog['name']}")
            if catalog.get("comment"):
                context_lines.append(f"   Description: {catalog['comment']}")
            
            for schema in catalog.get("schemas", []):
                context_lines.append(f"  📂 SCHEMA: {catalog['name']}.{schema['name']}")
                
                for table in schema.get("tables", []):
                    context_lines.append(f"    📋 TABLE: {table['full_name']}")
                    
                    # Add column information
                    columns_info = []
                    for col in table.get("columns", []):
                        col_desc = f"{col['name']} ({col['type']})"
                        if col.get("comment"):
                            col_desc += f" - {col['comment']}"
                        columns_info.append(col_desc)
                    
                    if columns_info:
                        context_lines.append(f"       Columns: {', '.join(columns_info[:8])}")  # Limit columns shown
                        if len(table.get("columns", [])) > 8:
                            context_lines.append(f"       ... and {len(table['columns']) - 8} more columns")
                    
                    context_lines.append("")  # Empty line between tables
        
        context_lines.extend([
            "=== REQUIREMENTS ===",
            "- MUST use fully qualified table names (catalog.schema.table)",
            "- Add LIMIT 100 for potentially large result sets",
            "- Use exact column names as shown above",
            "- Match user intent to appropriate tables/columns",
            f"- Available catalogs: {', '.join([cat['name'] for cat in catalog_context.get('catalogs', [])])}",
            ""
        ])
        
        return "\n".join(context_lines)
    
    def _format_specific_schema_context(self, catalog_context: Dict[str, Any]) -> str:
        """Format specific catalog/schema context"""
        context_lines = [
            f"=== SPECIFIC SCHEMA CONTEXT ===",
            f"Catalog: {catalog_context['catalog']}",
            f"Schema: {catalog_context['schema']}\n",
            "Available Tables and Columns:"
        ]
        
        for table in catalog_context.get("tables", []):
            context_lines.append(f"\nTable: {table['name']}")
            context_lines.append(f"Full Name: {catalog_context['catalog']}.{catalog_context['schema']}.{table['name']}")
            
            if "columns" in table and table["columns"]:
                col_details = []
                for col in table["columns"]:
                    col_name = col.get('name', 'unknown')
                    col_type = col.get('type', 'unknown')
                    col_details.append(f"  - {col_name} ({col_type})")
                context_lines.extend(col_details)
            else:
                context_lines.append("  - (columns not available)")
        
        context_lines.extend([
            f"\n=== REQUIREMENTS ===",
            f"- Use fully qualified names: {catalog_context['catalog']}.{catalog_context['schema']}.table_name",
            "- Add LIMIT clauses for large result sets",
            "- Use exact column names as listed above"
        ])
        
        return "\n".join(context_lines)
    
    def _format_catalog_list_context(self, catalog_context: Dict[str, Any]) -> str:
        """Format basic catalog list context"""
        context_lines = [
            "=== AVAILABLE CATALOGS ===",
            "Choose appropriate catalog based on query intent:\n"
        ]
        
        for catalog in catalog_context.get("available_catalogs", []):
            description = catalog.get('description', 'No description')
            context_lines.append(f"  - {catalog['name']}: {description}")
        
        context_lines.extend([
            "\n=== REQUIREMENTS ===",
            "- Suggest appropriate catalog and schema in your response",
            "- Use format: catalog.schema.table_name",
            "- Set suggested_catalog and suggested_schema fields",
            "- Lower confidence (0.5-0.7) due to limited schema information"
        ])
        
        return "\n".join(context_lines)
    
    def _parse_structured_response(self, llm_response: Dict[str, Any], natural_query: str) -> NaturalLanguageQueryResponse:
        """Parse structured LLM response into the expected format"""
        try:
            # Handle error responses
            if "error" in llm_response:
                return NaturalLanguageQueryResponse(
                    sql_query="SELECT 'Error with LLM service' as error",
                    explanation=f"LLM service error: {llm_response['error']}",
                    confidence=0.0,
                    suggested_catalog=None,
                    suggested_schema=None
                )
            
            # Extract structured response
            sql_query = llm_response.get("sql_query", "SELECT 'No query generated' as error")
            confidence = float(llm_response.get("confidence", 0.5))
            suggested_catalog = llm_response.get("suggested_catalog")
            suggested_schema = llm_response.get("suggested_schema")
            tables_used = llm_response.get("tables_used", [])
            
            # Generate a simple explanation based on the SQL query
            explanation = self._generate_simple_explanation(sql_query, tables_used)
            
            return NaturalLanguageQueryResponse(
                sql_query=sql_query,
                explanation=explanation,
                confidence=confidence,
                suggested_catalog=suggested_catalog,
                suggested_schema=suggested_schema
            )
            
        except Exception as e:
            logger.error(f"Error parsing structured response: {str(e)}")
            return NaturalLanguageQueryResponse(
                sql_query="SELECT 'Error parsing response' as error",
                explanation=f"Failed to parse LLM response: {str(e)}",
                confidence=0.0,
                suggested_catalog=None,
                suggested_schema=None
            )
    
    def _generate_simple_explanation(self, sql_query: str, tables_used: List[str]) -> str:
        """Generate a simple explanation based on the SQL query structure"""
        try:
            query_upper = sql_query.upper()
            explanation_parts = []
            
            if "SELECT" in query_upper:
                explanation_parts.append("Retrieves data")
            
            if tables_used:
                if len(tables_used) == 1:
                    explanation_parts.append(f"from {tables_used[0]} table")
                else:
                    explanation_parts.append(f"from {', '.join(tables_used)} tables with joins")
            
            if "WHERE" in query_upper:
                explanation_parts.append("with filtering conditions")
            
            if "GROUP BY" in query_upper:
                explanation_parts.append("grouped by specified columns")
            
            if "ORDER BY" in query_upper:
                explanation_parts.append("sorted by specified criteria")
            
            if "LIMIT" in query_upper:
                explanation_parts.append("with result limit applied")
            
            if explanation_parts:
                return " ".join(explanation_parts) + "."
            else:
                return "Executes the requested SQL operation."
                
        except Exception:
            return "Generated SQL query based on natural language input."

    async def suggest_query_improvements(
        self, 
        sql_query: str, 
        context: Optional[Dict[str, Any]] = None,
        model_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Suggest improvements for an existing SQL query using unified LLM service"""
        try:
            messages = [
                {
                    "role": "system", 
                    "content": "You are a SQL optimization expert. Provide practical suggestions in JSON format."
                },
                {
                    "role": "user", 
                    "content": f"""Analyze the following SQL query and suggest improvements for performance, readability, and best practices:

SQL Query:
{sql_query}

Database Context:
{json.dumps(context, indent=2) if context else 'No context provided'}

Please provide suggestions in JSON format:
{{
    "performance_suggestions": ["suggestion1", "suggestion2"],
    "readability_improvements": ["improvement1", "improvement2"],
    "best_practices": ["practice1", "practice2"],
    "optimized_query": "improved SQL query",
    "explanation": "explanation of changes made"
}}"""
                }
            ]
            
            model_key = model_key or self.default_model_key
            response = await unified_llm_service.generate_json_completion(
                messages=messages,
                model_key=model_key,
                temperature=0.2,
                max_tokens=1000
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error suggesting query improvements: {str(e)}")
            return {
                "performance_suggestions": [],
                "readability_improvements": [],
                "best_practices": [],
                "optimized_query": sql_query,
                "explanation": f"Error generating suggestions: {str(e)}"
            }

# Global service instance
nl2sql_service = NL2SQLService() 