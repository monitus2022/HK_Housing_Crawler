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
                housing_logger.debug(data.head(3))
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

    def process_single_building(self, data: dict[str, dict | list]) -> None:
        """
        Input:
            building: contains building info
            data: unit info and list of transactions

        Given building transaction data, split and insert into 2 data:
        1. Building Info
        2. Unit data (which will be further split)
        Refer to schema/examples/transactions.json for example body
        """
        if not data:
            return None
        # Process building info without data
        building_info = flatten_dict(
            data.get("building", {}), primary_key="building", sep="_", key_exclude=["bldg_type"]
        )
        building_info = self._check_and_convert_types_by_schema(
            building_info, BUILDING_INFO_TABLE_SCHEMA
        )
        building_id = building_info.get('building_id')
        building_name = building_info.get('building_name')
        self.data_cache[self.building_info_table].append(building_info)

        # Process each unit in the building
        units = data.get("data", [])
        for unit in units:
            self._process_single_unit(building_id, building_name, unit)

        # housing_logger.info(f"Finished processing building {building_id} - {building_name}")

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
        unit_id = data.get("unit_id")

        # Get extra unit info fields from the first transaction, if any
        transactions = data.get("transactions", [])
        if transactions:
            first_transaction = transactions[0]
            transaction_extra_info = {
                k: v
                for k, v in first_transaction.items()
                if k in UNIT_INFO_TABLE_SCHEMA
            }
            data.update(transaction_extra_info)

            # Get feature list
            unit_features_list = first_transaction.get("feature", [])
            if unit_features_list is not None:
                unit_features_list = [
                    {f"feature_{k}": v for k, v in feature.items()}
                    for feature in unit_features_list
                ]
                for feature in unit_features_list:
                    # Adding prefix
                    feature["unit_id"] = unit_id
                    feature = self._check_and_convert_types_by_schema(
                        feature, UNIT_FEATURES_TABLE_SCHEMA
            )
                # Save Unit Feature to cache
                self.data_cache[self.unit_features_table].extend(unit_features_list)

            # Process transactions for the unit
            self._process_single_unit_transactions(
                unit_id, data.get("transactions", [])
            )

        # Check unit info and save to cache
        unit_info = self._check_and_convert_types_by_schema(
            data, UNIT_INFO_TABLE_SCHEMA
        )
        self.data_cache[self.unit_info_table].append(unit_info)


    def _process_single_unit_transactions(self, unit_id: str, data: list[dict]) -> None:
        """
        Given a list of unit transactions, process and save into cache.
        """
        if not data:
            return None
        for tx in data:
            # Rename id to transaction_id
            tx["transaction_id"] = tx.get("id", "")
            tx["unit_id"] = unit_id
            tx = self._check_and_convert_types_by_schema(tx, TRANSACTIONS_TABLE_SCHEMA)
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
