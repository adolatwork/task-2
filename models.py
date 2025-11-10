from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class Currency(str, Enum):
    """Qo'llab-quladigan valyutalar"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    INR = "INR"
    AED = "AED"
    UZS = "UZS"


class ConversionRequest(BaseModel):
    """API so'rovining schema"""
    amount: float = Field(..., gt=0, description="Konvertasiya qilinadigan miqdor")
    from_currency: Currency = Field(..., description="Qaysi valyutadan")
    to_currency: Currency = Field(..., description="Qaysi valyutaga")

    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Miqdor 0 dan katta bo\'lishi kerak')
        return v


class ConversionResponse(BaseModel):
    """API javobining schema"""
    amount: float
    from_currency: Currency
    to_currency: Currency
    converted_amount: float
    rate: float
    timestamp: datetime
    cached: bool = False


class ExchangeRateData(BaseModel):
    """Tashqi API dan olingan exchange rate ma'lumotlari"""
    rates: dict
    base: Currency
    timestamp: datetime

    class Config:
        arbitrary_types_allowed = True
