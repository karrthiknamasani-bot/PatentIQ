import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.documents import router as documents_router
from app.api.routes.retrieval import router as retrieval_router
from app.api.routes.features import router as features_router
from app.api.routes.mapping import router as mapping_router
from app.api.routes.readiness import router as readiness_router
from app.api.routes.explanation import router as explanation_router
from app.api.routes.projects import router as projects_router
from app.api.routes.pipeline import router as pipeline_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("patentiq.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting %s v%s [environment: %s]",
        settings.PROJECT_NAME,
        settings.VERSION,
        settings.ENVIRONMENT,
    )
    # Pre-warm Qdrant collection, BM25 index, BGE dense embeddings, and Cross-Encoder model
    try:
        from app.services.retrieval.qdrant_store import QdrantVectorStore
        from app.services.retrieval.retrieval_service import retrieval_service
        from app.services.mapping.mapping_service import patent_mapping_service
        
        qdrant_store = QdrantVectorStore()
        qdrant_store.ensure_collection(dimension=settings.BGE_DIMENSION)
        
        # Pre-warm BM25 and BGE dense embedding index
        retrieval_service.initialize_from_corpus(index_dense=True)
        
        # Pre-warm Cross-Encoder reranker model
        _ = retrieval_service.reranker_service
        retrieval_service.reranker_service.reranker.score([("warmup", "passage")])
        
        # Pre-warm mapping service embedding provider
        _ = patent_mapping_service.matcher.get_embedding_provider()
        
        logger.info("Startup retrieval engine, BGE models, and Cross-Encoder pre-warmed successfully.")
    except Exception as exc:
        logger.warning("Startup retrieval pre-warm deferred: %s", exc)
    yield
    logger.info("Stopping %s", settings.PROJECT_NAME)



app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="PatentIQ - Evidence-Based AI Patent Readiness Assessment System API",
    lifespan=lifespan,
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# CORS Configuration
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include Routers
app.include_router(health_router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(documents_router, prefix=f"{settings.API_V1_STR}/documents", tags=["Documents"])
app.include_router(retrieval_router, prefix=f"{settings.API_V1_STR}/retrieval", tags=["Retrieval"])
app.include_router(features_router, prefix=f"{settings.API_V1_STR}/features", tags=["Features"])
app.include_router(mapping_router, prefix=f"{settings.API_V1_STR}/mapping", tags=["Mapping"])
app.include_router(readiness_router, prefix=f"{settings.API_V1_STR}/readiness", tags=["Readiness"])
app.include_router(explanation_router, prefix=f"{settings.API_V1_STR}/explanation", tags=["Explanation"])
app.include_router(projects_router, prefix=f"{settings.API_V1_STR}/projects", tags=["Projects"])
app.include_router(pipeline_router, prefix=f"{settings.API_V1_STR}/pipeline", tags=["Pipeline"])


@app.get("/", include_in_schema=False)
async def root():
    """Root redirect / basic service banner."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": f"{settings.API_V1_STR}/docs",
    }


@app.get("/docs", include_in_schema=False)
async def docs_redirect():
    """Convenience redirect from /docs to /api/docs."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"{settings.API_V1_STR}/docs")
