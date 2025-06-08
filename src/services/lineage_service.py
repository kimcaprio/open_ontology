"""
Data Lineage Service
OpenLineage-based data lineage tracking and visualization
"""

import json
import time
import networkx as nx
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict
from uuid import uuid4

from src.config.logging_config import get_service_logger

from src.models.lineage import (
    LineageDataset, LineageJob, LineageRun, LineageEvent, LineageGraph,
    LineageQueryRequest, LineageQueryResponse, LineageMetrics, ColumnLineage,
    LineageEventType, DatasetType, JobType,
    DEMO_DATASETS, DEMO_JOBS
)


class LineageService:
    """Service for managing data lineage"""
    
    def __init__(self):
        # Initialize service logger
        self.logger = get_service_logger("lineage")
        
        self.graph = nx.DiGraph()
        self.datasets: Dict[str, LineageDataset] = {}
        self.jobs: Dict[str, LineageJob] = {}
        self.runs: List[LineageRun] = []
        self.events: List[LineageEvent] = []
        self.column_lineage: List[ColumnLineage] = []
        
        # Initialize with demo data
        self._init_demo_data()
    
    def _init_demo_data(self):
        """Initialize service with demo data"""
        start_time = time.time()
        self.logger.log_function_start("_init_demo_data")
        
        try:
            # Add demo datasets
            for dataset in DEMO_DATASETS:
                self.add_dataset(dataset)
            
            # Add demo jobs
            for job in DEMO_JOBS:
                self.add_job(job)
            
            # Create demo runs and relationships
            self._create_demo_relationships()
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "_init_demo_data",
                result=f"Loaded {len(self.datasets)} datasets and {len(self.jobs)} jobs",
                execution_time=execution_time,
                dataset_count=len(self.datasets),
                job_count=len(self.jobs),
                run_count=len(self.runs)
            )
            
        except Exception as e:
            self.logger.log_function_error("_init_demo_data", e)
            raise
    
    def _create_demo_relationships(self):
        """Create demo lineage relationships"""
        # Customer data sync job
        customer_sync_job = self.jobs["etl.customer_data_sync"]
        customers_dataset = self.datasets["production.customers"]
        
        # Analytics pipeline job
        analytics_job = self.jobs["analytics.customer_analytics_pipeline"]
        orders_dataset = self.datasets["production.orders"]
        analytics_dataset = self.datasets["analytics.customer_analytics"]
        
        # Create demo runs
        run1 = LineageRun(
            job=customer_sync_job,
            status=LineageEventType.COMPLETE,
            started_at=datetime.now() - timedelta(hours=1),
            ended_at=datetime.now() - timedelta(minutes=55),
            input_datasets=[],  # External source
            output_datasets=[customers_dataset],
            properties={"records_processed": 10000, "execution_time": 300}
        )
        
        run2 = LineageRun(
            job=analytics_job,
            status=LineageEventType.COMPLETE,
            started_at=datetime.now() - timedelta(minutes=30),
            ended_at=datetime.now() - timedelta(minutes=20),
            input_datasets=[customers_dataset, orders_dataset],
            output_datasets=[analytics_dataset],
            properties={"records_processed": 5000, "execution_time": 600}
        )
        
        self.runs.extend([run1, run2])
        
        # Build graph relationships
        self._build_graph()
        
        # Add column-level lineage
        self._create_demo_column_lineage()
    
    def _create_demo_column_lineage(self):
        """Create demo column-level lineage"""
        self.column_lineage.extend([
            ColumnLineage(
                source_dataset="production.customers",
                source_column="customer_id",
                target_dataset="analytics.customer_analytics",
                target_column="customer_id",
                transformation="direct_copy",
                job_name="analytics.customer_analytics_pipeline"
            ),
            ColumnLineage(
                source_dataset="production.orders",
                source_column="order_total",
                target_dataset="analytics.customer_analytics",
                target_column="total_spent",
                transformation="sum(order_total) group by customer_id",
                job_name="analytics.customer_analytics_pipeline"
            ),
            ColumnLineage(
                source_dataset="production.orders",
                source_column="order_date",
                target_dataset="analytics.customer_analytics",
                target_column="last_order_date",
                transformation="max(order_date) group by customer_id",
                job_name="analytics.customer_analytics_pipeline"
            )
        ])
    
    def _build_graph(self):
        """Build NetworkX graph from lineage data"""
        self.graph.clear()
        
        # Add dataset nodes
        for dataset in self.datasets.values():
            self.graph.add_node(
                dataset.qualified_name,
                type="dataset",
                dataset_type=dataset.type.value,
                namespace=dataset.namespace,
                properties=dataset.properties
            )
        
        # Add job nodes
        for job in self.jobs.values():
            self.graph.add_node(
                job.qualified_name,
                type="job", 
                job_type=job.type.value,
                namespace=job.namespace,
                description=job.description,
                properties=job.properties
            )
        
        # Add edges based on runs
        for run in self.runs:
            job_name = run.job.qualified_name
            
            # Input datasets -> Job
            for input_ds in run.input_datasets:
                self.graph.add_edge(
                    input_ds.qualified_name,
                    job_name,
                    type="input",
                    run_id=str(run.run_id),
                    timestamp=run.started_at.isoformat()
                )
            
            # Job -> Output datasets
            for output_ds in run.output_datasets:
                self.graph.add_edge(
                    job_name,
                    output_ds.qualified_name,
                    type="output",
                    run_id=str(run.run_id),
                    timestamp=run.started_at.isoformat()
                )
    
    def add_dataset(self, dataset: LineageDataset):
        """Add dataset to lineage"""
        start_time = time.time()
        self.logger.log_function_start(
            "add_dataset",
            qualified_name=dataset.qualified_name,
            dataset_type=dataset.type.value,
            namespace=dataset.namespace
        )
        
        try:
            self.datasets[dataset.qualified_name] = dataset
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "add_dataset",
                result=f"Dataset added: {dataset.qualified_name}",
                execution_time=execution_time,
                qualified_name=dataset.qualified_name,
                dataset_type=dataset.type.value,
                total_datasets=len(self.datasets)
            )
            
        except Exception as e:
            self.logger.log_function_error("add_dataset", e, qualified_name=dataset.qualified_name)
            raise
    
    def add_job(self, job: LineageJob):
        """Add job to lineage"""
        start_time = time.time()
        self.logger.log_function_start(
            "add_job",
            qualified_name=job.qualified_name,
            job_type=job.type.value,
            namespace=job.namespace
        )
        
        try:
            self.jobs[job.qualified_name] = job
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "add_job",
                result=f"Job added: {job.qualified_name}",
                execution_time=execution_time,
                qualified_name=job.qualified_name,
                job_type=job.type.value,
                total_jobs=len(self.jobs)
            )
            
        except Exception as e:
            self.logger.log_function_error("add_job", e, qualified_name=job.qualified_name)
            raise
    
    def add_run(self, run: LineageRun):
        """Add run to lineage"""
        start_time = time.time()
        self.logger.log_function_start(
            "add_run",
            run_id=str(run.run_id),
            job_name=run.job.qualified_name,
            status=run.status.value,
            input_count=len(run.input_datasets),
            output_count=len(run.output_datasets)
        )
        
        try:
            self.runs.append(run)
            self._build_graph()  # Rebuild graph with new run
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "add_run",
                result=f"Run added: {run.run_id}",
                execution_time=execution_time,
                run_id=str(run.run_id),
                job_name=run.job.qualified_name,
                total_runs=len(self.runs),
                graph_nodes=self.graph.number_of_nodes(),
                graph_edges=self.graph.number_of_edges()
            )
            
        except Exception as e:
            self.logger.log_function_error("add_run", e, run_id=str(run.run_id))
            raise
    
    def query_lineage(self, request: LineageQueryRequest) -> LineageQueryResponse:
        """Query lineage graph"""
        start_time = time.time()
        self.logger.log_function_start(
            "query_lineage",
            entity_name=request.entity_name,
            direction=request.direction,
            depth=request.depth,
            include_schema=request.include_schema
        )
        
        try:
            query_start_time = datetime.now()
            
            # Determine starting nodes
            start_nodes = self._get_start_nodes(request)
            
            if not start_nodes:
                execution_time = (time.time() - start_time) * 1000
                self.logger.log_function_warning(
                    "query_lineage",
                    "No starting nodes found for query",
                    entity_name=request.entity_name,
                    execution_time=execution_time
                )
                return LineageQueryResponse(
                    query=request,
                    graph=LineageGraph(),
                    total_datasets=0,
                    total_jobs=0,
                    execution_time_ms=int((datetime.now() - query_start_time).total_seconds() * 1000)
                )
            
            # Find connected nodes based on direction and depth
            connected_nodes = self._find_connected_nodes(start_nodes, request.direction, request.depth)
            
            # Build subgraph
            subgraph = self._build_subgraph(connected_nodes, request.include_schema)
            
            response = LineageQueryResponse(
                query=request,
                graph=subgraph,
                total_datasets=len([n for n in connected_nodes if n in self.datasets]),
                total_jobs=len([n for n in connected_nodes if n in self.jobs]),
                execution_time_ms=int((datetime.now() - query_start_time).total_seconds() * 1000)
            )
            
            execution_time = (time.time() - start_time) * 1000
            self.logger.log_function_success(
                "query_lineage",
                result=response,
                execution_time=execution_time,
                entity_name=request.entity_name,
                start_nodes_count=len(start_nodes),
                connected_nodes_count=len(connected_nodes),
                result_datasets=response.total_datasets,
                result_jobs=response.total_jobs,
                query_execution_time=response.execution_time_ms
            )
            
            return response
            
        except Exception as e:
            self.logger.log_function_error("query_lineage", e, entity_name=request.entity_name)
            raise
    
    def _get_start_nodes(self, request: LineageQueryRequest) -> Set[str]:
        """Get starting nodes for lineage query"""
        start_nodes = set()
        
        if request.dataset_name:
            # Find datasets matching the name
            for dataset_name in self.datasets.keys():
                if request.dataset_name.lower() in dataset_name.lower():
                    start_nodes.add(dataset_name)
        
        if request.job_name:
            # Find jobs matching the name
            for job_name in self.jobs.keys():
                if request.job_name.lower() in job_name.lower():
                    start_nodes.add(job_name)
        
        return start_nodes
    
    def _find_connected_nodes(self, start_nodes: Set[str], direction: str, depth: int) -> Set[str]:
        """Find all nodes connected to start nodes"""
        connected = set(start_nodes)
        
        for start_node in start_nodes:
            if direction in ["upstream", "both"]:
                # Find upstream nodes (predecessors)
                upstream = set()
                for d in range(depth):
                    current_level = set()
                    for node in (upstream if d > 0 else {start_node}):
                        current_level.update(self.graph.predecessors(node))
                    if not current_level:
                        break
                    upstream.update(current_level)
                connected.update(upstream)
            
            if direction in ["downstream", "both"]:
                # Find downstream nodes (successors)
                downstream = set()
                for d in range(depth):
                    current_level = set()
                    for node in (downstream if d > 0 else {start_node}):
                        current_level.update(self.graph.successors(node))
                    if not current_level:
                        break
                    downstream.update(current_level)
                connected.update(downstream)
        
        return connected
    
    def _build_subgraph(self, nodes: Set[str], include_schema: bool) -> LineageGraph:
        """Build LineageGraph from selected nodes"""
        subgraph_datasets = {}
        subgraph_jobs = {}
        relationships = []
        
        for node in nodes:
            if node in self.datasets:
                dataset = self.datasets[node]
                if include_schema:
                    subgraph_datasets[node] = dataset
                else:
                    # Create dataset without schema
                    dataset_copy = dataset.model_copy()
                    dataset_copy.schema_fields = None
                    subgraph_datasets[node] = dataset_copy
            
            elif node in self.jobs:
                subgraph_jobs[node] = self.jobs[node]
        
        # Add relationships between selected nodes
        for edge in self.graph.edges(data=True):
            source, target, data = edge
            if source in nodes and target in nodes:
                relationships.append({
                    "source": source,
                    "target": target,
                    "type": data.get("type", "unknown"),
                    "run_id": data.get("run_id"),
                    "timestamp": data.get("timestamp")
                })
        
        # Add runs that involve selected nodes
        relevant_runs = []
        for run in self.runs:
            job_name = run.job.qualified_name
            if job_name in nodes:
                relevant_runs.append(run)
        
        return LineageGraph(
            datasets=subgraph_datasets,
            jobs=subgraph_jobs,
            runs=relevant_runs,
            relationships=relationships
        )
    
    def get_column_lineage(self, dataset_name: str, column_name: Optional[str] = None) -> List[ColumnLineage]:
        """Get column-level lineage for a dataset"""
        result = []
        
        for col_lineage in self.column_lineage:
            if (col_lineage.source_dataset == dataset_name or 
                col_lineage.target_dataset == dataset_name):
                
                if column_name is None or (
                    col_lineage.source_column == column_name or 
                    col_lineage.target_column == column_name
                ):
                    result.append(col_lineage)
        
        return result
    
    def get_metrics(self) -> LineageMetrics:
        """Get lineage metrics and statistics"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        # Calculate metrics
        failed_runs = len([r for r in self.runs if r.status == LineageEventType.FAIL and r.started_at >= last_24h])
        active_jobs = len([r for r in self.runs if r.status == LineageEventType.START])
        
        # Calculate average execution time
        completed_runs = [r for r in self.runs if r.status == LineageEventType.COMPLETE and r.ended_at]
        avg_execution_time = 0
        if completed_runs:
            total_time = sum((r.ended_at - r.started_at).total_seconds() for r in completed_runs)
            avg_execution_time = total_time / len(completed_runs)
        
        return LineageMetrics(
            total_datasets=len(self.datasets),
            total_jobs=len(self.jobs),
            total_runs=len(self.runs),
            active_jobs=active_jobs,
            failed_runs=failed_runs,
            avg_execution_time=avg_execution_time,
            last_updated=now
        )
    
    def get_dataset_impact_analysis(self, dataset_name: str) -> Dict[str, Any]:
        """Analyze impact of changes to a dataset"""
        if dataset_name not in self.datasets:
            return {"error": "Dataset not found"}
        
        # Find downstream dependencies
        downstream_request = LineageQueryRequest(
            dataset_name=dataset_name,
            direction="downstream",
            depth=10
        )
        downstream_result = self.query_lineage(downstream_request)
        
        # Analyze impact
        affected_datasets = len(downstream_result.graph.datasets) - 1  # Exclude the source dataset
        affected_jobs = len(downstream_result.graph.jobs)
        
        return {
            "dataset": dataset_name,
            "affected_datasets": affected_datasets,
            "affected_jobs": affected_jobs,
            "downstream_datasets": list(downstream_result.graph.datasets.keys()),
            "downstream_jobs": list(downstream_result.graph.jobs.keys()),
            "risk_level": "high" if affected_datasets > 5 else "medium" if affected_datasets > 2 else "low"
        }
    
    def export_lineage_graph(self, format: str = "json") -> str:
        """Export lineage graph in various formats"""
        if format == "json":
            return self._export_json()
        elif format == "graphml":
            return self._export_graphml()
        elif format == "dot":
            return self._export_dot()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_json(self) -> str:
        """Export lineage as JSON"""
        graph_data = {
            "datasets": {k: v.model_dump() for k, v in self.datasets.items()},
            "jobs": {k: v.model_dump() for k, v in self.jobs.items()},
            "runs": [r.model_dump() for r in self.runs],
            "column_lineage": [c.model_dump() for c in self.column_lineage]
        }
        return json.dumps(graph_data, indent=2, default=str)
    
    def _export_graphml(self) -> str:
        """Export lineage as GraphML"""
        from io import StringIO
        output = StringIO()
        nx.write_graphml(self.graph, output)
        return output.getvalue()
    
    def _export_dot(self) -> str:
        """Export lineage as DOT format"""
        from io import StringIO
        output = StringIO()
        nx.drawing.nx_agraph.write_dot(self.graph, output)
        return output.getvalue()


# Global service instance
lineage_service = LineageService() 