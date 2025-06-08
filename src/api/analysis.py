"""
SQL Analysis API Router
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import time

from src.models.analysis import (
    QueryRequest, QueryResult, SampleQueryRequest, SampleQueriesResponse,
    CatalogBrowserResponse, CatalogInfo, SchemaInfo, TableInfo, QueryType
)
from src.services.trino_service import trino_service
from src.services.activity_log_service import activity_log_service
from src.models.activity_log import ActivityType, ActivityLogRequest

# Import new unified LLM services
from src.services.unified_llm_service import unified_llm_service
from src.services.nl2sql_service import nl2sql_service
from src.services.visualization_service import visualization_service
from src.config.llm_config import llm_config, LLMProvider, LLMModelConfig
from src.services.query_execution_service import query_execution_service

router = APIRouter(prefix="/analysis", tags=["SQL Analysis"])

# Updated Pydantic models for visualization and NL2SQL
class VisualizationRequest(BaseModel):
    data: List[Dict[str, Any]]
    data_summary: Dict[str, Any] = {}
    user_intent: Optional[str] = None
    model_key: Optional[str] = None

class VisualizationRecommendation(BaseModel):
    chart_type: str
    chart_config: Dict[str, Any]
    reasoning: str
    confidence: float
    alternative_charts: List[str] = []

class NaturalLanguageQueryRequest(BaseModel):
    query: str
    catalog: Optional[str] = None
    schema: Optional[str] = None
    conversation_history: Optional[List[Dict[str, str]]] = []
    model_key: Optional[str] = None

class NaturalLanguageQueryResponse(BaseModel):
    sql_query: str
    explanation: str
    confidence: float
    suggested_catalog: Optional[str] = None
    suggested_schema: Optional[str] = None

# New models for LLM management
class LLMModelInfo(BaseModel):
    key: str
    display_name: str
    provider: str
    model_name: str
    supports_streaming: bool
    supports_json_mode: bool
    max_tokens: Optional[int]

class LLMModelsResponse(BaseModel):
    available_models: List[LLMModelInfo]
    default_model: str
    current_model: str

class SetDefaultModelRequest(BaseModel):
    model_key: str

# Add new models for SQL execution
class SQLExecutionRequest(BaseModel):
    sql_query: str
    catalog: Optional[str] = None
    schema: Optional[str] = None

class SQLExecutionResponse(BaseModel):
    query_result: QueryResult
    visualization_recommendation: Optional[Dict[str, Any]] = None
    execution_time_ms: float
    success: bool
    error: Optional[str] = None

# Add new models for visualization
class VisualizationRecommendationResponse(BaseModel):
    chart_type: str
    title: str
    description: str
    rationale: str
    config: Dict[str, Any]

@router.get("/health")
async def check_analysis_health():
    """Check analysis service health"""
    trino_healthy = await trino_service.health_check()
    
    return {
        "status": "healthy" if trino_healthy else "unhealthy",
        "trino": trino_healthy,
        "timestamp": "2025-01-25T10:25:00Z"
    }


@router.get("/catalog", response_model=CatalogBrowserResponse)
async def get_catalog_browser():
    """Get catalog browser data for sidebar"""
    try:
        # Log activity
        activity_log_service.log_page_view("analysis-catalog", "anonymous")
        
        response = await trino_service.get_catalog_browser_data()
        return response
        
    except Exception as e:
        activity_log_service.log_error(
            ActivityType.DATA_ACCESS,
            f"Error getting catalog browser data: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"Failed to get catalog data: {str(e)}")


@router.get("/catalogs", response_model=List[CatalogInfo])
async def get_catalogs():
    """Get available catalogs"""
    try:
        catalogs = await trino_service.get_catalogs()
        
        # Log activity
        request = ActivityLogRequest(
            activity_type=ActivityType.DATA_ACCESS,
            resource_type="catalog",
            description=f"Retrieved {len(catalogs)} catalogs"
        )
        activity_log_service.log_activity(request, user_id="anonymous")
        
        return catalogs
        
    except Exception as e:
        activity_log_service.log_error(
            ActivityType.DATA_ACCESS,
            f"Error getting catalogs: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"Failed to get catalogs: {str(e)}")


@router.get("/catalogs/{catalog}/schemas", response_model=List[SchemaInfo])
async def get_schemas(catalog: str):
    """Get schemas in a catalog"""
    try:
        schemas = await trino_service.get_schemas(catalog)
        
        # Log activity
        request = ActivityLogRequest(
            activity_type=ActivityType.DATA_ACCESS,
            resource_type="schema",
            resource_id=catalog,
            description=f"Retrieved {len(schemas)} schemas from catalog {catalog}"
        )
        activity_log_service.log_activity(request, user_id="anonymous")
        
        return schemas
        
    except Exception as e:
        activity_log_service.log_error(
            ActivityType.DATA_ACCESS,
            f"Error getting schemas for catalog {catalog}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"Failed to get schemas: {str(e)}")


@router.get("/catalogs/{catalog}/schemas/{schema}/tables", response_model=List[TableInfo])
async def get_tables(catalog: str, schema: str):
    """Get tables in a schema"""
    try:
        tables = await trino_service.get_tables(catalog, schema)
        
        # Log activity
        request = ActivityLogRequest(
            activity_type=ActivityType.DATA_ACCESS,
            resource_type="table",
            resource_id=f"{catalog}.{schema}",
            description=f"Retrieved {len(tables)} tables from {catalog}.{schema}"
        )
        activity_log_service.log_activity(request, user_id="anonymous")
        
        return tables
        
    except Exception as e:
        activity_log_service.log_error(
            ActivityType.DATA_ACCESS,
            f"Error getting tables for {catalog}.{schema}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"Failed to get tables: {str(e)}")


@router.get("/catalogs/{catalog}/schemas/{schema}/tables/{table}", response_model=TableInfo)
async def get_table_info(catalog: str, schema: str, table: str):
    """Get detailed table information"""
    try:
        table_info = await trino_service.get_table_info(catalog, schema, table)
        
        if not table_info:
            raise HTTPException(status_code=404, detail="Table not found")
        
        # Log activity
        request = ActivityLogRequest(
            activity_type=ActivityType.DATA_ACCESS,
            resource_type="table",
            resource_id=f"{catalog}.{schema}.{table}",
            description=f"Retrieved table info for {catalog}.{schema}.{table}"
        )
        activity_log_service.log_activity(request, user_id="anonymous")
        
        return table_info
        
    except HTTPException:
        raise
    except Exception as e:
        activity_log_service.log_error(
            ActivityType.DATA_ACCESS,
            f"Error getting table info for {catalog}.{schema}.{table}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"Failed to get table info: {str(e)}")


@router.post("/sample-queries", response_model=SampleQueriesResponse)
async def generate_sample_queries(request: SampleQueryRequest):
    """Generate sample SQL queries for a table"""
    try:
        response = await trino_service.generate_sample_queries(request)
        
        # Log activity
        log_request = ActivityLogRequest(
            activity_type=ActivityType.AI_SUGGESTION_GENERATE,
            resource_type="sample_queries",
            resource_id=f"{request.catalog}.{request.schema}.{request.table}",
            description=f"Generated {len(response.queries)} sample queries for {request.catalog}.{request.schema}.{request.table}",
            details={
                "query_types": [qt.value for qt in request.query_types],
                "query_count": len(response.queries)
            }
        )
        activity_log_service.log_activity(log_request, user_id="anonymous")
        
        return response
        
    except Exception as e:
        activity_log_service.log_error(
            ActivityType.AI_SUGGESTION_GENERATE,
            f"Error generating sample queries: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"Failed to generate sample queries: {str(e)}")


@router.post("/query", response_model=QueryResult)
async def execute_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """Execute SQL query"""
    try:
        result = await trino_service.execute_query(request)
        
        # Log activity in background
        def log_query_activity():
            log_request = ActivityLogRequest(
                activity_type=ActivityType.DATA_ACCESS,
                resource_type="query",
                description=f"Executed SQL query: {request.query[:100]}...",
                details={
                    "query": request.query,
                    "catalog": request.catalog,
                    "schema": request.schema,
                    "row_count": result.row_count,
                    "execution_time_ms": result.execution_time_ms,
                    "query_id": result.query_id,
                    "success": result.error is None
                },
                execution_time_ms=int(result.execution_time_ms)
            )
            activity_log_service.log_activity(log_request, user_id="anonymous")
        
        background_tasks.add_task(log_query_activity)
        
        return result
        
    except Exception as e:
        activity_log_service.log_error(
            ActivityType.DATA_ACCESS,
            f"Error executing query: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"Failed to execute query: {str(e)}")


@router.get("/query-types")
async def get_query_types():
    """Get available query types for sample generation"""
    return [
        {
            "value": QueryType.SELECT.value,
            "label": "SELECT",
            "description": "Retrieve data from tables"
        },
        {
            "value": QueryType.INSERT.value,
            "label": "INSERT", 
            "description": "Insert new data into tables"
        },
        {
            "value": QueryType.UPDATE.value,
            "label": "UPDATE",
            "description": "Update existing data in tables"
        },
        {
            "value": QueryType.DELETE.value,
            "label": "DELETE",
            "description": "Delete data from tables"
        },
        {
            "value": QueryType.DESCRIBE.value,
            "label": "DESCRIBE",
            "description": "Describe table structure"
        },
        {
            "value": QueryType.SHOW.value,
            "label": "SHOW",
            "description": "Show database objects"
        }
    ]


@router.get("/cross-catalog-examples")
async def get_cross_catalog_examples():
    """Get examples of cross-catalog queries (heterogeneous database joins)"""
    examples = [
        {
            "title": "Oracle-MySQL Cross Join",
            "description": "Join Oracle HR data with MySQL ecommerce data",
            "query": """SELECT 
    e.first_name,
    e.last_name,
    e.email as employee_email,
    c.name as customer_name,
    c.email as customer_email
FROM oracle_catalog.hr.employees e
FULL OUTER JOIN mysql_catalog.ecommerce.customers c 
    ON LOWER(e.email) = LOWER(c.email)
WHERE e.salary > 50000
LIMIT 20;""",
            "catalogs": ["oracle_catalog", "mysql_catalog"],
            "purpose": "Find employees who are also customers"
        },
        {
            "title": "PostgreSQL-MySQL Analytics",
            "description": "Analyze data across PostgreSQL warehouse and MySQL ecommerce",
            "query": """WITH sales_summary AS (
    SELECT 
        product_id,
        SUM(amount) as total_sales,
        COUNT(*) as order_count
    FROM mysql_catalog.ecommerce.orders
    GROUP BY product_id
),
warehouse_data AS (
    SELECT *
    FROM postgresql_catalog.warehouse.inventory
)
SELECT 
    w.product_name,
    w.stock_level,
    COALESCE(s.total_sales, 0) as total_sales,
    COALESCE(s.order_count, 0) as order_count,
    CASE 
        WHEN s.total_sales > 10000 THEN 'High'
        WHEN s.total_sales > 5000 THEN 'Medium'
        ELSE 'Low'
    END as sales_tier
FROM warehouse_data w
LEFT JOIN sales_summary s ON w.product_id = s.product_id
ORDER BY s.total_sales DESC NULLS LAST;""",
            "catalogs": ["mysql_catalog", "postgresql_catalog"],
            "purpose": "Cross-platform inventory and sales analysis"
        },
        {
            "title": "Multi-Database Reporting",
            "description": "Generate unified report from multiple database systems",
            "query": """WITH oracle_employees AS (
    SELECT 
        employee_id,
        first_name || ' ' || last_name as full_name,
        department_id,
        salary,
        'Oracle' as source_system
    FROM oracle_catalog.hr.employees
),
mysql_customers AS (
    SELECT
        customer_id,
        name as full_name,
        'N/A' as department_id,
        0 as salary,
        'MySQL' as source_system
    FROM mysql_catalog.ecommerce.customers
),
combined_people AS (
    SELECT * FROM oracle_employees
    UNION ALL
    SELECT customer_id, full_name, department_id, salary, source_system
    FROM mysql_customers
)
SELECT 
    source_system,
    COUNT(*) as total_records,
    AVG(salary) as avg_salary,
    MIN(full_name) as first_name_alphabetically,
    MAX(full_name) as last_name_alphabetically
FROM combined_people
GROUP BY source_system
ORDER BY source_system;""",
            "catalogs": ["oracle_catalog", "mysql_catalog"],
            "purpose": "Unified reporting across multiple systems"
        }
    ]
    
    return {"examples": examples, "total": len(examples)}


@router.post("/visualize-recommend", response_model=VisualizationRecommendation)
async def recommend_visualization(request: VisualizationRequest):
    """Get LLM-powered visualization recommendations for query results"""
    try:
        recommendation = await visualization_service.recommend_visualization(
            data_sample=request.data,
            data_summary=request.data_summary,
            user_intent=request.user_intent,
            model_key=request.model_key
        )
        
        # Log activity
        log_request = ActivityLogRequest(
            activity_type=ActivityType.AI_SUGGESTION_GENERATE,
            resource_type="visualization",
            description=f"Generated {recommendation.chart_type} visualization recommendation",
            details={
                "chart_type": recommendation.chart_type,
                "confidence": recommendation.confidence,
                "model_key": request.model_key or "default"
            }
        )
        activity_log_service.log_activity(log_request, user_id="anonymous")
        
        return recommendation
        
    except Exception as e:
        activity_log_service.log_error(
            ActivityType.AI_SUGGESTION_GENERATE,
            f"Error generating visualization recommendation: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"Failed to generate visualization recommendation: {str(e)}")


@router.post("/natural-language-query", response_model=NaturalLanguageQueryResponse)
async def convert_natural_language_to_sql(request: NaturalLanguageQueryRequest):
    """Convert natural language query to SQL using LLM"""
    try:
        # Get catalog context if not specified
        catalog_context = None
        if request.catalog and request.schema:
            # Get specific catalog/schema context
            try:
                tables = await trino_service.get_tables(request.catalog, request.schema)
                table_details = []
                for table in tables[:10]:  # Limit to 10 tables to avoid large context
                    try:
                        table_info = await trino_service.get_table_info(request.catalog, request.schema, table.name)
                        table_details.append({
                            "name": table.name,
                            "columns": [{"name": col.name, "type": col.type} for col in table_info.columns[:20]]  # Limit columns
                        })
                    except:
                        table_details.append({"name": table.name, "columns": []})
                
                catalog_context = {
                    "catalog": request.catalog,
                    "schema": request.schema,
                    "tables": table_details
                }
            except:
                pass
        else:
            # Get available catalogs context
            try:
                catalogs = await trino_service.get_catalogs()
                catalog_context = {
                    "available_catalogs": [{"name": cat.name, "description": cat.comment} for cat in catalogs]
                }
            except:
                pass
        
        # Convert natural language to SQL
        response = await nl2sql_service.convert_natural_language_to_sql(
            natural_query=request.query,
            catalog_context=catalog_context,
            conversation_history=request.conversation_history,
            model_key=request.model_key
        )
        
        # Log activity
        log_request = ActivityLogRequest(
            activity_type=ActivityType.AI_SUGGESTION_GENERATE,
            resource_type="natural_language_query",
            description=f"Converted natural language to SQL with confidence {response.confidence}",
            details={
                "query": request.query,
                "sql_query": response.sql_query,
                "confidence": response.confidence,
                "model_key": request.model_key or "default"
            }
        )
        activity_log_service.log_activity(log_request, user_id="anonymous")
        
        return response
        
    except Exception as e:
        activity_log_service.log_error(
            ActivityType.AI_SUGGESTION_GENERATE,
            f"Error converting natural language to SQL: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"Failed to convert natural language to SQL: {str(e)}")


@router.post("/chat-query")
async def execute_chat_query(request: NaturalLanguageQueryRequest, background_tasks: BackgroundTasks):
    """Execute a natural language query end-to-end (convert to SQL and execute) with full schema context"""
    try:
        # Step 1: Get comprehensive schema context
        catalog_context = None
        
        try:
            if request.catalog and request.schema:
                # Get specific catalog/schema context (existing logic)
                tables = await trino_service.get_tables(request.catalog, request.schema)
                table_details = []
                for table in tables[:10]:
                    try:
                        table_info = await trino_service.get_table_info(request.catalog, request.schema, table.name)
                        table_details.append({
                            "name": table.name,
                            "columns": [{"name": col.name, "type": col.type} for col in table_info.columns[:20]]
                        })
                    except:
                        table_details.append({"name": table.name, "columns": []})
                
                catalog_context = {
                    "catalog": request.catalog,
                    "schema": request.schema,
                    "tables": table_details
                }
            else:
                # Get full schema context with all available catalogs/schemas/tables
                schema_context = await trino_service.get_full_schema_context(
                    max_catalogs=4,  # Limit to prevent context overflow
                    max_schemas_per_catalog=3,
                    max_tables_per_schema=8
                )
                
                if schema_context and schema_context.get("catalogs"):
                    catalog_context = schema_context
                else:
                    # Fallback to basic catalog listing if full context fails
                    catalogs = await trino_service.get_catalogs()
                    catalog_context = {
                        "available_catalogs": [{"name": cat.name, "description": cat.comment} for cat in catalogs]
                    }
                    
        except Exception as catalog_error:
            # If schema context retrieval fails, continue with minimal context
            try:
                catalogs = await trino_service.get_catalogs()
                catalog_context = {
                    "available_catalogs": [{"name": cat.name, "description": cat.comment} for cat in catalogs]
                }
            except:
                catalog_context = None
        
        # Step 2: Convert natural language to SQL with enhanced context
        nl_response = await nl2sql_service.convert_natural_language_to_sql(
            natural_query=request.query,
            catalog_context=catalog_context,
            conversation_history=request.conversation_history,
            model_key=request.model_key
        )
        
        # Step 3: Try to execute the SQL query
        query_result = None
        query_error = None
        try:
            query_request = QueryRequest(
                query=nl_response.sql_query
            )
            query_result = await trino_service.execute_query(query_request)
        except Exception as qe:
            query_error = str(qe)
            query_result = None
        
        # Step 4: Generate visualization recommendation if there's data
        visualization_recommendation = None
        if query_result and query_result.data and len(query_result.data) > 0:
            try:
                visualization_recommendation = await visualization_service.recommend_visualization(
                    data_sample=query_result.data,
                    data_summary={"row_count": len(query_result.data)},
                    user_intent=request.query,
                    model_key=request.model_key
                )
            except Exception as viz_error:
                # If visualization fails, continue without it
                visualization_recommendation = None
        
        def log_chat_activity():
            """Log chat query activity in background"""
            try:
                log_request = ActivityLogRequest(
                    activity_type=ActivityType.CHAT_QUERY,
                    resource_type="natural_language_query",
                    description=f"Executed chat query: {request.query}",
                    details={
                        "natural_query": request.query,
                        "generated_sql": nl_response.sql_query,
                        "execution_time": query_result.execution_time_ms if query_result else None,
                        "rows_returned": len(query_result.data) if query_result and query_result.data else 0,
                        "sql_confidence": nl_response.confidence,
                        "has_visualization": visualization_recommendation is not None,
                        "model_key": request.model_key or "default",
                        "query_executed": query_result is not None,
                        "schema_context_used": catalog_context is not None,
                        "schema_context_type": "full" if catalog_context and "catalogs" in catalog_context else "basic" if catalog_context else "none",
                        "query_error": query_error
                    }
                )
                activity_log_service.log_activity(log_request, user_id="anonymous")
            except Exception as e:
                activity_log_service.log_error(
                    ActivityType.CHAT_QUERY,
                    f"Error logging chat activity: {str(e)}"
                )
        
        background_tasks.add_task(log_chat_activity)
        
        # Prepare response notes
        notes = []
        if not query_result:
            if query_error:
                notes.append(f"Query execution failed: {query_error}")
            else:
                notes.append("Query was converted but not executed due to database connection issues")
        
        if catalog_context:
            if "catalogs" in catalog_context:
                notes.append(f"Used full schema context with {len(catalog_context['catalogs'])} catalogs")
            elif "catalog" in catalog_context:
                notes.append(f"Used specific schema context for {catalog_context['catalog']}.{catalog_context['schema']}")
            else:
                notes.append("Used basic catalog listing")
        else:
            notes.append("No schema context available - generated query may need manual adjustment")
        
        return {
            "natural_language_query": request.query,
            "nl_response": nl_response,
            "query_result": query_result,
            "visualization_recommendation": visualization_recommendation,
            "status": "success",
            "notes": notes,
            "schema_context_summary": {
                "type": "full" if catalog_context and "catalogs" in catalog_context else "basic" if catalog_context else "none",
                "catalogs_available": len(catalog_context.get("catalogs", [])) if catalog_context and "catalogs" in catalog_context else 0,
                "tables_available": catalog_context.get("total_tables", 0) if catalog_context else 0
            }
        }
        
    except Exception as e:
        activity_log_service.log_error(
            ActivityType.CHAT_QUERY,
            f"Error executing chat query: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"Failed to execute chat query: {str(e)}")


@router.get("/llm-models", response_model=LLMModelsResponse)
async def get_llm_models():
    """Get available LLM models and current configuration"""
    try:
        print("DEBUG: Getting LLM models...")
        
        # Force complete refresh of Ollama models
        if llm_config.is_ollama_available():
            print("DEBUG: Ollama is available, forcing complete refresh...")
            try:
                # Get fresh models from Ollama API directly
                import requests
                response = requests.get(f"{llm_config.ollama_base_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    fresh_models = [model["name"] for model in data.get("models", [])]
                    print(f"DEBUG: Fresh models from Ollama: {fresh_models}")
                    
                    # Clear ALL existing Ollama models from config
                    llm_config.available_models = {
                        k: v for k, v in llm_config.available_models.items() 
                        if v.provider != LLMProvider.OLLAMA
                    }
                    print(f"DEBUG: Cleared Ollama models, remaining: {len(llm_config.available_models)}")
                    
                    # Add fresh Ollama models
                    for model_name in fresh_models:
                        clean_name = model_name.split(":")[0]
                        key = f"ollama-{clean_name}"
                        
                        llm_config.available_models[key] = LLMModelConfig(
                            provider=LLMProvider.OLLAMA,
                            model_name=model_name,
                            display_name=f"{clean_name.title()} (Ollama)",
                            api_base_env_var="OLLAMA_BASE_URL",
                            max_tokens=4096
                        )
                    
                    print(f"DEBUG: Added {len(fresh_models)} fresh Ollama models")
                    
                # Force refresh the unified service to pick up new models
                unified_llm_service._setup_provider_credentials()
                print("DEBUG: Ollama models updated successfully")
            except Exception as e:
                # Log but don't fail if Ollama update fails
                print(f"DEBUG Warning: Could not update Ollama models: {e}")
        else:
            print("DEBUG: Ollama is not available")
        
        available_models = llm_config.get_available_models()  # Get directly from config
        print(f"DEBUG: Total models available: {len(available_models)}")
        
        ollama_models = [key for key, model in available_models.items() if model.provider.value == "ollama"]
        print(f"DEBUG: Ollama models: {ollama_models}")
        
        model_list = []
        for key, config in available_models.items():
            model_list.append(LLMModelInfo(
                key=key,
                display_name=config.display_name,
                provider=config.provider.value,
                model_name=config.model_name,
                supports_streaming=config.supports_streaming,
                supports_json_mode=config.supports_json_mode,
                max_tokens=config.max_tokens
            ))
        
        return LLMModelsResponse(
            available_models=model_list,
            default_model=llm_config.default_model,
            current_model=unified_llm_service.default_model_key
        )
        
    except Exception as e:
        print(f"DEBUG Error in get_llm_models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get LLM models: {str(e)}")


@router.post("/refresh-ollama-models")
async def refresh_ollama_models():
    """Refresh available Ollama models from local server"""
    try:
        if not llm_config.is_ollama_available():
            raise HTTPException(status_code=503, detail="Ollama server is not available")
        
        # Fetch and update models
        await llm_config.update_ollama_models()
        
        # Get updated models
        ollama_models = llm_config.get_models_by_provider(LLMProvider.OLLAMA)
        
        return {
            "status": "success",
            "message": f"Refreshed {len(ollama_models)} Ollama models",
            "models": list(ollama_models.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh Ollama models: {str(e)}")


@router.get("/ollama-status")
async def get_ollama_status():
    """Get Ollama server status and available models"""
    try:
        is_available = llm_config.is_ollama_available()
        
        if not is_available:
            return {
                "available": False,
                "base_url": llm_config.ollama_base_url,
                "models": []
            }
        
        # Fetch latest models
        available_models = await llm_config.fetch_ollama_models()
        
        return {
            "available": True,
            "base_url": llm_config.ollama_base_url,
            "models": available_models,
            "model_count": len(available_models)
        }
        
    except Exception as e:
        return {
            "available": False,
            "base_url": llm_config.ollama_base_url,
            "models": [],
            "error": str(e)
        }


@router.post("/set-default-model")
async def set_default_model(request: SetDefaultModelRequest):
    """Set the default LLM model"""
    try:
        unified_llm_service.set_default_model(request.model_key)
        
        # Log activity
        log_request = ActivityLogRequest(
            activity_type=ActivityType.SYSTEM_CONFIG,
            resource_type="llm_model",
            description=f"Changed default LLM model to {request.model_key}",
            details={"model_key": request.model_key}
        )
        activity_log_service.log_activity(log_request, user_id="anonymous")
        
        return {"status": "success", "message": f"Default model set to {request.model_key}"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set default model: {str(e)}")


@router.get("/llm-providers")
async def get_llm_providers():
    """Get available LLM providers and their status"""
    try:
        providers_status = {}
        for provider in LLMProvider:
            models = llm_config.get_models_by_provider(provider)
            
            # Special handling for Ollama
            if provider == LLMProvider.OLLAMA:
                is_available = llm_config.is_ollama_available()
                if is_available:
                    try:
                        # Try to refresh Ollama models
                        await llm_config.update_ollama_models()
                        models = llm_config.get_models_by_provider(provider)
                    except Exception as e:
                        print(f"Failed to refresh Ollama models: {e}")
                
                providers_status[provider.value] = {
                    "available": is_available,
                    "model_count": len(models),
                    "models": list(models.keys()),
                    "base_url": llm_config.ollama_base_url,
                    "can_refresh": is_available
                }
            else:
                providers_status[provider.value] = {
                    "available": len(models) > 0,
                    "model_count": len(models),
                    "models": list(models.keys())
                }
        
        return {"providers": providers_status}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get provider status: {str(e)}")


@router.post("/test-nl2sql")
async def test_nl2sql_endpoint(request: NaturalLanguageQueryRequest):
    """Test endpoint for NL2SQL service"""
    try:
        # Simple test without Trino dependencies
        nl_response = await nl2sql_service.convert_natural_language_to_sql(
            natural_query=request.query,
            catalog_context=None,
            conversation_history=request.conversation_history,
            model_key=request.model_key
        )
        
        return {
            "status": "success",
            "query": request.query,
            "sql_query": nl_response.sql_query,
            "confidence": nl_response.confidence,
            "explanation": nl_response.explanation
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "query": request.query
        }

@router.post("/execute-sql", response_model=SQLExecutionResponse)
async def execute_sql_query(request: SQLExecutionRequest, background_tasks: BackgroundTasks):
    """Execute SQL query and return results with visualization recommendation"""
    try:
        # Log activity
        def log_sql_activity():
            activity_log_service.log_activity(
                ActivityLogRequest(
                    activity_type=ActivityType.DATA_ACCESS,
                    resource_type="sql_query", 
                    description=f"SQL query executed: {request.sql_query[:100]}..."
                ),
                user_id="anonymous"
            )
        
        background_tasks.add_task(log_sql_activity)
        
        # Execute SQL query
        start_time = time.time()
        query_result = await query_execution_service.execute_sql_query(
            sql_query=request.sql_query,
            catalog=request.catalog,
            schema=request.schema
        )
        
        # Generate visualization recommendation if we have data
        visualization_recommendation = None
        if query_result.data and len(query_result.data) > 0:
            viz_rec = visualization_service.analyze_data_and_recommend(query_result)
            visualization_recommendation = {
                "chart_type": viz_rec.chart_type,
                "title": viz_rec.title,
                "description": viz_rec.description,
                "rationale": viz_rec.rationale,
                "config": viz_rec.config
            }
        
        execution_time = (time.time() - start_time) * 1000
        
        return SQLExecutionResponse(
            query_result=query_result,
            visualization_recommendation=visualization_recommendation,
            execution_time_ms=execution_time,
            success=not bool(query_result.error),
            error=query_result.error
        )
        
    except Exception as e:
        logger.error(f"Error executing SQL query: {str(e)}")
        # Log error activity
        activity_log_service.log_error(
            ActivityType.DATA_ACCESS,
            f"SQL execution error: {str(e)}"
        )
        
        return SQLExecutionResponse(
            query_result=QueryResult(
                query=request.sql_query,
                columns=[],
                data=[],
                row_count=0,
                execution_time_ms=0,
                error=str(e)
            ),
            visualization_recommendation=None,
            execution_time_ms=0,
            success=False,
            error=str(e)
        )

@router.post("/visualize-data", response_model=VisualizationRecommendationResponse)
async def recommend_visualization_for_data(request: QueryResult, model_key: Optional[str] = None):
    """Generate visualization recommendation for query result data"""
    try:
        # Generate visualization recommendation
        recommendation = visualization_service.analyze_data_and_recommend(request)
        
        # Log activity
        activity_log_service.log_activity(
            ActivityLogRequest(
                activity_type=ActivityType.DATA_ACCESS,
                resource_type="visualization",
                description=f"Generated {recommendation.chart_type} visualization for {request.row_count} rows"
            ),
            user_id="anonymous"
        )
        
        return VisualizationRecommendationResponse(
            chart_type=recommendation.chart_type,
            title=recommendation.title,
            description=recommendation.description,
            rationale=recommendation.rationale,
            config=recommendation.config
        )
        
    except Exception as e:
        logger.error(f"Error generating visualization recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate visualization: {str(e)}")

@router.post("/ai-visualize-recommend")
async def generate_ai_visualization_recommendation(request: QueryResult, model_key: Optional[str] = None):
    """Generate AI-powered visualization recommendation using LLM"""
    try:
        # Generate AI recommendation
        ai_recommendation = await visualization_service.generate_ai_recommendation(
            query_result=request,
            model_key=model_key
        )
        
        # Also generate rule-based recommendation as fallback
        rule_based_rec = visualization_service.analyze_data_and_recommend(request)
        
        # Combine recommendations
        response = {
            "ai_recommendation": ai_recommendation,
            "rule_based_recommendation": {
                "chart_type": rule_based_rec.chart_type,
                "title": rule_based_rec.title,
                "description": rule_based_rec.description,
                "rationale": rule_based_rec.rationale,
                "config": rule_based_rec.config
            },
            "recommended_config": rule_based_rec.config  # Use rule-based as primary
        }
        
        # Log activity
        activity_log_service.log_activity(
            ActivityLogRequest(
                activity_type=ActivityType.DATA_ACCESS,
                resource_type="ai_visualization",
                description=f"Generated AI visualization recommendation: {ai_recommendation.get('chart_type', 'unknown')}"
            ),
            user_id="anonymous"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating AI visualization recommendation: {str(e)}")
        # Return rule-based fallback
        rule_based_rec = visualization_service.analyze_data_and_recommend(request)
        return {
            "ai_recommendation": {
                "chart_type": rule_based_rec.chart_type,
                "rationale": f"AI service unavailable, using rule-based recommendation: {str(e)}",
                "x_column": request.columns[0] if request.columns else "x",
                "y_column": request.columns[-1] if request.columns else "y",
                "title": rule_based_rec.title,
                "insights": []
            },
            "rule_based_recommendation": {
                "chart_type": rule_based_rec.chart_type,
                "title": rule_based_rec.title,
                "description": rule_based_rec.description,
                "rationale": rule_based_rec.rationale,
                "config": rule_based_rec.config
            },
            "recommended_config": rule_based_rec.config
        } 

@router.get("/schema-context-test")
async def test_schema_context():
    """Test endpoint to verify schema context functionality"""
    try:
        # Get full schema context
        schema_context = await trino_service.get_full_schema_context(
            max_catalogs=3,
            max_schemas_per_catalog=2,
            max_tables_per_schema=5
        )
        
        # Format for LLM
        formatted_context = trino_service.format_schema_context_for_llm(schema_context)
        
        return {
            "status": "success",
            "schema_context": schema_context,
            "formatted_for_llm": formatted_context,
            "summary": {
                "total_catalogs": schema_context.get("total_catalogs", 0),
                "total_schemas": schema_context.get("total_schemas", 0),
                "total_tables": schema_context.get("total_tables", 0),
                "generation_time_ms": schema_context.get("generation_time_ms", 0)
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "schema_context": None,
            "formatted_for_llm": None
        } 