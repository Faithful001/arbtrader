import asyncio
import httpx
import time

async def fetch_card(client, card_id):
    url = f"https://api.tcgdex.net/v2/en/cards/{card_id}"
    try:
        resp = await client.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        pass
    return None

async def main():
    print("Fetching list of Crown Zenith cards...")
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://api.tcgdex.net/v2/en/sets/swsh12.5")
        cards = resp.json().get("cards", [])[:20] # Test first 20 cards
        print(f"Starting parallel fetch of {len(cards)} cards...")
        start_time = time.time()
        tasks = [fetch_card(client, c['id']) for c in cards]
        results = await asyncio.gather(*tasks)
        valid_results = [r for r in results if r]
        print(f"Fetched {len(valid_results)} cards in {time.time() - start_time:.2f} seconds!")
        if valid_results:
            print("Sample rarity:", valid_results[0].get("rarity"))

if __name__ == "__main__":
    asyncio.run(main())
