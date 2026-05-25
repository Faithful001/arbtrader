from src.core.config import settings
import base64

client_id = settings.EBAY_CLIENT_ID
client_secret = settings.EBAY_CLIENT_SECRET

encoded_string = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

print(encoded_string)