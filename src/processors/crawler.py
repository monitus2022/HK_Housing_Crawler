from .base import BaseProcessor
from config import housing_crawler_config
from logger import housing_logger
import pandas as pd

class CrawlerProcessor(BaseProcessor):
    """
    Special processor to handle crawling tasks on the fly.
    This processor is not part of the main pipeline and is used for specific crawling tasks.
    """
    def __init__(self):
        super().__init__()
        self.sqlite_path = self.database_path / housing_crawler_config.storage.files.outputs.transactions_db
        self.connect_db(db_type="sqlite")

    def create_building_info_table(self) -> None:
        pass

    def create_unit_info_table(self) -> None:
        pass

    def create_transactions_table(self) -> None:
        pass

    def insert_building_info(self, data: pd.DataFrame) -> None:
        pass

    def insert_unit_info(self, data: pd.DataFrame) -> None:
        pass

    def insert_transactions(self, data: pd.DataFrame) -> None:
        pass

    def _get_existing_estate_ids(self) -> set:
        """
        Retrieve existing estate IDs from the SQLite database to avoid redundant crawling.
        """
        query = "SELECT DISTINCT estate_id FROM transactions"
        existing_estate_ids = set()
        result = self.execute_query(query)
        if result:
            existing_estate_ids = {row[0] for row in result}
        return existing_estate_ids
