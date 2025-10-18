from .base import BaseProcessor
import pandas as pd
import json
from schema import ESTATE_INFO_SCHEMA
from config import housing_crawler_config
from logger import housing_logger
from utils import flatten_dict, keep_only_numbers, convert_datetime
from typing import Union


class AgencyProcessor(BaseProcessor):
    def __init__(self):
        super().__init__()
        self.transaction_file_path = (
            self.data_storage_path / housing_crawler_config.transactions_json
        )
        self.estate_info_json_path = (
            self.data_storage_path / housing_crawler_config.estate_info_json
        )
        self.building_info_json_path = (
            self.data_storage_path / housing_crawler_config.building_info_json
        )
        self.unit_transactions_json_path = (
            self.data_storage_path / housing_crawler_config.unit_transactions_json
        )
        self._legacy_transaction_file_path = (
            self.data_storage_path / housing_crawler_config.legacy_transaction_csv
        )

    def process_transaction_json(self) -> None:
        with open(self.transaction_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        processed_data = [
            self._process_single_building(transaction) for transaction in data
        ]
        building_info = [item["building_info"] for item in processed_data]
        unit_transactions = []
        for item in processed_data:
            unit_transactions.extend(item["unit_transactions"])

        with open(
            self.data_storage_path / "building_info.json", "w", encoding="utf-8"
        ) as file:
            json.dump(building_info, file, ensure_ascii=False, indent=2)

        with open(
            self.data_storage_path / "unit_transactions.json", "w", encoding="utf-8"
        ) as file:
            json.dump(unit_transactions, file, ensure_ascii=False, indent=2)

    def _process_single_building(
        self, transaction: dict
    ) -> dict[str, Union[dict, list]]:
        """
        Split building transaction data into 2 subset with building_id as future foreign key
        For original transaction data structure, please refer to transaction.json in examples
        1. building info
        2. unit info with transaction info per unit
        """
        output = {"building_info": {}, "unit_transactions": []}
        # Process building info
        building_info = transaction.get("building", {})
        if not building_info:
            housing_logger.warning("No building info found in transaction data.")
            return output
        output["building_info"] = flatten_dict(
            building_info, primary_key="building", sep="_", key_exclude=["bldg_type"]
        )
        building_id = building_info.get("id", None)

        # Process unit transactions
        units = transaction.get("data", [])
        if not isinstance(units, list):
            housing_logger.error("Units data is not a list.")
            raise ValueError("Units data is not a list.")
        for unit in units:
            if not isinstance(unit, dict):
                housing_logger.error("Unit data is not a dict.")
                raise ValueError("Unit data is not a dict.")
            unit_transactions = self._process_single_unit_transactions(
                unit_data=unit, building_id=building_id
            )
            output["unit_transactions"].extend(unit_transactions)
        return output

    def _process_single_unit_transactions(
        self, unit_data: dict, building_id: str
    ) -> list[dict[str, any]]:
        """
        Process unit transactions, adding building_id as foreign key
        """

        transactions = unit_data.get("transactions", [])
        if not isinstance(transactions, list):
            housing_logger.error("Transactions is not a list.")
            raise ValueError("Transactions is not a list.")

        output = []

        unit_info = {
            k: v for k, v in unit_data.items() if k not in ["unit_type", "transactions"]
        }
        unit_info.update({"building_id": building_id})
        if transactions is None:
            output.append(unit_info)
            return output

        # Process each transaction
        for transaction in transactions:
            if not isinstance(transaction, dict):
                housing_logger.error("Transaction is not a dict.")
                raise ValueError("Transaction is not a dict.")
            processed_transaction = self._process_single_transaction(transaction)
            output.append(processed_transaction)
        return output

    def _process_single_transaction(self, transaction: dict) -> dict[str, any]:
        """
        Process a single transaction record from single unit
        For list of features, break down to feature_1, feature_2, ...
        """
        transaction_keys_exclude = [
            "id",
            "tx_type",
            "area",
            "net_area",
            "mkt_type",
            "url_desc",
        ]

        output = {}
        for k, v in transaction.items():
            if k in transaction_keys_exclude:
                continue
            elif isinstance(v, dict):
                v = flatten_dict(
                    v, primary_key=k, sep="_", key_exclude=transaction_keys_exclude
                )
                output.update(v)
            elif isinstance(v, list):
                for idx, item in enumerate(v):
                    output[f"{k}_{idx+1}"] = item
            else:
                output[k] = v
        return output

    def process_and_save_estate_info(self, db_type: str = "duckdb") -> None:
        """
        Process estate info JSON, save processed data to file and database.
        Uses BaseProcessor database logic for saving.
        """
        with open(self.estate_info_json_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        processed_data = [self._process_single_estate_info(info) for info in data]
        with open(self.processed_estate_info_json_path, "w", encoding="utf-8") as file:
            json.dump(processed_data, file, ensure_ascii=False, indent=2)

        df = pd.DataFrame(processed_data)

        # Save to db
        self.save_df_to_db(
            df=df,
            table_name=housing_crawler_config.estate_info_table_name,
            schema=ESTATE_INFO_SCHEMA,
            db_type=db_type,
        )
        housing_logger.info(
            f"Saved processed estate info to table: {housing_crawler_config.estate_info_table_name} in {db_type} database."
        )

    def _process_single_estate_info(self, info) -> dict:
        output_dict = {}
        for key, value in info.items():
            if (
                "url" in key
                or "combined" in key
                or key in ["icon", "hos", "show", "photo"]
            ):
                continue
            elif key == "property_stat":
                output_dict.update(value)
            elif key == "market_stat":
                if "yearly" in value:
                    yearly_info = value["yearly"]
                    yearly_info = {f"yearly_{k}": v for k, v in yearly_info.items()}
                    output_dict.update(yearly_info)
                    value.pop("yearly")
                output_dict.update({f"recent_{k}": v for k, v in value.items()})
            elif type(value) is dict:
                output_dict.update(
                    {
                        f"{key}_{sub_key}": sub_value
                        for sub_key, sub_value in value.items()
                    }
                )
            else:
                output_dict[key] = value
        return output_dict

    def get_estate_ids_from_processed_estate_info(self) -> list[str]:
        with open(self.processed_estate_info_json_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return [item["id"] for item in data if "id" in item]

    def _legacy_process_transaction_table(self) -> pd.DataFrame:
        """
        Process the transaction table CSV file.
        Cleans and converts data types for specific columns.
        Only applies to the legacy CSV format.
        """
        int_columns = [
            "Area(Saleable)",
            "Area(Gross)",
            "Price(m)",
            "Price/ft2(Saleable)",
            "Price/ft2(Gross)",
        ]
        datetime_columns = ["Trans. Date", "Last Transaction Date"]

        df = pd.read_csv(self._legacy_transaction_file_path)
        df = df.drop(columns=["Change"], errors="ignore")
        df[int_columns] = df[int_columns].map(keep_only_numbers).astype("Int64")
        df[datetime_columns] = df[datetime_columns].map(convert_datetime)
        df.to_csv(self.transaction_file_path, index=False)
        return df
