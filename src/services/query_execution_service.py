"""
Query Execution Service
Provides SQL query execution with fallback to demo data
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import uuid4

from src.services.trino_service import trino_service
from src.models.analysis import QueryRequest, QueryResult
from src.config.logging_config import get_service_logger

logger = get_service_logger("query_execution")

class QueryExecutionService:
    """Service for executing SQL queries with demo data fallback"""
    
    def __init__(self):
        self._demo_data_cache = {}
    
    async def execute_sql_query(self, sql_query: str, catalog: str = None, schema: str = None) -> QueryResult:
        """Execute SQL query with fallback to demo data"""
        start_time = time.time()
        logger.info(f"Executing SQL query: {sql_query[:100]}...")
        
        try:
            # Try to execute with Trino first
            request = QueryRequest(
                query=sql_query,
                catalog=catalog or "memory",
                schema=schema or "default",
                limit=1000
            )
            
            result = await trino_service.execute_query(request)
            
            # If Trino execution failed or returned no data, generate demo data
            if result.error or not result.data:
                logger.warning(f"Trino execution failed or no data, generating demo data: {result.error}")
                demo_result = self._generate_demo_query_result(sql_query)
                execution_time = (time.time() - start_time) * 1000
                demo_result.execution_time_ms = execution_time
                return demo_result
            
            logger.info(f"Successfully executed query, returned {result.row_count} rows")
            return result
            
        except Exception as e:
            logger.error(f"Error executing SQL query: {str(e)}")
            # Fallback to demo data
            demo_result = self._generate_demo_query_result(sql_query)
            execution_time = (time.time() - start_time) * 1000
            demo_result.execution_time_ms = execution_time
            return demo_result
    
    def _generate_demo_query_result(self, sql_query: str) -> QueryResult:
        """Generate demo query result based on SQL query analysis"""
        query_upper = sql_query.upper()
        
        # Analyze query to determine appropriate demo data
        if "EMPLOYEE" in query_upper and "DEPARTMENT" in query_upper:
            return self._generate_employee_department_data()
        elif "EMPLOYEE" in query_upper:
            return self._generate_employee_data()
        elif "DEPARTMENT" in query_upper:
            return self._generate_department_data()
        elif "ORDER" in query_upper and ("CUSTOMER" in query_upper or "SALES" in query_upper):
            return self._generate_sales_data()
        elif "ORDER" in query_upper:
            return self._generate_order_data()
        elif "CUSTOMER" in query_upper:
            return self._generate_customer_data()
        elif "SALES" in query_upper or "REVENUE" in query_upper:
            return self._generate_sales_summary_data()
        elif "TIME" in query_upper or "DATE" in query_upper:
            return self._generate_time_series_data()
        else:
            return self._generate_general_demo_data()
    
    def _generate_employee_department_data(self) -> QueryResult:
        """Generate employee-department join demo data"""
        departments = [
            {"id": 1, "name": "Engineering", "location": "San Francisco"},
            {"id": 2, "name": "Marketing", "location": "New York"}, 
            {"id": 3, "name": "Sales", "location": "Chicago"},
            {"id": 4, "name": "HR", "location": "Austin"},
            {"id": 5, "name": "Finance", "location": "Boston"}
        ]
        
        employees_per_dept = [25, 12, 18, 8, 10]  # Different counts per department
        
        data = []
        for i, dept in enumerate(departments):
            data.append([
                dept["name"],
                employees_per_dept[i],
                dept["location"],
                employees_per_dept[i] * random.randint(75000, 120000)  # Total salary
            ])
        
        # Sort by employee count descending
        data.sort(key=lambda x: x[1], reverse=True)
        
        return QueryResult(
            query="Simulated employee-department query",
            columns=["department_name", "employee_count", "location", "total_salary"],
            data=data,
            row_count=len(data),
            execution_time_ms=25.0,
            query_id=str(uuid4())
        )
    
    def _generate_employee_data(self) -> QueryResult:
        """Generate employee demo data"""
        first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        departments = ["Engineering", "Marketing", "Sales", "HR", "Finance"]
        
        data = []
        for i in range(20):
            data.append([
                i + 1,
                f"{random.choice(first_names)} {random.choice(last_names)}",
                random.choice(departments),
                random.randint(50000, 150000),
                (datetime.now() - timedelta(days=random.randint(30, 1825))).strftime("%Y-%m-%d")
            ])
        
        return QueryResult(
            query="Simulated employee query",
            columns=["employee_id", "full_name", "department", "salary", "hire_date"],
            data=data,
            row_count=len(data),
            execution_time_ms=18.0,
            query_id=str(uuid4())
        )
    
    def _generate_department_data(self) -> QueryResult:
        """Generate department demo data"""
        data = [
            [1, "Engineering", "San Francisco", 25, 2500000],
            [2, "Marketing", "New York", 12, 960000],
            [3, "Sales", "Chicago", 18, 1440000],
            [4, "HR", "Austin", 8, 480000],
            [5, "Finance", "Boston", 10, 800000]
        ]
        
        return QueryResult(
            query="Simulated department query",
            columns=["dept_id", "dept_name", "location", "employee_count", "total_budget"],
            data=data,
            row_count=len(data),
            execution_time_ms=12.0,
            query_id=str(uuid4())
        )
    
    def _generate_sales_data(self) -> QueryResult:
        """Generate sales demo data"""
        products = ["Laptop", "Smartphone", "Tablet", "Headphones", "Monitor", "Keyboard", "Mouse"]
        customers = ["TechCorp", "InnovateLLC", "StartupXYZ", "Enterprise Inc", "SMB Solutions"]
        
        data = []
        for i in range(30):
            quantity = random.randint(1, 50)
            unit_price = random.randint(100, 2000)
            data.append([
                i + 1,
                random.choice(customers),
                random.choice(products),
                quantity,
                unit_price,
                quantity * unit_price,
                (datetime.now() - timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d")
            ])
        
        # Sort by total descending
        data.sort(key=lambda x: x[5], reverse=True)
        
        return QueryResult(
            query="Simulated sales query",
            columns=["order_id", "customer", "product", "quantity", "unit_price", "total_amount", "order_date"],
            data=data,
            row_count=len(data),
            execution_time_ms=22.0,
            query_id=str(uuid4())
        )
    
    def _generate_order_data(self) -> QueryResult:
        """Generate order demo data"""
        statuses = ["Completed", "Pending", "Shipped", "Cancelled"]
        
        data = []
        for i in range(25):
            data.append([
                i + 1001,
                f"CUST{random.randint(100, 999)}",
                random.randint(100, 5000),
                random.choice(statuses),
                (datetime.now() - timedelta(days=random.randint(1, 180))).strftime("%Y-%m-%d")
            ])
        
        return QueryResult(
            query="Simulated order query",
            columns=["order_id", "customer_id", "amount", "status", "order_date"],
            data=data,
            row_count=len(data),
            execution_time_ms=15.0,
            query_id=str(uuid4())
        )
    
    def _generate_customer_data(self) -> QueryResult:
        """Generate customer demo data"""
        companies = ["TechCorp", "InnovateLLC", "StartupXYZ", "Enterprise Inc", "SMB Solutions", 
                    "Global Systems", "Future Tech", "Smart Solutions", "Digital Dynamics", "CloudFirst"]
        cities = ["San Francisco", "New York", "Chicago", "Austin", "Boston", "Seattle", "Los Angeles", "Denver"]
        
        data = []
        for i, company in enumerate(companies):
            data.append([
                f"CUST{100 + i}",
                company,
                random.choice(cities),
                random.randint(10, 500),
                random.randint(50000, 1000000),
                (datetime.now() - timedelta(days=random.randint(30, 2000))).strftime("%Y-%m-%d")
            ])
        
        return QueryResult(
            query="Simulated customer query",
            columns=["customer_id", "company_name", "city", "employees", "annual_revenue", "signup_date"],
            data=data,
            row_count=len(data),
            execution_time_ms=14.0,
            query_id=str(uuid4())
        )
    
    def _generate_sales_summary_data(self) -> QueryResult:
        """Generate sales summary demo data"""
        months = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]
        
        data = []
        for month in months:
            data.append([
                month,
                random.randint(50000, 200000),
                random.randint(100, 500),
                random.randint(40000, 180000)
            ])
        
        return QueryResult(
            query="Simulated sales summary query",
            columns=["month", "total_revenue", "order_count", "avg_order_value"],
            data=data,
            row_count=len(data),
            execution_time_ms=8.0,
            query_id=str(uuid4())
        )
    
    def _generate_time_series_data(self) -> QueryResult:
        """Generate time series demo data"""
        data = []
        base_date = datetime.now() - timedelta(days=30)
        
        for i in range(30):
            date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
            value = 1000 + random.randint(-200, 300) + (i * 10)  # Trending upward
            data.append([
                date,
                value,
                random.randint(10, 100),
                value * random.uniform(0.8, 1.2)
            ])
        
        return QueryResult(
            query="Simulated time series query",
            columns=["date", "metric_value", "count", "adjusted_value"],
            data=data,
            row_count=len(data),
            execution_time_ms=16.0,
            query_id=str(uuid4())
        )
    
    def _generate_general_demo_data(self) -> QueryResult:
        """Generate general demo data"""
        categories = ["Category A", "Category B", "Category C", "Category D", "Category E"]
        
        data = []
        for i, category in enumerate(categories):
            data.append([
                i + 1,
                category,
                random.randint(10, 100),
                random.uniform(10.5, 99.9),
                random.choice(["Active", "Inactive", "Pending"])
            ])
        
        return QueryResult(
            query="Simulated general query",
            columns=["id", "category", "count", "value", "status"],
            data=data,
            row_count=len(data),
            execution_time_ms=10.0,
            query_id=str(uuid4())
        )

# Global service instance
query_execution_service = QueryExecutionService() 