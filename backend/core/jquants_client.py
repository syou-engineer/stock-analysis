import os
import requests
from dotenv import load_dotenv

load_dotenv()

class JQuantsClient:
    def __init__(self):
        # V2 APIではエンドポイントのルートが異なります
        self.base_url = "https://api.jquants.com/v2"
        # .env から APIキー を取得 (JQUANTS_API_KEY を設定してください)
        self.api_key = os.getenv("JQUANTS_API_KEY")
        
        if not self.api_key:
            raise ValueError("JQUANTS_API_KEY is not set in .env file")

        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def get(self, endpoint: str, params: dict = None) -> dict:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"[JQuants API Error] {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            raise