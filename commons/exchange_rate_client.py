import httpx

from enum import Enum
from typing import Optional
from datetime import datetime

from core.logging import logger
from models import Currency, ExchangeRateData


class ExchangeRateProvider(str, Enum):
    """Qo'llab-quladigan valyuta kursi provayderlari"""
    EXCHANGE_RATES_API = "exchangeratesapi.io"
    FIXER = "fixer.io"


class ExchangeRateClient:
    """
    Tashqi API bilan ishlash
    
    Settings orqali URL va API key-ni oladi
    """
    
    def __init__(
        self,
        provider: ExchangeRateProvider = ExchangeRateProvider.EXCHANGE_RATES_API,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 10
    ):
        """
        Initialize Exchange Rate Client
        
        Args:
            provider: API provider tanlovi
            api_url: API URL (settings dan olinadi agar None bo'lsa)
            api_key: API key (settings dan olinadi agar None bo'lsa)
            timeout: Request timeout sekundlarda
        """
        self.provider = provider
        self.timeout = timeout

        if api_url is None:
            from core.config import settings
            self.api_url = str(settings.EXCHANGE_RATES_API)
        else:
            self.api_url = api_url

        if api_key is None:
            from core.config import settings
            self.api_key = settings.EXCHANGE_RATES_API_KEY
        else:
            self.api_key = api_key
        
        logger.info(f"ExchangeRateClient initialized: {self.provider.value}")
    
    async def get_exchange_rates(
        self,
        base_currency: Currency,
        target_currencies: Optional[list[Currency]] = None
    ) -> ExchangeRateData:
        """
        Valyuta kursini API dan olish
        
        Args:
            base_currency: Asosiy valyuta (USD, EUR, va h.k.)
            target_currencies: Maqsadli valyutalar (None bo'lsa barchasi)
        
        Returns:
            ExchangeRateData: Kurs ma'lumotlari
        
        Raises:
            httpx.RequestError: Tarmoq xatosi
            ValueError: API xatosi
        """
        try:
            params = {}

            if self.api_key:
                params["access_key"] = self.api_key
                if base_currency != Currency.EUR:
                    logger.warning(
                        f"Free tier only supports EUR base, but {base_currency.value} was requested. "
                        f"Using EUR base."
                    )
            else:
                params["base"] = base_currency.value

            if target_currencies:
                params["symbols"] = ",".join([c.value for c in target_currencies])

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.api_url, params=params)
                response.raise_for_status()
                
                data = response.json()

                if not data.get("success", True) and "error" in data:
                    error_message = data.get("error", {}).get("info", "Unknown error")
                    raise ValueError(f"API xatosi: {error_message}")
                
                rates = data.get("rates", {})
                if not rates:
                    logger.warning(f"No rates returned for base currency")

                actual_base = Currency.EUR if self.api_key else base_currency

                logger.info(f"Successfully fetched rates (base: {actual_base.value})")

                return ExchangeRateData(
                    rates=rates,
                    base=actual_base,
                    timestamp=datetime.now()
                )
        
        except httpx.RequestError as e:
            logger.error(f"API so'rov xatosi ({self.provider.value}): {str(e)}")
            raise
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP xatosi {e.response.status_code}: {str(e)}")
            raise
        
        except ValueError as e:
            logger.error(f"API validation xatosi: {str(e)}")
            raise
        
        except Exception as e:
            logger.error(f"Noma'lum xato: {str(e)}", exc_info=True)
            raise
    
    async def get_rate(
        self,
        from_currency: Currency,
        to_currency: Currency
    ) -> float:
        """
        Bitta kursni olish

        Args:
            from_currency: Qaysi valyutadan
            to_currency: Qaysi valyutaga

        Returns:
            float: Konversiya koeffitsiyenti (1.0 agar bir xil valyuta bo'lsa)

        Raises:
            ValueError: Kurs topilmasa yoki API xatosi
        """
        if from_currency == to_currency:
            return 1.0

        try:
            if from_currency == Currency.EUR:
                exchange_data = await self.get_exchange_rates(
                    Currency.EUR,
                    [to_currency]
                )
                rate = exchange_data.rates.get(to_currency.value)

            elif to_currency == Currency.EUR:
                exchange_data = await self.get_exchange_rates(
                    Currency.EUR,
                    [from_currency]
                )
                eur_to_from = exchange_data.rates.get(from_currency.value)
                if eur_to_from:
                    rate = 1.0 / eur_to_from
                else:
                    rate = None

            else:
                exchange_data = await self.get_exchange_rates(
                    Currency.EUR,
                    [from_currency, to_currency]
                )

                eur_to_from = exchange_data.rates.get(from_currency.value)
                eur_to_to = exchange_data.rates.get(to_currency.value)

                if eur_to_from and eur_to_to:
                    rate = eur_to_to / eur_to_from
                else:
                    rate = None

            if rate is None:
                error_msg = (
                    f"Kurs topilmadi: {from_currency.value} -> {to_currency.value}. "
                    f"Available rates: {list(exchange_data.rates.keys())}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)

            logger.debug(f"Rate: {from_currency.value} -> {to_currency.value} = {rate}")
            return float(rate)

        except Exception as e:
            logger.error(f"Kurs olishda xato: {str(e)}")
            raise
    
    async def get_multiple_rates(
        self,
        from_currency: Currency,
        to_currencies: list[Currency]
    ) -> dict[str, float]:
        """
        Bir nechta kursni bir vaqtda olish (optimized)

        Args:
            from_currency: Qaysi valyutadan
            to_currencies: Qaysi valyutalarga

        Returns:
            dict: {to_currency: rate} mapping

        Raises:
            ValueError: API xatosi
        """
        try:
            logger.info(
                f"Getting multiple rates: {from_currency.value} -> "
                f"{[c.value for c in to_currencies]}"
            )

            all_currencies = [from_currency] + to_currencies
            currencies_to_fetch = list(set([c for c in all_currencies if c != Currency.EUR]))

            exchange_data = await self.get_exchange_rates(
                Currency.EUR,
                currencies_to_fetch if currencies_to_fetch else None
            )

            result = {}
            for to_curr in to_currencies:
                if from_currency == to_curr:
                    result[to_curr.value] = 1.0
                elif from_currency == Currency.EUR:
                    rate = exchange_data.rates.get(to_curr.value)
                    if rate:
                        result[to_curr.value] = float(rate)
                elif to_curr == Currency.EUR:
                    eur_to_from = exchange_data.rates.get(from_currency.value)
                    if eur_to_from:
                        result[to_curr.value] = float(1.0 / eur_to_from)
                else:
                    eur_to_from = exchange_data.rates.get(from_currency.value)
                    eur_to_to = exchange_data.rates.get(to_curr.value)
                    if eur_to_from and eur_to_to:
                        result[to_curr.value] = float(eur_to_to / eur_to_from)

            if not result:
                raise ValueError(
                    f"Hech bir kurs topilmadi: {from_currency.value} -> "
                    f"{[c.value for c in to_currencies]}"
                )

            return result

        except Exception as e:
            logger.error(f"Multiple rates olishda xato: {str(e)}")
            raise


async def get_exchange_rate(
    from_currency: Currency,
    to_currency: Currency,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> float:
    """
    Utility function - qulay qo'shilishi uchun
    """
    client = ExchangeRateClient(api_url=api_url, api_key=api_key)
    return await client.get_rate(from_currency, to_currency)
