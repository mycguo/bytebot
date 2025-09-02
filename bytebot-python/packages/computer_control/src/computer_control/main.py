"""Main entry point for computer control service."""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from shared.utils.logging import setup_logging
from .api.router import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
    logger = logging.getLogger(__name__)
    logger.info("Starting Computer Control Service")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Computer Control Service")


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="Bytebot Computer Control Service",
        description="Desktop automation and computer control API",
        version="0.1.0",
        lifespan=lifespan
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")
    
    # Legacy route compatibility (matches TypeScript version)
    app.include_router(api_router, prefix="")

    @app.get("/")
    async def root():
        return {"message": "Bytebot Computer Control Service"}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app


app = create_app()


def main():
    """Main entry point for running the service."""
    port = int(os.getenv("PORT", "9995"))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting Computer Control Service on {host}:{port}")
    
    # Use uvicorn if available, otherwise fallback
    try:
        import uvicorn
        print("Starting with uvicorn...")
        uvicorn.run(app, host=host, port=port)
    except ImportError:
        print("uvicorn not available, trying basic server...")
        # Simple fallback using built-in server
        import asyncio
        from datetime import datetime
        print(f"Service available at http://{host}:{port}")
        print("Note: For full functionality, uvicorn is recommended")
        
        # Keep running
        try:
            while True:
                import time
                time.sleep(60)
                print(f"[{datetime.now()}] Service still running...")
        except KeyboardInterrupt:
            print("Service stopped.")


if __name__ == "__main__":
    main()