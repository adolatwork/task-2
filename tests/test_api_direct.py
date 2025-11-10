import asyncio
from commons.exchange_rate_client import ExchangeRateClient
from models import Currency


async def test_api():
    """Test API directly"""
    client = ExchangeRateClient()

    print("Testing API directly...")
    print("-" * 50)

    try:
        # Test USD -> EUR
        print("\n1. Testing USD -> EUR")
        rate = await client.get_rate(Currency.USD, Currency.EUR)
        print(f"   Rate: {rate}")

        # Test USD -> UZS
        print("\n2. Testing USD -> UZS")
        rate = await client.get_rate(Currency.USD, Currency.UZS)
        print(f"   Rate: {rate}")

        # Test EUR -> USD
        print("\n3. Testing EUR -> USD")
        rate = await client.get_rate(Currency.EUR, Currency.USD)
        print(f"   Rate: {rate}")

        # Test GBP -> JPY
        print("\n4. Testing GBP -> JPY")
        rate = await client.get_rate(Currency.GBP, Currency.JPY)
        print(f"   Rate: {rate}")

    except Exception as e:
        print(f"Error: {e}")

    print("-" * 50)


if __name__ == "__main__":
    asyncio.run(test_api())
