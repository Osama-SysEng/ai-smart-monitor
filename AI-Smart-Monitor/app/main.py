import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from contextvars import ContextVar

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import DomainError
from app.core.identity import resolve_identity
from app.core.metrics import runtime_metrics
from app.db.session import SessionLocal, init_db

request_id_context: ContextVar[str] = ContextVar("request_id", default="")
_hits: defaultdict[str, list[float]] = defaultdict(list)


def request_id() -> str:
    return request_id_context.get()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.environment in {"development", "test"}:
        init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Operational intelligence, deterministic reconciliation, investigation, and controlled execution platform",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Request-Id"],
)


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message, "details": exc.details or {}, "request_id": request_id()}})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed", "details": {"errors": exc.errors()}, "request_id": request_id()}})


@app.middleware("http")
async def request_controls(request: Request, call_next):
    correlation_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex
    token = request_id_context.set(correlation_id)
    started_at = time.perf_counter()
    runtime_metrics.started()
    try:
        if request.method in {"POST", "PUT", "PATCH"}:
            content_length = int(request.headers.get("content-length", "0") or 0)
            if content_length > settings.max_upload_bytes:
                return JSONResponse({"error": {"code": "PAYLOAD_TOO_LARGE", "message": "Request exceeds configured upload limit", "request_id": correlation_id}}, status_code=413)
        public_paths = {"/", "/api/v1/health", "/api/v1/health/ready"}
        if request.url.path not in public_paths:
            try:
                with SessionLocal() as db:
                    request.state.identity = resolve_identity(request, db)
            except HTTPException as exc:
                return JSONResponse({"error": {"code": "UNAUTHORIZED", "message": str(exc.detail), "request_id": correlation_id}}, status_code=exc.status_code)
        client_key = request.client.host if request.client else "unknown"
        now = time.time()
        _hits[client_key] = [timestamp for timestamp in _hits[client_key] if now - timestamp < 60]
        if len(_hits[client_key]) >= settings.rate_limit_per_minute:
            return JSONResponse({"error": {"code": "RATE_LIMITED", "message": "Rate limit exceeded", "request_id": correlation_id}}, status_code=429)
        _hits[client_key].append(now)
        response = await call_next(request)
        response.headers["X-Request-Id"] = correlation_id
        route = getattr(request.scope.get("route"), "path", request.url.path)
        runtime_metrics.record(route, response.status_code, time.perf_counter() - started_at)
        return response
    finally:
        runtime_metrics.completed()
        request_id_context.reset(token)


@app.get("/")
def root():
    return {"name": settings.app_name, "version": settings.version, "docs": "/docs", "health": "/api/v1/health"}


app.include_router(api_router, prefix="/api/v1")
