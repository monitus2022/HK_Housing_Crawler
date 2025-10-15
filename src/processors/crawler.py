from .base import BaseProcessor
from config import housing_crawler_config
from logger import housing_logger
import pandas as pd
from utils import flatten_dict
from schema.transactions import (
    BUILDING_INFO_TABLE_SCHEMA,
    UNIT_INFO_TABLE_SCHEMA,
    UNIT_FEATURES_TABLE_SCHEMA,
    TRANSACTIONS_TABLE_SCHEMA,
)


class CrawlerProcessor(BaseProcessor):
    """
    Special processor to handle crawling tasks on the fly.
    This processor is not part of the main pipeline and is used for specific crawling tasks.
    """

    def __init__(self):
        super().__init__()
        self.sqlite_path = (
            self.database_path
            / housing_crawler_config.storage.files.outputs.transactions_db
        )
        self.connect_db(db_type="sqlite")
        self.set_table_names()
        self.set_table_schemas()
        self.set_data_cache()

    def set_table_names(self) -> None:
        # TODO: config
        self.building_info_table = "building_info"
        self.unit_info_table = "unit_info"
        self.unit_features_table = "unit_features"
        self.transactions_table = "transactions"

    def set_table_schemas(self) -> None:
        self.table_schemas = {
            self.building_info_table: BUILDING_INFO_TABLE_SCHEMA,
            self.unit_info_table: UNIT_INFO_TABLE_SCHEMA,
            self.unit_features_table: UNIT_FEATURES_TABLE_SCHEMA,
            self.transactions_table: TRANSACTIONS_TABLE_SCHEMA,
        }

    def set_data_cache(self) -> None:
        self.data_cache = {
            self.building_info_table: [],
            self.unit_info_table: [],
            self.unit_features_table: [],
            self.transactions_table: [],
        }

    def get_data_cache(self) -> dict:
        return self.data_cache

    def update_tables(self) -> None:
        for table_name, data in self.data_cache.items():
            if data:
                # Convert cache data to DataFrame
                data = pd.DataFrame(data)
                # Insert data into the database
                self.save_dataframe_to_db(
                    data,
                    db_type="sqlite",
                    table_name=table_name,
                    dtypes=self.table_schemas.get(table_name),
                    if_exists="append",
                )
                housing_logger.info(
                    f"Inserted {len(data)} records into {table_name} table"
                )
            else:
                housing_logger.info(f"No new records to insert into {table_name} table")
        # Clear cache after updating database
        self.set_data_cache()  

    def process_single_building(self, data: dict) -> None:
        """
        Given building transaction data, split and insert into 2 data:
        1. Building Info
        2. Unit data (which will be further split)
        """
        if not data:
            return None
        # Process building info
        building_info = flatten_dict(
            data, primary_key="building", sep="_", key_exclude=["bldg_type"]
        )
        building_info = self._check_and_convert_types_by_schema(
            building_info, BUILDING_INFO_TABLE_SCHEMA
        )
        self.data_cache[self.building_info_table].append(building_info)

        # Process each unit in the building
        for unit in data.get("data", []):
            self._process_single_unit(
                data["building_id"], data["building_name"], unit
            )

    def _process_single_unit(self, building_id: str, building_name: str, data: dict) -> None:
        """
        Given unit transaction data, split and insert into 3 dict:
        1. Unit Info
        2. Unit Features
        3. Transaction Info
        """
        if not data:
            return None

        # Add additional fields for unit info
        data["building_id"] = building_id
        data["building_name"] = building_name
        # Get extra unit info fields from the first transaction
        transaction_extra_info = {
            k: v
            for k, v in data.get("transactions", [{}])[0].items()
            if k in UNIT_INFO_TABLE_SCHEMA
        }
        data.update(transaction_extra_info)

        unit_info = self._check_and_convert_types_by_schema(
            data, UNIT_INFO_TABLE_SCHEMA
        )
        self.data_cache[self.unit_info_table].append(unit_info)

        # Process unit features
        unit_features_list = data.get("features", [])
        if unit_features_list:
            for feature in unit_features_list:
                feature["unit_id"] = data["unit_id"]
            unit_features = self._check_and_convert_types_by_schema(
                unit_features_list, UNIT_FEATURES_TABLE_SCHEMA
            )
            self.data_cache[self.unit_features_table].extend(unit_features)

        # Process transactions for the unit
        self._process_single_unit_transactions(
            data["unit_id"], data.get("transactions", [])
        )

    def _process_single_unit_transactions(self, unit_id: str, data: list[dict]) -> None:
        """
        Given a list of unit transactions, process and save into cache.
        """
        if not data:
            return None
        for tx in data:
            # Rename id to transaction_id
            tx["transaction_id"] = tx.pop("id", None)
            tx = self._check_and_convert_types_by_schema(tx, TRANSACTIONS_TABLE_SCHEMA)

            tx["unit_id"] = unit_id
            self.data_cache[self.transactions_table].append(tx)

    def get_existing_estate_ids(self) -> set:
        """
        Retrieve existing estate IDs from the SQLite database to avoid redundant crawling.
        """
        query = f"SELECT DISTINCT estate_id FROM {self.building_info_table}"
        existing_estate_ids = set()
        result = self.execute_query(query)
        if result:
            existing_estate_ids = {row[0] for row in result}
        return existing_estate_ids
