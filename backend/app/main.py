import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import settings
from app.routers import jobs, career

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="CareerMatch AI - Intelligent Job-Matching, Verification & Career Roadmap Acceleration System"
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(jobs.router, prefix=settings.API_PREFIX)
app.include_router(career.router, prefix=settings.API_PREFIX)

# Frontend static serving
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))

if os.path.exists(FRONTEND_DIR):
    # Mount frontend static folders for scripts and styles
    src_dir = os.path.join(FRONTEND_DIR, "src")
    if os.path.exists(src_dir):
        app.mount("/src", StaticFiles(directory=src_dir), name="src")

    vendor_dir = os.path.join(FRONTEND_DIR, "vendor")
    if os.path.exists(vendor_dir):
        app.mount("/vendor", StaticFiles(directory=vendor_dir), name="vendor")

    @app.get("/")
    def serve_frontend():
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {
            "system": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "Online",
            "documentation": "/docs"
        }
else:
    @app.get("/")
    def root():
        return {
            "system": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "Online",
            "documentation": "/docs"
        }

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
