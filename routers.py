from fastapi import HTTPException, Depends

from core.logging import logger
from core.lifespan import get_service
from commons.redis_cache import get_redis
from core.base_router import get_base_router
from commons.service import CurrencyConversionService
from models import ConversionRequest, ConversionResponse, Currency


router = get_base_router(app_prefix="/exchange", tags=["Exchange"])


@router.post(
    "/convert",
    response_model=ConversionResponse,
    summary="Convert currency",
    description="Convert amount from one currency to another using real-time exchange rates"
)
async def convert(
    request: ConversionRequest,
    service: CurrencyConversionService = Depends(get_service)
) -> ConversionResponse:
    """
    Convert currency amount from one currency to another.

    - amount: Amount to convert (must be positive)
    - from_currency: Source currency code (e.g., USD, EUR, GBP)
    - to_currency: Target currency code

    Returns the converted amount with the exchange rate and timestamp.
    Results are cached for 30 minutes for better performance.
    """
    try:
        return await service.convert(request)
    
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Conversion error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.post(
    "/batch-convert",
    response_model=list[ConversionResponse],
    summary="Batch convert currencies",
    description="Convert multiple currency pairs in a single request"
)
async def batch_convert(
    requests: list[ConversionRequest],
    service: CurrencyConversionService = Depends(get_service)
) -> list[ConversionResponse]:
    """
    Batch convert multiple currency amounts.

    Accepts a list of conversion requests and processes them concurrently.
    Returns only successful conversions.
    """
    try:
        return await service.convert_batch(requests)
    
    except Exception as e:
        logger.error(f"Batch error: {str(e)}")
        raise HTTPException(status_code=503, detail="Batch conversion failed")


@router.get(
    "/currencies",
    summary="Get supported currencies",
    description="Returns a list of all supported currency codes"
)
async def get_currencies():
    """
    Get list of all supported currency codes.

    Returns all available currencies that can be used for conversion.
    """
    return {"currencies": [c.value for c in Currency]}


@router.get(
    "/cache/stats",
    summary="Get cache statistics",
    description="Returns cache performance metrics including hit rate and total requests"
)
async def cache_stats():
    """
    Get Redis cache statistics.

    Returns metrics about cache performance:
    - status: Redis connection status
    - used_memory: Memory used by Redis
    - connected_clients: Number of connected clients
    - total_commands: Total commands processed
    - total_keys: Total number of keys in database
    - cached_rates: Number of cached exchange rates
    """
    try:
        cache = get_redis()
        stats = await cache.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/cache",
    summary="Clear cache",
    description="Clears all cached exchange rates and statistics"
)
async def clear_cache():
    """
    Clear entire cache.

    Removes all cached exchange rates and resets cache statistics.
    Next conversion requests will fetch fresh data from the API.
    """
    try:
        cache = get_redis()
        await cache.clear()
        return {"message": "Cache cleared"}
    except Exception as e:
        logger.error(f"Cache clear error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")
