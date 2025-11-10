from fastapi import FastAPI
from contextlib import asynccontextmanager

from core.logging import logger
from commons.redis_cache import init_redis, shutdown_redis
from commons.service import CurrencyConversionService
from commons.exchange_rate_client import ExchangeRateClient


_service: CurrencyConversionService = None

def get_service() -> CurrencyConversionService:
    """Get conversion service"""
    if _service is None:
        raise RuntimeError("Service not initialized")
    return _service


async def startup(app: FastAPI) -> None:
    cache = await init_redis()
    client = ExchangeRateClient()
    global _service
    _service = CurrencyConversionService(cache, client)
    logger.info("Application started")


async def shutdown(app: FastAPI) -> None:
    await shutdown_redis()

    logger.info("Application shutting down")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup(app)
    try:
        yield
    finally:
        await shutdown(app)
