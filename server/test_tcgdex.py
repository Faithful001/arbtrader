import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    print("Fetching single card details from TCGdex...")
    url = "https://api.tcgdex.net/v2/en/cards/swsh12.5-001"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
        print("Status code:", response.status)
        data = json.loads(response.read().decode())
        print("Card details keys:", data.keys())
        print("Rarity:", data.get("rarity"))
        print("Types:", data.get("types"))
        print("HP:", data.get("hp"))
        print("Image high res:", f"{data.get('image')}/high.png")
except Exception as e:
    print("Failed:", str(e))
