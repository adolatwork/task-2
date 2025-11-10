from fastapi import FastAPI

from commons.redis_cache import get_redis
from routers import router as exchange_router
from core.lifespan import lifespan
from core.config import settings


app = FastAPI(
    title="Currency Conversion API",
    description="Valyuta konversiya xizmati",
    lifespan=lifespan,
    version="1.0.0"
)


@app.get("/health", tags=["Core"])
async def health_check():
    """Health check"""
    try:
        cache = get_redis()
        is_connected = await cache.is_connected()
        return {
            "status": "healthy" if is_connected else "degraded",
            "redis": "connected" if is_connected else "disconnected",
            "message": "Application is running" + (" without Redis caching" if not is_connected else "")
        }
    except RuntimeError as e:
        # Redis not initialized at all
        return {
            "status": "degraded",
            "redis": "not_initialized",
            "message": "Application is running without Redis"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/endpoints", tags=["Core"])
async def list_routes():
    routers = []
    for route in app.routes[6:]:
        route_info = {
            "path": route.path,
            "name": route.name,
            "description": route.description,
            "methods": route.methods
        }
        routers.append(route_info)
    return routers


app.include_router(exchange_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.SVC_HOST,
        port=settings.SVC_PORT,
        reload=settings.SVC_RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )
