"""
Data Lineage API endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from loguru import logger

from src.models.lineage import (
    LineageQueryRequest, LineageQueryResponse, LineageMetrics,
    ColumnLineage, LineageDataset, LineageJob, LineageRun
)
from src.services.lineage_service import lineage_service

router = APIRouter(tags=["lineage"])


@router.get("/lineage/query", response_model=LineageQueryResponse)
async def query_lineage(
    dataset_name: Optional[str] = Query(None, description="Dataset name to trace"),
    job_name: Optional[str] = Query(None, description="Job name to trace"),
    direction: str = Query("both", description="Direction: upstream, downstream, or both"),
    depth: int = Query(3, description="Maximum depth to traverse"),
    include_schema: bool = Query(True, description="Include schema information")
):
    """Query data lineage graph"""
    try:
        request = LineageQueryRequest(
            dataset_name=dataset_name,
            job_name=job_name,
            direction=direction,
            depth=depth,
            include_schema=include_schema
        )
        
        logger.info(f"Querying lineage: {request}")
        result = lineage_service.query_lineage(request)
        
        logger.info(f"Lineage query completed: {result.total_datasets} datasets, {result.total_jobs} jobs")
        return result
        
    except Exception as e:
        logger.error(f"Error querying lineage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lineage/datasets", response_model=Dict[str, LineageDataset])
async def get_all_datasets():
    """Get all datasets in lineage"""
    try:
        return lineage_service.datasets
    except Exception as e:
        logger.error(f"Error getting datasets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lineage/jobs", response_model=Dict[str, LineageJob]) 
async def get_all_jobs():
    """Get all jobs in lineage"""
    try:
        return lineage_service.jobs
    except Exception as e:
        logger.error(f"Error getting jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lineage/runs", response_model=List[LineageRun])
async def get_all_runs():
    """Get all runs in lineage"""
    try:
        return lineage_service.runs
    except Exception as e:
        logger.error(f"Error getting runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lineage/column/{dataset_name}", response_model=List[ColumnLineage])
async def get_column_lineage(
    dataset_name: str,
    column_name: Optional[str] = Query(None, description="Specific column name")
):
    """Get column-level lineage for a dataset"""
    try:
        result = lineage_service.get_column_lineage(dataset_name, column_name)
        logger.info(f"Found {len(result)} column lineage entries for {dataset_name}")
        return result
    except Exception as e:
        logger.error(f"Error getting column lineage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lineage/metrics", response_model=LineageMetrics)
async def get_lineage_metrics():
    """Get lineage metrics and statistics"""
    try:
        metrics = lineage_service.get_metrics()
        logger.info(f"Retrieved lineage metrics: {metrics.total_datasets} datasets, {metrics.total_jobs} jobs")
        return metrics
    except Exception as e:
        logger.error(f"Error getting lineage metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lineage/impact/{dataset_name}")
async def get_impact_analysis(dataset_name: str):
    """Get impact analysis for a dataset"""
    try:
        analysis = lineage_service.get_dataset_impact_analysis(dataset_name)
        logger.info(f"Impact analysis for {dataset_name}: {analysis}")
        return analysis
    except Exception as e:
        logger.error(f"Error getting impact analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lineage/export")
async def export_lineage(
    format: str = Query("json", description="Export format: json, graphml, or dot")
):
    """Export lineage graph in various formats"""
    try:
        if format not in ["json", "graphml", "dot"]:
            raise HTTPException(status_code=400, detail="Invalid format. Use json, graphml, or dot")
        
        content = lineage_service.export_lineage_graph(format)
        
        # Set appropriate content type
        content_types = {
            "json": "application/json",
            "graphml": "application/xml", 
            "dot": "text/plain"
        }
        
        return PlainTextResponse(
            content=content,
            media_type=content_types[format],
            headers={
                "Content-Disposition": f"attachment; filename=lineage.{format}"
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting lineage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lineage/datasets", response_model=dict)
async def add_dataset(dataset: LineageDataset):
    """Add a new dataset to lineage"""
    try:
        lineage_service.add_dataset(dataset)
        logger.info(f"Added dataset: {dataset.qualified_name}")
        return {"status": "success", "message": f"Dataset {dataset.qualified_name} added"}
    except Exception as e:
        logger.error(f"Error adding dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lineage/jobs", response_model=dict)
async def add_job(job: LineageJob):
    """Add a new job to lineage"""
    try:
        lineage_service.add_job(job)
        logger.info(f"Added job: {job.qualified_name}")
        return {"status": "success", "message": f"Job {job.qualified_name} added"}
    except Exception as e:
        logger.error(f"Error adding job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lineage/runs", response_model=dict)
async def add_run(run: LineageRun):
    """Add a new run to lineage"""
    try:
        lineage_service.add_run(run)
        logger.info(f"Added run: {run.run_id}")
        return {"status": "success", "message": f"Run {run.run_id} added"}
    except Exception as e:
        logger.error(f"Error adding run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lineage/graph/visualization")
async def get_lineage_visualization(
    dataset_name: Optional[str] = Query(None, description="Dataset to center visualization on"),
    format: str = Query("json", description="Visualization format: json or cytoscape")
):
    """Get lineage graph data formatted for visualization"""
    try:
        # Query lineage data
        request = LineageQueryRequest(
            dataset_name=dataset_name if dataset_name else "customers",
            direction="both",
            depth=3,
            include_schema=False
        )
        
        result = lineage_service.query_lineage(request)
        
        if format == "cytoscape":
            # Format for Cytoscape.js
            nodes = []
            edges = []
            
            # Add dataset nodes
            for name, dataset in result.graph.datasets.items():
                nodes.append({
                    "data": {
                        "id": name,
                        "label": dataset.name,
                        "type": "dataset",
                        "dataset_type": dataset.type.value,
                        "namespace": dataset.namespace
                    },
                    "classes": f"dataset {dataset.type.value}"
                })
            
            # Add job nodes
            for name, job in result.graph.jobs.items():
                nodes.append({
                    "data": {
                        "id": name,
                        "label": job.name,
                        "type": "job",
                        "job_type": job.type.value,
                        "namespace": job.namespace,
                        "description": job.description
                    },
                    "classes": f"job {job.type.value}"
                })
            
            # Add edges
            for relationship in result.graph.relationships:
                edges.append({
                    "data": {
                        "id": f"{relationship['source']}-{relationship['target']}",
                        "source": relationship['source'],
                        "target": relationship['target'],
                        "type": relationship['type']
                    },
                    "classes": relationship['type']
                })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "query": request.model_dump(),
                "stats": {
                    "total_datasets": result.total_datasets,
                    "total_jobs": result.total_jobs,
                    "execution_time_ms": result.execution_time_ms
                }
            }
        
        else:
            # Return raw JSON format
            return {
                "graph": result.graph.model_dump(),
                "query": request.model_dump(),
                "stats": {
                    "total_datasets": result.total_datasets,
                    "total_jobs": result.total_jobs,
                    "execution_time_ms": result.execution_time_ms
                }
            }
        
    except Exception as e:
        logger.error(f"Error getting lineage visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 