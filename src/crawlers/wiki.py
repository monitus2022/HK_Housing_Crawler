from .base import BaseCrawler
import requests
from config import housing_crawler_config

class WikiCrawler(BaseCrawler):
    def __init__(self):
        super().__init__()
        self.headers = dict(housing_crawler_config.agency_api.headers)
        
        # Init session to persist headers and cookies
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _set_file_paths(self):
        pass

    def _set_request_urls(self):
        pass