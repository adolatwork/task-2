import asyncio

from typing import Optional
from datetime import datetime

from core.logging import logger
from core.config import settings
from commons.redis_cache import RedisCache
from commons.exchange_rate_client import ExchangeRateClient
from models import Currency, ConversionRequest, ConversionResponse

CACHE_PREFIX = "exchange_rate"


class CurrencyConversionService:
    """
    Currency Conversion Service - Latest Version
    
    Features:
    - Redis caching with configurable TTL
    - Graceful fallback on API errors
    - Batch operations
    - Detailed logging
    - Error handling
    """
    
    def __init__(
        self,
        cache_provider: RedisCache,
        exchange_rate_client: Optional[ExchangeRateClient] = None,
        ttl_seconds: int = None
    ):
        """
        Initialize Currency Conversion Service
        
        Args:
            cache_provider: RedisCache instance
            exchange_rate_client: Exchange rate API client
            ttl_seconds: Cache TTL (default from settings)
        """
        self.cache = cache_provider
        self.client = exchange_rate_client or ExchangeRateClient()
        self.ttl = ttl_seconds or settings.CACHE_TTL_SECONDS
        
        logger.info(
            f"CurrencyConversionService initialized | "
            f"TTL: {self.ttl}s | "
            f"API: {settings.EXCHANGE_RATES_API}"
        )
    
    def _cache_key(self, from_currency: Currency, to_currency: Currency) -> str:
        """
        Generate cache key
        
        Format: exchange_rate:USD:EUR
        """
        return f"{CACHE_PREFIX}:{from_currency.value}:{to_currency.value}"
    
    async def _get_cached_rate(self, key: str) -> Optional[float]:
        """Get rate from cache"""
        try:
            rate = await self.cache.get(key)
            if rate is not None:
                return rate
            return None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None
    
    async def _cache_rate(self, key: str, rate: float) -> None:
        """Cache rate"""
        try:
            await self.cache.set(key, rate, self.ttl)
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
    
    async def convert(self, request: ConversionRequest) -> ConversionResponse:
        """
        Convert currency amount
        
        Process:
        1. Validate request
        2. Check cache
        3. If miss → fetch from API
        4. Cache result
        5. Return response
        
        Args:
            request: ConversionRequest(amount, from_currency, to_currency)
        
        Returns:
            ConversionResponse
        
        Raises:
            ValueError: Validation or conversion error
        """
        try:
            if request.amount <= 0:
                raise ValueError("Amount must be greater than 0")
            
            if request.from_currency == request.to_currency:
                return ConversionResponse(
                    amount=request.amount,
                    from_currency=request.from_currency,
                    to_currency=request.to_currency,
                    converted_amount=request.amount,
                    rate=1.0,
                    timestamp=datetime.now(),
                    cached=False
                )
            
            cache_key = self._cache_key(request.from_currency, request.to_currency)
            rate = await self._get_rate(cache_key, request.from_currency, request.to_currency)
            
            converted_amount = request.amount * rate
            
            return ConversionResponse(
                amount=request.amount,
                from_currency=request.from_currency,
                to_currency=request.to_currency,
                converted_amount=round(converted_amount, 2),
                rate=rate,
                timestamp=datetime.now(),
                cached=await self._was_cached(cache_key, rate)
            )
        
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Conversion error: {str(e)}", exc_info=True)
            raise
    
    async def _get_rate(
        self,
        cache_key: str,
        from_currency: Currency,
        to_currency: Currency
    ) -> float:
        """
        Get exchange rate (with cache)
        
        Args:
            cache_key: Cache key
            from_currency: From currency
            to_currency: To currency
        
        Returns:
            Exchange rate
        
        Raises:
            ValueError: Rate not available
        """
        cached_rate = await self._get_cached_rate(cache_key)
        if cached_rate is not None:
            return cached_rate
        
        try:
            rate = await self.client.get_rate(from_currency, to_currency)
            
            await self._cache_rate(cache_key, rate)
            
            return rate
        
        except Exception as e:
            logger.error(f"API error: {str(e)}")
            
            fallback = await self._get_fallback_rate(from_currency, to_currency)
            if fallback is not None:
                return fallback
            
            raise ValueError(f"Could not get rate for {from_currency.value} → {to_currency.value}")
    
    async def _was_cached(self, cache_key: str, rate: float) -> bool:
        """Check if rate came from cache"""
        cached = await self._get_cached_rate(cache_key)
        return cached == rate
    
    async def _get_fallback_rate(
        self,
        from_currency: Currency,
        to_currency: Currency
    ) -> Optional[float]:
        """
        Fallback rates for API downtime
        
        In production, get from:
        - Database
        - Redis with longer TTL
        - Static config
        """
        
        if from_currency == to_currency:
            return 1.0
        
        fallback_rates = {
            ("USD", "EUR"): 0.92,
            ("USD", "GBP"): 0.79,
            ("USD", "JPY"): 149.50,
            ("USD", "INR"): 83.12,
            ("USD", "AED"): 3.67,
            ("USD", "UZS"): 12755.0,
            
            ("EUR", "USD"): 1.09,
            ("EUR", "GBP"): 0.86,
            ("EUR", "JPY"): 162.50,
            
            ("GBP", "USD"): 1.27,
            ("GBP", "EUR"): 1.16,
            
            ("JPY", "USD"): 0.0067,
            ("JPY", "EUR"): 0.0062,
            
            ("INR", "USD"): 0.012,
            ("INR", "EUR"): 0.011,
            
            ("AED", "USD"): 0.27,
            ("AED", "EUR"): 0.25,
            
            ("UZS", "USD"): 0.000078,
            ("UZS", "EUR"): 0.000072,
        }
        
        key = (from_currency.value, to_currency.value)
        rate = fallback_rates.get(key)
        
        if rate:
            logger.info(f"Fallback rate available: {key} = {rate}")
        else:
            logger.warning(f"No fallback rate for {key}")
        
        return rate
    
    async def convert_batch(
        self,
        requests: list[ConversionRequest]
    ) -> list[ConversionResponse]:
        """
        Convert multiple amounts simultaneously
        
        Args:
            requests: List of ConversionRequest
        
        Returns:
            List of ConversionResponse
        
        Raises:
            ValueError: If no conversions succeed
        """
        logger.info(f"Batch converting {len(requests)} requests")
        
        tasks = [self.convert(req) for req in requests]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful = []
            errors = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Request {i} failed: {str(result)}")
                    errors.append((i, str(result)))
                else:
                    successful.append(result)
            
            if not successful:
                raise ValueError("All batch conversions failed")
            
            if errors:
                logger.warning(f"Batch: {len(successful)} success, {len(errors)} failed")
            else:
                logger.info(f"✓ Batch complete: {len(successful)} conversions")
            
            return successful
        
        except Exception as e:
            logger.error(f"Batch error: {str(e)}")
            raise
    
    async def clear_cache(self) -> None:
        """Clear all cache"""
        try:
            await self.cache.clear()
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            raise
    
    async def get_rate_direct(
        self,
        from_currency: Currency,
        to_currency: Currency,
        use_cache: bool = True
    ) -> float:
        """
        Get rate directly (no response wrapping)
        
        Args:
            from_currency: From currency
            to_currency: To currency
            use_cache: Use cache
        
        Returns:
            Exchange rate
        """
        if not use_cache:
            return await self.client.get_rate(from_currency, to_currency)
        
        cache_key = self._cache_key(from_currency, to_currency)
        return await self._get_rate(cache_key, from_currency, to_currency)
    
    async def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        try:
            stats = await self.cache.get_stats()
            return stats
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {"error": str(e)}
    
    async def health_check(self) -> dict:
        """Health check"""
        try:
            is_connected = await self.cache.is_connected()
            api_available = await self._test_api()
            
            return {
                "status": "healthy" if (is_connected and api_available) else "degraded",
                "cache": "connected" if is_connected else "disconnected",
                "api": "available" if api_available else "unavailable"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _test_api(self) -> bool:
        """Test API connectivity"""
        try:
            await self.client.get_rate(Currency.USD, Currency.EUR)
            return True
        except Exception:
            return False
    
    def get_config(self) -> dict:
        """Get service configuration"""
        return {
            "api_url": settings.EXCHANGE_RATES_API,
            "cache_ttl": self.ttl,
            "api_timeout": settings.EXCHANGE_RATES_TIMEOUT,
            "supported_currencies": [c.value for c in Currency]
        }


async def create_service(
    cache: RedisCache,
    client: Optional[ExchangeRateClient] = None
) -> CurrencyConversionService:
    """
    Create service instance
    
    Args:
        cache: RedisCache instance
        client: Optional ExchangeRateClient
    
    Returns:
        CurrencyConversionService
    """
    if client is None:
        client = ExchangeRateClient()
    
    return CurrencyConversionService(cache, client)
