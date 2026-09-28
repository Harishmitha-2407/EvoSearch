import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import init_db
from app.api import health, documents, search, chat, comparison, code, timeline, auth

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("evosearch")

app = FastAPI(
    title="EVOSearch API",
    description="AI-powered document & code evolution intelligence platform.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    logger.info(f"Starting {settings.APP_NAME} (env={settings.ENV})")
    
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database init failed: {e}", exc_info=True)
    
    logger.info(f"✅ {settings.APP_NAME} backend started successfully")
    logger.info("Note: Embedding model will be loaded on first use (may take 1-2 minutes for initial download)")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Log full detail server-side
    logger.exception(f"Unhandled error on {request.method} {request.url.path}")
    
    # In development, return the actual error; in production return generic
    if settings.ENV == "development":
        return JSONResponse(
            status_code=500,
            content={"detail": f"Server error: {str(exc)}"},
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred. It has been logged."},
        )


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(comparison.router)
app.include_router(code.router)
app.include_router(timeline.router)


@app.get("/")
def root():
    return {"name": settings.APP_NAME, "status": "running", "docs": "/docs"}
