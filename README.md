# 💱 Currency Conversion API

**Production-ready FastAPI application with Redis caching**

---

## 🎯 Overview

Modern valyuta konversiya API - **Redis caching** bilan optimized. Bir vaqtda ko'p currency conversion, batch operations, health checks, cache management.

### ✨ Key Features

- ✅ **Real-time Currency Conversion** - Live exchange rates
- ✅ **Redis Caching** - 30-minute TTL, ~80-90% hit rate
- ✅ **Batch Operations** - Convert multiple currencies simultaneously
- ✅ **Fallback Rates** - Graceful degradation on API errors
- ✅ **Health Monitoring** - Complete system diagnostics
- ✅ **Comprehensive Logging** - Debug-friendly output
- ✅ **Type Safety** - Full type hints
- ✅ **Docker Support** - Ready for containerization
- ✅ **Production Ready** - Error handling, validation, security

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Python 3.10 or higher
python --version

# Docker (for Redis)
docker --version
```

### 2. Clone & Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

### 3. Get API Key

Go to **https://exchangeratesapi.io/**

1. Click "Get Free API"
2. Sign up with email
3. Verify email
4. Copy API key
5. Paste in `.env`:

```env
EXCHANGE_RATES_API_KEY="your_api_key_here"
```

### 4. Start Redis

```bash
# Terminal 1
docker run -p 6379:6379 redis:7-alpine
```

### 5. Run Application

```bash
# Terminal 2
python main_latest.py
```

### 6. Test

```bash
# Health check
curl http://localhost:8000/health

# Convert currency
curl -X POST http://localhost:8000/convert \
  -H "Content-Type: application/json" \
  -d '{"amount": 100, "from_currency": "USD", "to_currency": "EUR"}'

# API docs (open in browser)
http://localhost:8000/docs
```

---

## 🔧 Installation

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd currency-conversion-api
```

### Step 2: Create Virtual Environment

```bash
# Create
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Setup Configuration

```bash
# Copy template
cp .env.example .env

# Edit with your API key
nano .env
```

### Step 5: Start Redis

```bash
# Docker
docker run -p 6379:6379 redis:7-alpine
```

### Step 6: Run Application

```bash
python main_latest.py
```

---

## ⚙️ Configuration

### Environment Variables

```env
# Service
SVC_NAME="Currency Conversion API"
SVC_HOST="0.0.0.0"
SVC_PORT=8000
SVC_DEBUG=false
SVC_RELOAD=false

# Logging
LOG_LEVEL="INFO"

# Redis
REDIS_HOST="localhost"
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=""
REDIS_TIMEOUT=5

# Cache
CACHE_TTL_SECONDS=1800

# API
EXCHANGE_RATES_API="https://api.exchangeratesapi.io/latest"
EXCHANGE_RATES_API_KEY="YOUR_KEY_HERE"
EXCHANGE_RATES_TIMEOUT=10

# Security
SECRET_KEY="your-secret-key"
```

---

## 💻 Usage

### Single Conversion

```python
from models import ConversionRequest, Currency
from service_latest import CurrencyConversionService
from cache_redis_only import init_redis

cache = await init_redis()
service = CurrencyConversionService(cache)

request = ConversionRequest(
    amount=100,
    from_currency=Currency.USD,
    to_currency=Currency.EUR
)

response = await service.convert(request)
print(f"100 USD = {response.converted_amount} EUR")
```

### Batch Conversion

```python
requests = [
    ConversionRequest(100, Currency.USD, Currency.EUR),
    ConversionRequest(50, Currency.EUR, Currency.GBP),
]

responses = await service.convert_batch(requests)
```

### Cache Management

```python
# Stats
stats = await service.get_cache_stats()
print(f"Memory: {stats['used_memory']}")

# Clear cache
await service.clear_cache()

# Health check
health = await service.health_check()
```

---

## 🔌 API Endpoints

### Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "cache": "connected",
  "api": "available"
}
```

### Convert Currency

```bash
POST /convert
```

Request:
```json
{
  "amount": 100,
  "from_currency": "USD",
  "to_currency": "EUR"
}
```

Response:
```json
{
  "amount": 100,
  "from_currency": "USD",
  "to_currency": "EUR",
  "converted_amount": 92.50,
  "rate": 0.925,
  "timestamp": "2024-01-15T10:30:00",
  "cached": false
}
```

### Batch Convert

```bash
POST /batch-convert
```

Request:
```json
[
  {"amount": 100, "from_currency": "USD", "to_currency": "EUR"},
  {"amount": 50, "from_currency": "EUR", "to_currency": "GBP"}
]
```

### Get Currencies

```bash
GET /currencies
```

Response:
```json
{
  "currencies": ["USD", "EUR", "GBP", "JPY", "INR", "AED", "UZS"]
}
```

### Cache Statistics

```bash
GET /cache/stats
```

Response:
```json
{
  "status": "connected",
  "used_memory": "1.26M",
  "connected_clients": 1,
  "total_commands": 71
}
```

### Clear Cache

```bash
DELETE /cache
```

### Service Config

```bash
GET /config
```
