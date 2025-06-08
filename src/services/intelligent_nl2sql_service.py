"""
Intelligent Natural Language to SQL Service
Uses LLM to analyze user queries and intelligently select relevant tables and generate SQL
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import re
import time

from src.services.unified_llm_service import unified_llm_service
from src.services.schema_context_service import schema_context_service, SchemaContext, TableInfo
from src.services.trino_service import trino_service
from src.models.analysis import QueryRequest, QueryResult
from src.config.logging_config import get_service_logger

logger = get_service_logger("intelligent_nl2sql_service")

class TableSelection(BaseModel):
    """Selected table with relevance score and reasoning"""
    table_name: str
    full_name: str
    relevance_score: float  # 0.0 to 1.0
    reasoning: str
    suggested_role: str  # 'primary', 'lookup', 'bridge', 'aggregation'

class QueryIntent(BaseModel):
    """Analyzed user query intent"""
    intent_type: str  # 'analysis', 'lookup', 'aggregation', 'comparison', 'trend'
    business_domain: str  # 'customer_management', 'sales', 'product_catalog'
    key_entities: List[str]  # ['customer', 'album', 'purchase']
    analysis_type: str  # 'count', 'sum', 'average', 'top_n', 'distribution'
    korean_keywords: List[str]  # Original Korean keywords found

class SQLGeneration(BaseModel):
    """Generated SQL with metadata"""
    sql_query: str
    explanation: str
    confidence: float
    selected_tables: List[TableSelection]
    query_intent: QueryIntent
    # New fields for error correction
    original_sql: Optional[str] = None
    fixed_sql: Optional[str] = None
    fix_attempts: int = 0
    fix_reason: Optional[str] = None
    execution_success: bool = False

class SQLErrorInfo(BaseModel):
    """Information about SQL error for debugging"""
    error_type: str
    error_message: str
    problem_column: Optional[str] = None
    problem_table: Optional[str] = None
    suggestion: str

class IntelligentNL2SQLService:
    """Advanced NL2SQL service using LLM for intelligent table selection and SQL generation"""
    
    def __init__(self):
        self.logger = logger
        self.max_fix_attempts = 3
    
    async def convert_natural_language_to_sql(
        self,
        natural_query: str,
        model_key: Optional[str] = "gpt-3.5-turbo",
        max_tables: int = 20
    ) -> SQLGeneration:
        """
        Convert natural language to SQL using intelligent LLM-based analysis with auto-validation and error correction
        """
        try:
            self.logger.info(f"Processing natural language query: {natural_query}")
            
            # Step 1: Get comprehensive schema context
            schema_context = await schema_context_service.get_comprehensive_schema_context(max_tables=max_tables)
            
            if not schema_context.tables:
                raise Exception("No tables available in schema context")
            
            # Step 2: Analyze query intent
            query_intent = await self._analyze_query_intent(natural_query, schema_context, model_key)
            
            # Step 3: Select relevant tables
            selected_tables = await self._select_relevant_tables(natural_query, query_intent, schema_context, model_key)
            
            # Step 4: Generate SQL
            sql_result = await self._generate_sql(natural_query, query_intent, selected_tables, schema_context, model_key)
            
            # Step 5: NEW - Validate and fix SQL if needed
            validated_sql_result = await self._validate_and_fix_sql(
                sql_result["sql_query"], 
                sql_result, 
                natural_query, 
                query_intent, 
                selected_tables, 
                schema_context, 
                model_key
            )
            
            result = SQLGeneration(
                sql_query=validated_sql_result["final_sql"],
                explanation=validated_sql_result["final_explanation"],
                confidence=validated_sql_result["confidence"],
                selected_tables=selected_tables,
                query_intent=query_intent,
                original_sql=sql_result["sql_query"],
                fixed_sql=validated_sql_result.get("fixed_sql"),
                fix_attempts=validated_sql_result.get("fix_attempts", 0),
                fix_reason=validated_sql_result.get("fix_reason"),
                execution_success=validated_sql_result.get("execution_success", False)
            )
            
            if result.fix_attempts > 0:
                self.logger.info(f"SQL auto-corrected after {result.fix_attempts} attempts: {result.fix_reason}")
            
            self.logger.success(f"Generated {'and fixed ' if result.fix_attempts > 0 else ''}SQL with confidence {result.confidence}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in intelligent NL2SQL conversion: {str(e)}")
            # Return fallback result
            return SQLGeneration(
                sql_query="SELECT 'Error in intelligent query processing' as message",
                explanation=f"Failed to process query: {str(e)}",
                confidence=0.1,
                selected_tables=[],
                query_intent=QueryIntent(
                    intent_type="error",
                    business_domain="unknown",
                    key_entities=[],
                    analysis_type="none",
                    korean_keywords=[]
                ),
                execution_success=False
            )

    async def _validate_and_fix_sql(
        self, 
        original_sql: str, 
        sql_result: Dict[str, Any],
        natural_query: str,
        query_intent: QueryIntent,
        selected_tables: List[TableSelection],
        schema_context: SchemaContext,
        model_key: str
    ) -> Dict[str, Any]:
        """
        Validate SQL by executing it and fix errors if they occur
        """
        current_sql = original_sql
        fix_attempts = 0
        fix_reason = None
        execution_success = False
        
        for attempt in range(self.max_fix_attempts):
            try:
                self.logger.info(f"Validating SQL (attempt {attempt + 1}): {current_sql[:100]}...")
                
                # Try to execute the SQL
                request = QueryRequest(
                    query=current_sql,
                    catalog="ontology_mysql",  # Use the main catalog
                    schema="ontology_dev",
                    limit=10  # Small limit for validation
                )
                
                result = await trino_service.execute_query(request)
                
                if not result.error:
                    # Success! SQL is valid
                    execution_success = True
                    self.logger.success(f"SQL validation successful on attempt {attempt + 1}")
                    break
                else:
                    # Error occurred, try to fix it
                    self.logger.warning(f"SQL validation failed: {result.error}")
                    
                    error_info = self._analyze_sql_error(result.error)
                    fixed_sql = await self._fix_sql_error(
                        current_sql, 
                        error_info,
                        natural_query,
                        query_intent,
                        selected_tables,
                        schema_context,
                        model_key
                    )
                    
                    if fixed_sql and fixed_sql != current_sql:
                        fix_attempts += 1
                        fix_reason = f"{error_info.error_type}: {error_info.suggestion}"
                        current_sql = fixed_sql
                        self.logger.info(f"Applied fix (attempt {fix_attempts}): {error_info.suggestion}")
                    else:
                        # Can't fix this error, break
                        self.logger.warning(f"Unable to fix SQL error: {result.error}")
                        break
                        
            except Exception as e:
                self.logger.error(f"Error during SQL validation: {str(e)}")
                break
        
        return {
            "final_sql": current_sql,
            "final_explanation": self._generate_final_explanation(
                sql_result["explanation"], 
                fix_attempts, 
                fix_reason, 
                execution_success
            ),
            "confidence": self._adjust_confidence(sql_result["confidence"], fix_attempts, execution_success),
            "fixed_sql": current_sql if fix_attempts > 0 else None,
            "fix_attempts": fix_attempts,
            "fix_reason": fix_reason,
            "execution_success": execution_success
        }

    def _analyze_sql_error(self, error_message: str) -> SQLErrorInfo:
        """
        Analyze SQL error message to identify the problem type and suggest fixes
        """
        error_upper = error_message.upper()
        
        # EXPRESSION_NOT_AGGREGATE error
        if "EXPRESSION_NOT_AGGREGATE" in error_upper or "MUST BE AN AGGREGATE EXPRESSION" in error_upper:
            # Extract the problematic column from the error message
            column_match = re.search(r"'([^']+)'\s+must be an aggregate expression", error_message, re.IGNORECASE)
            problem_column = column_match.group(1) if column_match else None
            
            return SQLErrorInfo(
                error_type="EXPRESSION_NOT_AGGREGATE",
                error_message=error_message,
                problem_column=problem_column,
                suggestion=f"Add '{problem_column}' to GROUP BY clause" if problem_column else "Fix GROUP BY clause"
            )
        
        # TABLE_NOT_FOUND error
        elif "TABLE_NOT_FOUND" in error_upper or "does not exist" in error_upper:
            table_match = re.search(r"Table\s+'([^']+)'\s+does not exist", error_message, re.IGNORECASE)
            problem_table = table_match.group(1) if table_match else None
            
            return SQLErrorInfo(
                error_type="TABLE_NOT_FOUND",
                error_message=error_message,
                problem_table=problem_table,
                suggestion=f"Replace with correct table name for '{problem_table}'" if problem_table else "Fix table reference"
            )
        
        # COLUMN_NOT_FOUND error
        elif "COLUMN_NOT_FOUND" in error_upper or "Column" in error_message and "cannot be resolved" in error_message:
            column_match = re.search(r"Column\s+'([^']+)'\s+cannot be resolved", error_message, re.IGNORECASE)
            problem_column = column_match.group(1) if column_match else None
            
            return SQLErrorInfo(
                error_type="COLUMN_NOT_FOUND", 
                error_message=error_message,
                problem_column=problem_column,
                suggestion=f"Replace with correct column name for '{problem_column}'" if problem_column else "Fix column reference"
            )
        
        # SYNTAX_ERROR
        elif "SYNTAX_ERROR" in error_upper or "syntax error" in error_message.lower():
            return SQLErrorInfo(
                error_type="SYNTAX_ERROR",
                error_message=error_message,
                suggestion="Fix SQL syntax"
            )
        
        # Generic error
        else:
            return SQLErrorInfo(
                error_type="UNKNOWN_ERROR",
                error_message=error_message,
                suggestion="Review and fix SQL query"
            )

    async def _fix_sql_error(
        self,
        sql: str,
        error_info: SQLErrorInfo,
        natural_query: str,
        query_intent: QueryIntent,
        selected_tables: List[TableSelection],
        schema_context: SchemaContext,
        model_key: str
    ) -> Optional[str]:
        """
        Fix SQL based on error type and error information - LLM-first approach
        """
        try:
            # Primary: Always try LLM-based fixing first for all error types
            self.logger.info(f"Attempting LLM-based fix for {error_info.error_type}")
            llm_fixed_sql = await self._fix_with_llm_enhanced(
                sql, 
                error_info, 
                natural_query, 
                query_intent,
                selected_tables,
                schema_context,
                model_key
            )
            
            if llm_fixed_sql and llm_fixed_sql != sql:
                self.logger.info(f"LLM successfully fixed {error_info.error_type}")
                return llm_fixed_sql
            
            # Fallback: Use specific fixing methods if LLM fails
            self.logger.warning(f"LLM fix failed for {error_info.error_type}, trying fallback methods")
            
            if error_info.error_type == "EXPRESSION_NOT_AGGREGATE":
                return self._fix_aggregate_error_fallback(sql, error_info)
            elif error_info.error_type == "TABLE_NOT_FOUND":
                return await self._fix_table_not_found_error(sql, error_info, selected_tables, schema_context)
            elif error_info.error_type == "COLUMN_NOT_FOUND":
                return await self._fix_column_not_found_error(sql, error_info, selected_tables, schema_context)
            else:
                # For unknown errors, LLM was already tried
                return None
                
        except Exception as e:
            self.logger.error(f"Error fixing SQL: {str(e)}")
            return None

    async def _fix_with_llm_enhanced(
        self, 
        sql: str, 
        error_info: SQLErrorInfo,
        natural_query: str,
        query_intent: QueryIntent,
        selected_tables: List[TableSelection],
        schema_context: SchemaContext,
        model_key: str
    ) -> Optional[str]:
        """
        Enhanced LLM-based SQL error fixing with comprehensive context
        """
        try:
            # Build comprehensive context for LLM
            table_info = ""
            if selected_tables:
                table_details = []
                for selection in selected_tables:
                    table_detail = next((t for t in schema_context.tables if t.full_name == selection.full_name), None)
                    if table_detail:
                        columns_str = ", ".join([f"{col['name']} ({col['type']})" for col in table_detail.columns[:10]])
                        table_details.append(f"""
Table: {selection.full_name}
Role: {selection.suggested_role}
Columns: {columns_str}""")
                table_info = "\n".join(table_details)
            
            # Create detailed prompt for LLM
            prompt = f"""You are an expert SQL engineer. Fix the following SQL query that has an error.

**Original User Request:** "{natural_query}"

**Query Intent:**
- Type: {query_intent.intent_type} 
- Domain: {query_intent.business_domain}
- Analysis: {query_intent.analysis_type}
- Entities: {', '.join(query_intent.key_entities)}

**SQL Query with Error:**
```sql
{sql}
```

**Error Details:**
- Error Type: {error_info.error_type}
- Error Message: {error_info.error_message}
- Problem Column: {error_info.problem_column or 'Not specified'}
- Problem Table: {error_info.problem_table or 'Not specified'}

**Available Tables and Columns:**
{table_info}

**Common SQL Patterns for Reference:**
- EXPRESSION_NOT_AGGREGATE: Add missing columns to GROUP BY clause
- TABLE_NOT_FOUND: Use correct catalog.schema.table format
- COLUMN_NOT_FOUND: Use exact column names from table schema
- SYNTAX_ERROR: Fix SQL syntax according to standard SQL rules

**Instructions:**
1. Analyze the error message carefully
2. Understand what the user wants to achieve
3. Fix the SQL while maintaining the original intent
4. Ensure all columns in SELECT are either aggregated or in GROUP BY
5. Use proper table references with catalog.schema.table format
6. Return ONLY the corrected SQL query without any explanation

**Corrected SQL:**"""

            messages = [{"role": "user", "content": prompt}]
            response = await unified_llm_service.generate_completion(
                messages=messages,
                model_key=model_key,
                temperature=0.1,
                max_tokens=800
            )
            
            fixed_sql = response.content.strip()
            
            # Clean up response (remove markdown formatting if present)
            if fixed_sql.startswith("```"):
                lines = fixed_sql.split('\n')
                # Find SQL content between ``` blocks
                sql_lines = []
                in_sql_block = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_sql_block = not in_sql_block
                        continue
                    if in_sql_block:
                        sql_lines.append(line)
                
                if sql_lines:
                    fixed_sql = '\n'.join(sql_lines).strip()
            
            # Remove any explanatory text that might be included
            if "corrected sql:" in fixed_sql.lower():
                fixed_sql = fixed_sql.split("corrected sql:")[-1].strip()
            
            if fixed_sql and fixed_sql != sql:
                self.logger.info(f"LLM fixed SQL for {error_info.error_type}: {len(fixed_sql)} chars")
                return fixed_sql
            else:
                self.logger.warning(f"LLM returned same or empty SQL for {error_info.error_type}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error in enhanced LLM SQL fixing: {str(e)}")
            return None

    def _fix_aggregate_error_fallback(self, sql: str, error_info: SQLErrorInfo) -> Optional[str]:
        """
        Fallback method for EXPRESSION_NOT_AGGREGATE error using regex (renamed from original method)
        """
        if not error_info.problem_column:
            return None
        
        try:
            # Simple approach: find "GROUP BY" and replace the entire GROUP BY clause
            sql_upper = sql.upper()
            group_by_pos = sql_upper.find('GROUP BY')
            
            if group_by_pos == -1:
                self.logger.warning("EXPRESSION_NOT_AGGREGATE error but no GROUP BY clause found")
                return None
            
            # Find the end of GROUP BY clause by looking for ORDER BY, HAVING, LIMIT or end of string
            group_by_start = group_by_pos + len('GROUP BY')
            rest_sql = sql[group_by_start:].strip()
            
            # Find where GROUP BY clause ends
            end_keywords = ['ORDER BY', 'HAVING', 'LIMIT']
            end_pos = len(rest_sql)  # Default to end of string
            
            for keyword in end_keywords:
                keyword_pos = rest_sql.upper().find(keyword)
                if keyword_pos != -1 and keyword_pos < end_pos:
                    end_pos = keyword_pos
            
            # Extract current GROUP BY clause
            current_group_by = rest_sql[:end_pos].strip()
            remaining_sql = rest_sql[end_pos:].strip()
            
            # Add the missing column to GROUP BY
            if current_group_by:
                new_group_by = f"{current_group_by}, {error_info.problem_column}"
            else:
                new_group_by = error_info.problem_column
            
            # Reconstruct the SQL
            before_group_by = sql[:group_by_pos]
            fixed_sql = f"{before_group_by}GROUP BY {new_group_by}"
            
            if remaining_sql:
                fixed_sql += f" {remaining_sql}"
            
            self.logger.info(f"Fallback fixed GROUP BY: '{current_group_by}' -> '{new_group_by}'")
            return fixed_sql
                
        except Exception as e:
            self.logger.error(f"Error in fallback aggregate fix: {str(e)}")
            return None

    async def _fix_with_llm(
        self, 
        sql: str, 
        error_info: SQLErrorInfo,
        natural_query: str,
        model_key: str
    ) -> Optional[str]:
        """
        Simple LLM-based SQL error fixing (kept for backward compatibility)
        """
        try:
            prompt = f"""Fix the following SQL query that has an error.

Original User Query: "{natural_query}"

SQL Query with Error:
```sql
{sql}
```

Error Information:
- Error Type: {error_info.error_type}
- Error Message: {error_info.error_message}
- Suggestion: {error_info.suggestion}

Please provide ONLY the corrected SQL query without any explanation or markdown formatting.
Focus on fixing the specific error while maintaining the original intent of the query.

Corrected SQL:"""

            messages = [{"role": "user", "content": prompt}]
            response = await unified_llm_service.generate_completion(
                messages=messages,
                model_key=model_key,
                temperature=0.1,
                max_tokens=500
            )
            
            fixed_sql = response.content.strip()
            
            # Remove markdown formatting if present
            if fixed_sql.startswith("```"):
                lines = fixed_sql.split('\n')
                fixed_sql = '\n'.join(lines[1:-1]) if len(lines) > 2 else fixed_sql
            
            self.logger.info(f"Simple LLM fixed SQL for {error_info.error_type}")
            return fixed_sql
            
        except Exception as e:
            self.logger.error(f"Error in simple LLM SQL fixing: {str(e)}")
            return None

    def _generate_final_explanation(
        self, 
        original_explanation: str, 
        fix_attempts: int, 
        fix_reason: Optional[str],
        execution_success: bool
    ) -> str:
        """
        Generate final explanation including fix information
        """
        explanation = original_explanation
        
        if fix_attempts > 0:
            status = "successfully" if execution_success else "attempted to"
            explanation += f"\n\n🔧 Auto-correction: {status} fixed {fix_attempts} SQL error(s)."
            if fix_reason:
                explanation += f"\n📝 Fix applied: {fix_reason}"
        
        if execution_success:
            explanation += "\n✅ SQL validation successful - query is ready to execute."
        else:
            explanation += "\n⚠️ SQL validation pending - please review the query."
        
        return explanation

    def _adjust_confidence(self, original_confidence: float, fix_attempts: int, execution_success: bool) -> float:
        """
        Adjust confidence based on fix attempts and execution success
        """
        confidence = original_confidence
        
        # Reduce confidence for each fix attempt
        confidence -= (fix_attempts * 0.1)
        
        # Boost confidence if execution was successful
        if execution_success:
            confidence += 0.1
        else:
            confidence -= 0.2
        
        # Keep confidence within bounds
        return max(0.1, min(1.0, confidence))

    async def _analyze_query_intent(self, query: str, schema_context: SchemaContext, model_key: str) -> QueryIntent:
        """Analyze user query to understand intent and extract key information"""
        
        prompt = f"""Analyze this natural language query to understand the user's intent and extract key information.

Query: "{query}"

Available Business Domains: {', '.join(schema_context.business_domains)}

Please analyze and respond with JSON in this exact format:
{{
    "intent_type": "analysis|lookup|aggregation|comparison|trend",
    "business_domain": "customer_management|sales|product_catalog|human_resources|analytics|general",
    "key_entities": ["entity1", "entity2"],
    "analysis_type": "count|sum|average|top_n|distribution|details|join",
    "korean_keywords": ["keyword1", "keyword2"]
}}

Analysis Guidelines:
- intent_type: What does the user want to do?
- business_domain: Which business area is this about?
- key_entities: What are the main subjects (customer, album, purchase, etc.)?
- analysis_type: What kind of analysis or operation?
- korean_keywords: Extract key Korean words that indicate intent

Examples:
"앨범을 구매한 고객정보를 분석해줘" → {{"intent_type": "analysis", "business_domain": "sales", "key_entities": ["customer", "album", "purchase"], "analysis_type": "join", "korean_keywords": ["앨범", "구매", "고객정보", "분석"]}}
"""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await unified_llm_service.generate_completion(
                messages=messages,
                model_key=model_key,
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse JSON response
            intent_data = json.loads(response.content)
            return QueryIntent(**intent_data)
            
        except Exception as e:
            self.logger.warning(f"Failed to analyze query intent: {e}")
            # Return basic intent analysis
            return QueryIntent(
                intent_type="analysis",
                business_domain="general",
                key_entities=["data"],
                analysis_type="details",
                korean_keywords=[]
            )
    
    async def _select_relevant_tables(
        self, 
        query: str, 
        intent: QueryIntent, 
        schema_context: SchemaContext, 
        model_key: str
    ) -> List[TableSelection]:
        """Select the most relevant tables for the query using LLM"""
        
        # Format schema for LLM
        schema_summary = schema_context_service.format_for_llm(schema_context, max_tokens=6000)
        
        prompt = f"""Given this user query and database schema, select the most relevant tables and explain their roles.

User Query: "{query}"
Query Intent: {intent.intent_type} in {intent.business_domain} domain
Key Entities: {', '.join(intent.key_entities)}

{schema_summary}

Please select relevant tables and respond with JSON array in this format:
[
    {{
        "table_name": "table_name",
        "full_name": "catalog.schema.table_name", 
        "relevance_score": 0.95,
        "reasoning": "This table contains customer information which is directly relevant to the query",
        "suggested_role": "primary|lookup|bridge|aggregation"
    }}
]

Role Definitions:
- primary: Main table containing the core data being queried
- lookup: Reference table providing additional details
- bridge: Junction table connecting primary tables
- aggregation: Table used for calculations/summaries

Guidelines:
1. Select 2-5 most relevant tables
2. Prioritize tables matching the business domain and key entities
3. Consider table relationships for JOIN operations
4. Assign relevance scores based on how directly each table relates to the query
5. Korean query "앨범을 구매한 고객정보" should select Customer, Album, Invoice tables
"""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await unified_llm_service.generate_completion(
                messages=messages,
                model_key=model_key,
                temperature=0.2,
                max_tokens=1000
            )
            
            # Parse JSON response
            selections_data = json.loads(response.content)
            return [TableSelection(**selection) for selection in selections_data]
            
        except Exception as e:
            self.logger.warning(f"Failed to select tables via LLM: {e}")
            # Fallback: select tables based on business domain
            return self._fallback_table_selection(intent, schema_context)
    
    def _fallback_table_selection(self, intent: QueryIntent, schema_context: SchemaContext) -> List[TableSelection]:
        """Fallback table selection based on business domain matching"""
        
        selections = []
        
        # Filter tables by business domain
        domain_tables = [t for t in schema_context.tables if t.business_context == intent.business_domain]
        
        if not domain_tables:
            # Use any available tables
            domain_tables = schema_context.tables[:5]
        
        for table in domain_tables[:3]:  # Limit to top 3 tables
            selections.append(TableSelection(
                table_name=table.name,
                full_name=table.full_name,
                relevance_score=0.7,
                reasoning=f"Selected based on business domain matching: {intent.business_domain}",
                suggested_role="primary" if not selections else "lookup"
            ))
        
        return selections
    
    async def _generate_sql(
        self,
        query: str,
        intent: QueryIntent,
        selected_tables: List[TableSelection],
        schema_context: SchemaContext,
        model_key: str
    ) -> Dict[str, Any]:
        """Generate SQL query based on selected tables and intent"""
        
        # Build detailed table information for selected tables
        table_details = []
        for selection in selected_tables:
            # Find full table info
            table_info = next((t for t in schema_context.tables if t.full_name == selection.full_name), None)
            if table_info:
                columns_str = ", ".join([f"{col['name']} ({col['type']})" for col in table_info.columns])
                table_details.append(f"""
Table: {selection.full_name} [{selection.suggested_role}]
Relevance: {selection.relevance_score}
Reasoning: {selection.reasoning}
Columns: {columns_str}
Relationships: {', '.join(table_info.potential_relationships)}
""")
        
        # Build relationships context
        relevant_relationships = [
            rel for rel in schema_context.relationships 
            if any(sel.full_name in [rel['from_table'], rel['to_table']] for sel in selected_tables)
        ]
        
        relationships_str = "\n".join([
            f"• {rel['from_table']} → {rel['to_table']} ({rel['type']})"
            for rel in relevant_relationships
        ])
        
        prompt = f"""Generate a SQL query based on the user's natural language request and selected tables.

User Query: "{query}"
Intent: {intent.intent_type} ({intent.analysis_type}) in {intent.business_domain}
Key Entities: {', '.join(intent.key_entities)}
Korean Keywords: {', '.join(intent.korean_keywords)}

Selected Tables:
{''.join(table_details)}

Table Relationships:
{relationships_str}

⚠️  CATALOG & SCHEMA REQUIREMENTS ⚠️
Available Catalogs and Valid Table References:
1. memory.default.* (temporary tables)
   - memory.default.sample_customers
   - memory.default.albums  
   - memory.default.purchases

2. ontology_mysql.ontology_dev.* (persistent MySQL tables)
   - ontology_mysql.ontology_dev.album
   - ontology_mysql.ontology_dev.artist
   - ontology_mysql.ontology_dev.customer
   - ontology_mysql.ontology_dev.track
   - ontology_mysql.ontology_dev.invoice
   - ontology_mysql.ontology_dev.invoiceline

3. sample_data.* (sample connector)

SCHEMA FORMAT RULES:
- Always use full catalog.schema.table format
- CORRECT: ontology_mysql.ontology_dev.album
- CORRECT: memory.default.sample_customers
- WRONG: memory.memory.table_name ❌
- WRONG: memory.table_name ❌

SQL Generation Guidelines:
1. Use the most appropriate catalog based on the query context
2. For persistent business data analysis, prefer ontology_mysql.ontology_dev.*
3. For demo/sample queries, use memory.default.*
4. Use proper JOIN conditions based on relationships
5. Include appropriate WHERE, GROUP BY, ORDER BY clauses
6. Add LIMIT for large result sets
7. Use meaningful column aliases

Example SQL Templates:
- MySQL Album query: "SELECT a.title FROM ontology_mysql.ontology_dev.album a"
- Memory customer query: "SELECT c.customer_name FROM memory.default.sample_customers c"
- Cross-catalog JOIN: "FROM ontology_mysql.ontology_dev.album a JOIN memory.default.purchases p ON ..."

Respond with JSON in this format:
{{
    "sql_query": "SELECT a.title, ar.name FROM ontology_mysql.ontology_dev.album a JOIN ontology_mysql.ontology_dev.artist ar ON a.artistid = ar.artistid LIMIT 10",
    "explanation": "This query retrieves album titles with artist names from the persistent MySQL database...",
    "confidence": 0.9
}}
"""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await unified_llm_service.generate_completion(
                messages=messages,
                model_key=model_key,
                temperature=0.1,
                max_tokens=1500
            )
            
            # Parse JSON response
            return json.loads(response.content)
            
        except Exception as e:
            self.logger.warning(f"Failed to generate SQL via LLM: {e}")
            # Fallback SQL generation
            return self._fallback_sql_generation(query, selected_tables)
    
    def _fallback_sql_generation(self, query: str, selected_tables: List[TableSelection]) -> Dict[str, Any]:
        """Generate fallback SQL when LLM fails"""
        
        if not selected_tables:
            # No tables selected, create a demo query based on query intent
            query_lower = query.lower()
            
            if any(keyword in query_lower for keyword in ["고객", "customer", "사용자"]):
                return {
                    "sql_query": "SELECT * FROM memory.default.sample_customers LIMIT 10",
                    "explanation": "고객 정보를 조회하는 샘플 쿼리입니다. memory.default 스키마를 사용합니다.",
                    "confidence": 0.6
                }
            elif any(keyword in query_lower for keyword in ["앨범", "album", "음악"]):
                return {
                    "sql_query": "SELECT * FROM memory.default.albums LIMIT 10", 
                    "explanation": "앨범 정보를 조회하는 샘플 쿼리입니다. memory.default 스키마를 사용합니다.",
                    "confidence": 0.6
                }
            elif any(keyword in query_lower for keyword in ["구매", "purchase", "거래"]):
                return {
                    "sql_query": "SELECT * FROM memory.default.purchases LIMIT 10",
                    "explanation": "구매 정보를 조회하는 샘플 쿼리입니다. memory.default 스키마를 사용합니다.",
                    "confidence": 0.6
                }
            else:
                return {
                    "sql_query": "SELECT 'Available tables: memory.default.sample_customers, memory.default.albums, memory.default.purchases' as info",
                    "explanation": "사용 가능한 테이블 목록을 표시합니다. 모든 테이블은 memory.default 스키마에 있습니다.",
                    "confidence": 0.3
                }
        
        # Generate SQL based on selected tables with proper schema
        primary_table = selected_tables[0]
        
        # Ensure we always use memory.default format
        if primary_table.full_name.startswith("memory.default."):
            table_ref = primary_table.full_name
        else:
            # Force correct schema format
            table_name = primary_table.table_name
            if "customer" in table_name.lower():
                table_ref = "memory.default.sample_customers"
            elif "album" in table_name.lower():
                table_ref = "memory.default.albums"
            elif "purchase" in table_name.lower():
                table_ref = "memory.default.purchases"
            else:
                table_ref = "memory.default.sample_customers"  # Safe default
        
        return {
            "sql_query": f"SELECT * FROM {table_ref} LIMIT 20",
            "explanation": f"기본 쿼리: {table_ref} 테이블에서 데이터를 조회합니다. (memory.default 스키마 사용)",
            "confidence": 0.5
        }

    async def _fix_table_not_found_error(
        self, 
        sql: str, 
        error_info: SQLErrorInfo,
        selected_tables: List[TableSelection],
        schema_context: SchemaContext
    ) -> Optional[str]:
        """
        Fallback method for TABLE_NOT_FOUND error by replacing with correct table name
        """
        if not error_info.problem_table:
            return None
        
        try:
            # Find the best matching table from available tables
            available_tables = [t.full_name for t in schema_context.tables]
            
            # Simple matching logic - can be improved
            problem_table_lower = error_info.problem_table.lower()
            best_match = None
            
            for table in available_tables:
                if problem_table_lower in table.lower() or table.split('.')[-1].lower() in problem_table_lower:
                    best_match = table
                    break
            
            if best_match:
                fixed_sql = sql.replace(error_info.problem_table, best_match)
                self.logger.info(f"Fallback fixed table reference: '{error_info.problem_table}' -> '{best_match}'")
                return fixed_sql
            else:
                self.logger.warning(f"No suitable replacement found for table '{error_info.problem_table}'")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in fallback table fix: {str(e)}")
            return None

    async def _fix_column_not_found_error(
        self, 
        sql: str, 
        error_info: SQLErrorInfo,
        selected_tables: List[TableSelection],
        schema_context: SchemaContext
    ) -> Optional[str]:
        """
        Fallback method for COLUMN_NOT_FOUND error by replacing with correct column name
        """
        if not error_info.problem_column:
            return None
        
        try:
            # Collect all available columns from selected tables
            available_columns = []
            for table_selection in selected_tables:
                table_info = next((t for t in schema_context.tables if t.full_name == table_selection.full_name), None)
                if table_info:
                    available_columns.extend([col['name'] for col in table_info.columns])
            
            # Find best matching column
            problem_column_lower = error_info.problem_column.split('.')[-1].lower()  # Handle table.column references
            best_match = None
            
            for column in available_columns:
                if problem_column_lower in column.lower() or column.lower() in problem_column_lower:
                    best_match = column
                    break
            
            if best_match:
                fixed_sql = sql.replace(error_info.problem_column, best_match)
                self.logger.info(f"Fallback fixed column reference: '{error_info.problem_column}' -> '{best_match}'")
                return fixed_sql
            else:
                self.logger.warning(f"No suitable replacement found for column '{error_info.problem_column}'")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in fallback column fix: {str(e)}")
            return None

# Global instance
intelligent_nl2sql_service = IntelligentNL2SQLService() 