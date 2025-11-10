import asyncio
import httpx


async def test_conversion():
    """Test USD to UZS conversion"""
    base_url = "http://localhost:8000/api/v1/exchange"

    print("Testing USD -> UZS conversion...")
    print("-" * 50)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/convert",
            json={
                "amount": 100,
                "from_currency": "USD",
                "to_currency": "UZS"
            }
        )

        if response.status_code == 200:
            data = response.json()
            print("✓ Conversion successful!")
            print(f"  Amount: {data['amount']} {data['from_currency']}")
            print(f"  Converted: {data['converted_amount']} {data['to_currency']}")
            print(f"  Rate: {data['rate']}")
            print(f"  Cached: {data['cached']}")
            print(f"  Timestamp: {data['timestamp']}")
        else:
            print(f"✗ Conversion failed!")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.text}")

    print("-" * 50)
    print("\nTesting EUR -> USD conversion...")
    print("-" * 50)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/convert",
            json={
                "amount": 100,
                "from_currency": "EUR",
                "to_currency": "USD"
            }
        )

        if response.status_code == 200:
            data = response.json()
            print("✓ Conversion successful!")
            print(f"  Amount: {data['amount']} {data['from_currency']}")
            print(f"  Converted: {data['converted_amount']} {data['to_currency']}")
            print(f"  Rate: {data['rate']}")
        else:
            print(f"✗ Conversion failed!")
            print(f"  Status: {response.status_code}")


if __name__ == "__main__":
    asyncio.run(test_conversion())
