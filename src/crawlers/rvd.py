import requests
from ..logger import housing_logger

class RvdCrawler:
    def __init__(self):
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        }
        # Init session to persist headers and cookies
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _make_request(
        self,
        url: str,
        params: dict = None,
    ):
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            housing_logger.error(f"Error making request to {url}: {str(e)}")
            return None
