import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.websockets import WebSocket

from app.config import settings
from app.database import Base, engine

from app.routers.auth import router as auth_router
from app.routers.cameras import router as cameras_router
from app.routers.incidents import router as incidents_router
from app.routers.notifications import router as notifications_router
from app.routers.dashboard import router as dashboard_router
from app.routers.streams import router as streams_router

# --------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sitesafe")

# --------------------------------------------------------------------
# Database
# --------------------------------------------------------------------
# Creates tables if they don't already exist.
# For production use Alembic migrations instead.
Base.metadata.create_all(bind=engine)

# --------------------------------------------------------------------
# FastAPI App
# --------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

# --------------------------------------------------------------------
# CORS
# --------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------
# Routers
# --------------------------------------------------------------------
app.include_router(auth_router)
app.include_router(cameras_router)
app.include_router(incidents_router)
app.include_router(notifications_router)
app.include_router(dashboard_router)
app.include_router(streams_router)

# --------------------------------------------------------------------
# Exception Handlers
# --------------------------------------------------------------------
from fastapi.responses import JSONResponse
from starlette.websockets import WebSocket

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    if isinstance(request, WebSocket):
        logger.warning(
            "WebSocket HTTPException on %s: %s",
            request.url.path,
            exc.detail,
        )
        # Don't return a JSON response for WebSockets.
        return

    logger.warning(
        "HTTPException on %s %s: %s",
        request.method,
        request.url.path,
        exc.detail,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled error on %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# --------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------
@app.get("/")
def home():
    return {
        "message": "SiteSafe backend running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }