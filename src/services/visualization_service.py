"""
Visualization Service
Analyzes query results and generates visualization recommendations
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from src.models.analysis import QueryResult
from src.services.unified_llm_service import unified_llm_service
from src.config.logging_config import get_service_logger

logger = get_service_logger("visualization")

class VisualizationRecommendation:
    """Visualization recommendation with Plotly configuration"""
    
    def __init__(self, chart_type: str, title: str, description: str, rationale: str, config: Dict[str, Any]):
        self.chart_type = chart_type
        self.title = title
        self.description = description
        self.rationale = rationale
        self.config = config

class VisualizationService:
    """Service for generating visualization recommendations and Plotly configurations"""
    
    def __init__(self):
        self.chart_type_mapping = {
            'bar': 'Bar Chart',
            'line': 'Line Chart', 
            'scatter': 'Scatter Plot',
            'pie': 'Pie Chart',
            'histogram': 'Histogram',
            'box': 'Box Plot',
            'heatmap': 'Heatmap',
            'area': 'Area Chart'
        }
    
    def analyze_data_and_recommend(self, query_result: QueryResult) -> VisualizationRecommendation:
        """Analyze query result and recommend best visualization"""
        if not query_result.data or not query_result.columns:
            return self._create_default_recommendation()
        
        # Analyze column types and data patterns
        column_analysis = self._analyze_columns(query_result)
        data_characteristics = self._analyze_data_characteristics(query_result, column_analysis)
        
        # Determine best chart type
        chart_type, rationale = self._determine_chart_type(column_analysis, data_characteristics)
        
        # Generate Plotly configuration
        config = self._generate_plotly_config(query_result, column_analysis, chart_type)
        
        # Create recommendation
        recommendation = VisualizationRecommendation(
            chart_type=chart_type,
            title=self.chart_type_mapping.get(chart_type, chart_type.title()),
            description=f"Recommended visualization for your data with {len(query_result.columns)} columns and {query_result.row_count} rows",
            rationale=rationale,
            config=config
        )
        
        logger.info(f"Generated {chart_type} recommendation for query with {query_result.row_count} rows")
        return recommendation
    
    def _analyze_columns(self, query_result: QueryResult) -> Dict[str, Dict]:
        """Analyze column types and characteristics"""
        analysis = {}
        
        for i, column in enumerate(query_result.columns):
            col_data = [row[i] for row in query_result.data if len(row) > i and row[i] is not None]
            
            if not col_data:
                analysis[column] = {'type': 'unknown', 'unique_count': 0}
                continue
            
            # Determine column type
            col_type = self._infer_column_type(col_data)
            unique_count = len(set(str(val) for val in col_data))
            
            analysis[column] = {
                'type': col_type,
                'unique_count': unique_count,
                'sample_values': col_data[:5],
                'is_categorical': unique_count <= min(10, len(col_data) * 0.5),
                'is_numeric': col_type in ['integer', 'float'],
                'is_date': col_type == 'date',
                'has_nulls': len(col_data) < query_result.row_count
            }
        
        return analysis
    
    def _infer_column_type(self, data: List[Any]) -> str:
        """Infer the type of a column based on its data"""
        if not data:
            return 'unknown'
        
        sample = data[:100]  # Use first 100 values for inference
        
        # Check for dates
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{4}-\d{2}',        # YYYY-MM
        ]
        
        if any(isinstance(val, str) and any(re.match(pattern, str(val)) for pattern in date_patterns) for val in sample):
            return 'date'
        
        # Check for numeric types
        numeric_count = 0
        for val in sample:
            try:
                if isinstance(val, (int, float)):
                    numeric_count += 1
                elif isinstance(val, str):
                    float(val)
                    numeric_count += 1
            except (ValueError, TypeError):
                pass
        
        if numeric_count / len(sample) > 0.8:
            # Check if all numeric values are integers
            if all(isinstance(val, int) or (isinstance(val, float) and val.is_integer()) 
                   or (isinstance(val, str) and '.' not in val) for val in sample):
                return 'integer'
            else:
                return 'float'
        
        return 'string'
    
    def _analyze_data_characteristics(self, query_result: QueryResult, column_analysis: Dict) -> Dict:
        """Analyze overall data characteristics"""
        numeric_cols = [col for col, info in column_analysis.items() if info['is_numeric']]
        categorical_cols = [col for col, info in column_analysis.items() if info['is_categorical']]
        date_cols = [col for col, info in column_analysis.items() if info['is_date']]
        
        return {
            'total_columns': len(query_result.columns),
            'total_rows': query_result.row_count,
            'numeric_columns': len(numeric_cols),
            'categorical_columns': len(categorical_cols),
            'date_columns': len(date_cols),
            'numeric_col_names': numeric_cols,
            'categorical_col_names': categorical_cols,
            'date_col_names': date_cols,
            'is_time_series': len(date_cols) >= 1 and len(numeric_cols) >= 1,
            'is_comparison': len(categorical_cols) >= 1 and len(numeric_cols) >= 1,
            'is_distribution': len(numeric_cols) >= 1 and query_result.row_count > 20
        }
    
    def _determine_chart_type(self, column_analysis: Dict, characteristics: Dict) -> Tuple[str, str]:
        """Determine the best chart type based on data analysis"""
        
        # Time series data
        if characteristics['is_time_series']:
            return 'line', 'Time series data is best visualized with line charts to show trends over time'
        
        # Single numeric column with many rows - histogram
        if characteristics['numeric_columns'] == 1 and characteristics['total_rows'] > 20:
            return 'histogram', 'Single numeric variable with many data points - histogram shows distribution'
        
        # Categorical vs numeric - bar chart
        if characteristics['categorical_columns'] >= 1 and characteristics['numeric_columns'] >= 1:
            # Check if categorical column has reasonable number of categories
            cat_col = characteristics['categorical_col_names'][0]
            if column_analysis[cat_col]['unique_count'] <= 20:
                return 'bar', 'Categorical data with numeric values - bar chart shows comparison between categories'
        
        # Two numeric columns - scatter plot
        if characteristics['numeric_columns'] >= 2:
            return 'scatter', 'Two or more numeric variables - scatter plot shows relationships and correlations'
        
        # Single categorical column with counts - pie chart
        if characteristics['categorical_columns'] == 1 and characteristics['numeric_columns'] == 1:
            cat_col = characteristics['categorical_col_names'][0]
            if column_analysis[cat_col]['unique_count'] <= 8:
                return 'pie', 'Single categorical variable with values - pie chart shows proportional relationships'
        
        # Default to bar chart for mixed data
        if characteristics['categorical_columns'] >= 1:
            return 'bar', 'Mixed data types - bar chart provides clear comparison visualization'
        
        # Fallback to table view for complex data
        return 'bar', 'Data structure suggests bar chart as the most appropriate visualization'
    
    def _generate_plotly_config(self, query_result: QueryResult, column_analysis: Dict, chart_type: str) -> Dict[str, Any]:
        """Generate Plotly configuration for the recommended chart type"""
        
        columns = query_result.columns
        data = query_result.data
        
        if chart_type == 'bar':
            return self._generate_bar_config(columns, data, column_analysis)
        elif chart_type == 'line':
            return self._generate_line_config(columns, data, column_analysis)
        elif chart_type == 'scatter':
            return self._generate_scatter_config(columns, data, column_analysis)
        elif chart_type == 'pie':
            return self._generate_pie_config(columns, data, column_analysis)
        elif chart_type == 'histogram':
            return self._generate_histogram_config(columns, data, column_analysis)
        else:
            return self._generate_bar_config(columns, data, column_analysis)
    
    def _generate_bar_config(self, columns: List[str], data: List[List], column_analysis: Dict) -> Dict[str, Any]:
        """Generate bar chart configuration"""
        # Find categorical and numeric columns
        categorical_cols = [col for col, info in column_analysis.items() if info['is_categorical']]
        numeric_cols = [col for col, info in column_analysis.items() if info['is_numeric']]
        
        if not categorical_cols:
            categorical_cols = [columns[0]]
        if not numeric_cols:
            numeric_cols = [columns[-1]]
        
        x_col = categorical_cols[0]
        y_col = numeric_cols[0]
        
        x_idx = columns.index(x_col)
        y_idx = columns.index(y_col)
        
        x_values = [row[x_idx] for row in data]
        y_values = [row[y_idx] for row in data]
        
        return {
            'data': [{
                'x': x_values,
                'y': y_values,
                'type': 'bar',
                'name': y_col,
                'marker': {
                    'color': 'rgba(55, 128, 191, 0.7)',
                    'line': {
                        'color': 'rgba(55, 128, 191, 1.0)',
                        'width': 1
                    }
                }
            }],
            'layout': {
                'title': f'{y_col} by {x_col}',
                'xaxis': {'title': x_col},
                'yaxis': {'title': y_col},
                'margin': {'l': 60, 'r': 30, 't': 50, 'b': 60}
            },
            'config': {'displayModeBar': True, 'responsive': True}
        }
    
    def _generate_line_config(self, columns: List[str], data: List[List], column_analysis: Dict) -> Dict[str, Any]:
        """Generate line chart configuration"""
        # Find date and numeric columns
        date_cols = [col for col, info in column_analysis.items() if info['is_date']]
        numeric_cols = [col for col, info in column_analysis.items() if info['is_numeric']]
        
        if not date_cols:
            date_cols = [columns[0]]
        if not numeric_cols:
            numeric_cols = [columns[-1]]
        
        x_col = date_cols[0]
        y_col = numeric_cols[0]
        
        x_idx = columns.index(x_col)
        y_idx = columns.index(y_col)
        
        x_values = [row[x_idx] for row in data]
        y_values = [row[y_idx] for row in data]
        
        return {
            'data': [{
                'x': x_values,
                'y': y_values,
                'type': 'scatter',
                'mode': 'lines+markers',
                'name': y_col,
                'line': {'color': 'rgb(55, 128, 191)', 'width': 2},
                'marker': {'size': 6}
            }],
            'layout': {
                'title': f'{y_col} over {x_col}',
                'xaxis': {'title': x_col},
                'yaxis': {'title': y_col},
                'margin': {'l': 60, 'r': 30, 't': 50, 'b': 60}
            },
            'config': {'displayModeBar': True, 'responsive': True}
        }
    
    def _generate_scatter_config(self, columns: List[str], data: List[List], column_analysis: Dict) -> Dict[str, Any]:
        """Generate scatter plot configuration"""
        numeric_cols = [col for col, info in column_analysis.items() if info['is_numeric']]
        
        if len(numeric_cols) < 2:
            numeric_cols = columns[:2]
        
        x_col = numeric_cols[0]
        y_col = numeric_cols[1]
        
        x_idx = columns.index(x_col)
        y_idx = columns.index(y_col)
        
        x_values = [row[x_idx] for row in data]
        y_values = [row[y_idx] for row in data]
        
        return {
            'data': [{
                'x': x_values,
                'y': y_values,
                'type': 'scatter',
                'mode': 'markers',
                'name': 'Data Points',
                'marker': {
                    'color': 'rgba(55, 128, 191, 0.7)',
                    'size': 8,
                    'line': {'color': 'rgba(55, 128, 191, 1.0)', 'width': 1}
                }
            }],
            'layout': {
                'title': f'{y_col} vs {x_col}',
                'xaxis': {'title': x_col},
                'yaxis': {'title': y_col},
                'margin': {'l': 60, 'r': 30, 't': 50, 'b': 60}
            },
            'config': {'displayModeBar': True, 'responsive': True}
        }
    
    def _generate_pie_config(self, columns: List[str], data: List[List], column_analysis: Dict) -> Dict[str, Any]:
        """Generate pie chart configuration"""
        categorical_cols = [col for col, info in column_analysis.items() if info['is_categorical']]
        numeric_cols = [col for col, info in column_analysis.items() if info['is_numeric']]
        
        if not categorical_cols:
            categorical_cols = [columns[0]]
        if not numeric_cols:
            numeric_cols = [columns[-1]]
        
        labels_col = categorical_cols[0]
        values_col = numeric_cols[0]
        
        labels_idx = columns.index(labels_col)
        values_idx = columns.index(values_col)
        
        labels = [row[labels_idx] for row in data]
        values = [row[values_idx] for row in data]
        
        return {
            'data': [{
                'labels': labels,
                'values': values,
                'type': 'pie',
                'hole': 0.3,
                'textinfo': 'label+percent',
                'textposition': 'outside'
            }],
            'layout': {
                'title': f'Distribution of {values_col} by {labels_col}',
                'margin': {'l': 60, 'r': 60, 't': 50, 'b': 60}
            },
            'config': {'displayModeBar': True, 'responsive': True}
        }
    
    def _generate_histogram_config(self, columns: List[str], data: List[List], column_analysis: Dict) -> Dict[str, Any]:
        """Generate histogram configuration"""
        numeric_cols = [col for col, info in column_analysis.items() if info['is_numeric']]
        
        if not numeric_cols:
            numeric_cols = [columns[0]]
        
        col = numeric_cols[0]
        col_idx = columns.index(col)
        
        values = [row[col_idx] for row in data]
        
        return {
            'data': [{
                'x': values,
                'type': 'histogram',
                'name': col,
                'marker': {'color': 'rgba(55, 128, 191, 0.7)'},
                'nbinsx': min(20, len(set(values)))
            }],
            'layout': {
                'title': f'Distribution of {col}',
                'xaxis': {'title': col},
                'yaxis': {'title': 'Frequency'},
                'margin': {'l': 60, 'r': 30, 't': 50, 'b': 60}
            },
            'config': {'displayModeBar': True, 'responsive': True}
        }
    
    def _create_default_recommendation(self) -> VisualizationRecommendation:
        """Create default recommendation when data is insufficient"""
        return VisualizationRecommendation(
            chart_type='bar',
            title='Default Visualization',
            description='No data available for visualization',
            rationale='Insufficient data to generate specific recommendations',
            config={
                'data': [{'x': ['No Data'], 'y': [0], 'type': 'bar'}],
                'layout': {'title': 'No Data Available'},
                'config': {'displayModeBar': False}
            }
        )
    
    async def generate_ai_recommendation(self, query_result: QueryResult, model_key: str = None) -> Dict[str, Any]:
        """Generate AI-powered visualization recommendation using LLM"""
        try:
            # Prepare data summary for LLM
            data_summary = {
                'columns': query_result.columns,
                'row_count': query_result.row_count,
                'sample_data': query_result.data[:5] if query_result.data else [],
                'column_analysis': self._analyze_columns(query_result)
            }
            
            messages = [
                {
                    "role": "system",
                    "content": """You are a data visualization expert. Analyze the provided query result data and recommend the best chart type and configuration. 
                    
                    Respond with JSON containing:
                    {
                        "chart_type": "bar|line|scatter|pie|histogram|box|heatmap",
                        "rationale": "explanation for why this chart type is best",
                        "x_column": "column name for x-axis",
                        "y_column": "column name for y-axis", 
                        "title": "suggested chart title",
                        "insights": ["key insight 1", "key insight 2"]
                    }"""
                },
                {
                    "role": "user",
                    "content": f"Analyze this data and recommend visualization:\n{json.dumps(data_summary, indent=2)}"
                }
            ]
            
            response = await unified_llm_service.generate_json_completion(
                messages=messages,
                model_key=model_key,
                temperature=0.3,
                max_tokens=1000
            )
            
            logger.info(f"Generated AI visualization recommendation: {response.get('chart_type', 'unknown')}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating AI recommendation: {str(e)}")
            return {
                "chart_type": "bar",
                "rationale": "Default recommendation due to AI service error",
                "x_column": query_result.columns[0] if query_result.columns else "x",
                "y_column": query_result.columns[-1] if query_result.columns else "y",
                "title": "Data Visualization",
                "insights": []
            }

    async def recommend_visualization(self, data_sample: List[Dict[str, Any]], 
                                    data_summary: Dict[str, Any] = None,
                                    user_intent: str = None,
                                    model_key: str = None) -> 'VisualizationRecommendation':
        """
        Legacy method for visualization recommendation (used by API)
        Converts data format and calls analyze_data_and_recommend
        """
        try:
            if not data_sample:
                return self._create_default_recommendation()
            
            # Convert data format to QueryResult format
            columns = list(data_sample[0].keys()) if data_sample else []
            data = [[row.get(col) for col in columns] for row in data_sample]
            row_count = len(data_sample)
            
            # Create a QueryResult-like object
            from types import SimpleNamespace
            query_result = SimpleNamespace(
                columns=columns,
                data=data,
                row_count=row_count
            )
            
            # Use existing analysis method
            recommendation = self.analyze_data_and_recommend(query_result)
            
            # Convert to expected format for API compatibility
            return type('VisualizationRecommendation', (), {
                'chart_type': recommendation.chart_type,
                'chart_config': recommendation.config,
                'reasoning': recommendation.rationale,
                'confidence': 0.8,  # Default confidence
                'alternative_charts': ['table', 'bar', 'line', 'scatter']
            })()
            
        except Exception as e:
            logger.error(f"Error in recommend_visualization: {str(e)}")
            # Return fallback recommendation
            return type('VisualizationRecommendation', (), {
                'chart_type': 'bar',
                'chart_config': {
                    'data': [{'x': ['Error'], 'y': [1], 'type': 'bar'}],
                    'layout': {'title': 'Visualization Error'},
                    'config': {'displayModeBar': False}
                },
                'reasoning': f'Error generating recommendation: {str(e)}',
                'confidence': 0.1,
                'alternative_charts': ['table']
            })()

# Global service instance
visualization_service = VisualizationService() 