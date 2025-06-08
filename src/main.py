"""
Main FastAPI application
"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.config.logging_config import setup_logging, get_service_logger, log_service_health
from src.api.system import router as system_router
from src.api.lineage import router as lineage_router
from src.api.ai_suggestions import router as ai_suggestions_router
from src.api.ontology import router as ontology_router
from src.api.activity_logs import router as activity_logs_router
from src.api.analysis import router as analysis_router
from src.api.datasources import router as datasources_router
from src.api.catalog import router as catalog_router
from src.services.activity_log_service import activity_log_service


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    # Initialize logging system first
    setup_logging()
    
    # Get application logger
    app_logger = get_service_logger("ontology")  # Use ontology as main app logger
    
    settings = get_settings()
    
    app_logger.info("Creating FastAPI application", 
                   app_name=settings.app_name,
                   version=settings.app_version,
                   environment=settings.app_env)
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Python-based open-source ontology platform",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount static files
    app.mount("/static", StaticFiles(directory="src/web/static"), name="static")
    
    # Configure templates
    templates = Jinja2Templates(directory="src/web/templates")
    
    @app.get("/")
    async def root(request: Request):
        """Root endpoint with web interface"""
        # Log page view
        activity_log_service.log_page_view("index", "anonymous", request.client.host if request.client else None)
        
        return templates.TemplateResponse(
            "index.html", 
            {"request": request, "title": settings.app_name}
        )
    
    @app.get("/datasources")
    async def datasources_page(request: Request):
        """Data sources management page"""
        # Log page view
        activity_log_service.log_page_view("datasources", "anonymous", request.client.host if request.client else None)
        
        return templates.TemplateResponse(
            "datasources.html",
            {"request": request, "title": f"Data Sources - {settings.app_name}"}
        )
    
    @app.get("/catalog")
    async def catalog_page(request: Request):
        """Data catalog browser page"""
        # Log page view
        activity_log_service.log_page_view("catalog", "anonymous", request.client.host if request.client else None)
        
        return templates.TemplateResponse(
            "catalog.html",
            {"request": request, "title": f"Data Catalog - {settings.app_name}"}
        )
    
    @app.get("/ontology")
    async def ontology_page(request: Request):
        """Ontology management page"""
        # Log page view
        activity_log_service.log_page_view("ontology", "anonymous", request.client.host if request.client else None)
        
        return templates.TemplateResponse(
            "ontology.html",
            {"request": request, "title": f"Ontology Management - {settings.app_name}"}
        )
    
    @app.get("/analysis")
    async def analysis_page(request: Request):
        """SQL Analysis page with Trino MPP engine"""
        # Log page view
        activity_log_service.log_page_view("analysis", "anonymous", request.client.host if request.client else None)
        
        return templates.TemplateResponse(
            "analysis.html",
            {"request": request, "title": f"SQL Analysis - {settings.app_name}"}
        )
    
    @app.get("/activity-logs")
    async def activity_logs_page(request: Request):
        """Activity logs page"""
        # Log page view
        activity_log_service.log_page_view("activity-logs", "anonymous", request.client.host if request.client else None)
        
        return templates.TemplateResponse(
            "activity_logs.html",
            {"request": request, "title": f"Activity Logs - {settings.app_name}"}
        )
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "app_name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env
        }
    
    # Include API routers
    app.include_router(system_router, prefix=settings.api_v1_prefix)
    app.include_router(lineage_router, prefix=settings.api_v1_prefix)
    app.include_router(ai_suggestions_router, prefix=settings.api_v1_prefix)
    app.include_router(ontology_router, prefix=settings.api_v1_prefix)
    app.include_router(activity_logs_router, prefix=settings.api_v1_prefix)
    app.include_router(analysis_router, prefix=settings.api_v1_prefix)
    app.include_router(datasources_router, prefix=settings.api_v1_prefix)
    app.include_router(catalog_router, prefix=settings.api_v1_prefix)
    
    app_logger.success("FastAPI application created successfully")
    
    # Log service health status
    log_service_health()
    
    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    
    # Get application logger
    app_logger = get_service_logger("ontology")
    
    app_logger.info(f"Starting {settings.app_name} v{settings.app_version}",
                   app_name=settings.app_name,
                   version=settings.app_version,
                   environment=settings.app_env,
                   host="0.0.0.0",
                   port=8000,
                   reload=settings.is_development)
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    ) 