import re
from .base import BaseProcessor
import sqlite3
import pandas as pd
import json

class AgencyProcessor(BaseProcessor):
    def __init__(self):
        super().__init__()
        self.connect_db()
        self.legacy_transaction_file_path = "transactions.csv"
        self.transaction_file_path = "all_transactions.json"
        self.estate_info_json_path = "estate_info.json"

    def process_transaction_json(self) -> pd.DataFrame:
        """
        Process the transaction JSON file.
        Output a cleaned DataFrame to be stored in the database.
        """
        with open(self.transaction_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        

    def _legacy_process_transaction_table(self) -> pd.DataFrame:
        """
        Process the transaction table CSV file.
        Cleans and converts data types for specific columns.
        Only applies to the legacy CSV format.
        """
        int_columns = ["Area(Saleable)","Area(Gross)","Price(m)","Price/ft2(Saleable)","Price/ft2(Gross)"]
        datetime_columns = ["Trans. Date", "Last Transaction Date"]

        df = pd.read_csv(self.transaction_file_path)
        df = df.drop(columns=["Change"], errors='ignore')
        df[int_columns] = df[int_columns].map(self.keep_only_numbers).astype("Int64")
        df[datetime_columns] = df[datetime_columns].map(self.convert_datetime)
        df.to_csv(self.transaction_file_path, index=False)
        return df
    
    def process_estate_info_json(self) -> list[dict]:
        with open(self.estate_info_json_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        data = [self._process_single_estate_info(info) for info in data]
        with open("processed_" + self.estate_info_json_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        return data

    def _process_single_estate_info(self, info) -> dict:
        output_dict = {}
        for key, value in info.items():
            if key == "property_stat":
                output_dict.update(value)
            elif key == "market_stat":
                if "yearly" in value:
                    yearly_info = value["yearly"]
                    yearly_info = {
                        f"yearly_{k}": v 
                        for k, v in yearly_info.items()
                        }
                    output_dict.update(yearly_info)
                    value.pop("yearly")
                output_dict.update({
                    f"recent_{k}": v
                    for k, v in value.items()
                })
            elif type(value) is dict:
                output_dict.update({
                    f"{key}_{sub_key}": sub_value
                    for sub_key, sub_value in value.items()
                })
            elif "url" in key or key in ["icon", "hos", "show"]: 
                continue
            else:
                output_dict[key] = value
        return output_dict

    def get_estate_ids_from_processed_estate_info(self) -> list[str]:
        with open("processed_" + self.estate_info_json_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return [item["id"] for item in data if "id" in item]

    @staticmethod
    def keep_only_numbers(cell) -> any:
        """
        Turns a cell with mixed characters into a cell with only numbers.
        """
        if isinstance(cell, str):
            # Keep only numbers (remove all non-digit characters)
            numbers = re.sub(r'\D', "", cell)
            return numbers if numbers else pd.NA
        return cell

    @staticmethod
    def convert_datetime(cell) -> any:
        """
        Converts a cell to datetime format.
        """
        if isinstance(cell, str):
            try:
                return pd.to_datetime(cell)
            except ValueError:
                return pd.NA
        return cell