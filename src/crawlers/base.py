from config import housing_crawler_config
from logger import housing_logger
import pathlib
from typing import Optional
import requests
from abc import ABC, abstractmethod

class BaseCrawler(ABC):
    def __init__(self):
        self.working_dir = pathlib.Path(__file__).parent.parent.parent.resolve()
        # Set up data storage paths
        self.data_storage_path = self.working_dir / housing_crawler_config.storage.root_path
        self.files_path = self.data_storage_path / housing_crawler_config.storage.files.path
        for path in [self.data_storage_path, self.files_path]:
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    housing_logger.error(f"Failed to create directory {path}: {e}")
        self.session: Optional[requests.Session] = None

    def _make_request(self, url: str, params: dict = None) -> Optional[requests.Response]:
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            housing_logger.error(f"Error making request to {url}: {str(e)}")
            return None
    
    @abstractmethod
    def _set_file_paths(self):
        pass

    @abstractmethod
    def _set_request_urls(self):
        pass