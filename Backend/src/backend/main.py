import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import CORS_ORIGINS
from backend.routers import auth, tasks
from backend.store import store


@asynccontextmanager
async def lifespan(app: FastAPI):
    store.init_db()
    yield


app = FastAPI(
    title="Mini Personal Kanban API",
    description=(
        "RESTful API specification for the Mini Personal Kanban board application. "
        "Supports single-board personal task management with authentication, "
        "fixed columns (Ideas, To Do, In Progress, Done), priority levels, "
        "due dates, drag-and-drop reordering/column movement, and clearing completed tasks."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from fastapi.exceptions import RequestValidationError


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail_message = str(exc.detail) if isinstance(exc.detail, str) else "An error occurred"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": detail_message,
            "detail": exc.detail,
            "statusCode": exc.status_code,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "message": "Validation error: please check your input.",
            "detail": exc.errors(),
            "statusCode": 422,
        },
    )


# Mount routers under /api and also at root to support all client configurations
app.include_router(auth.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")

app.include_router(auth.router)
app.include_router(tasks.router)


@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "mini-kanban-backend"}


# Static files and frontend SPA serving
STATIC_DIR = os.getenv("STATIC_DIR", "")
if not STATIC_DIR or not os.path.exists(STATIC_DIR):
    for candidate in [
        Path("/app/static"),
        Path(__file__).resolve().parent.parent.parent / "static",
        Path(__file__).resolve().parent.parent.parent.parent / "Frontend" / ".output" / "public",
    ]:
        if candidate.exists() and candidate.is_dir():
            STATIC_DIR = str(candidate)
            break

if STATIC_DIR and os.path.exists(STATIC_DIR):
    assets_path = os.path.join(STATIC_DIR, "assets")
    if os.path.exists(assets_path):
        app.mount("/assets", StaticFiles(directory=assets_path), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(STATIC_DIR, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        index_file = os.path.join(STATIC_DIR, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Not Found")


def main():
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
