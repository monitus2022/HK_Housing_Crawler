import re
from .base import BaseProcessor
import sqlite3
import pandas as pd

class AgencyProcessor(BaseProcessor):
    def __init__(self):
        super().__init__()
        self.connect_db()
        self.transaction_file_path = "transactions.csv"

    def process_transaction_table(self):
        """
        Process the transaction table CSV file.
        Cleans and converts data types for specific columns.
        """
        int_columns = ["Area(Saleable)","Area(Gross)","Price(m)","Price/ft2(Saleable)","Price/ft2(Gross)"]
        datetime_columns = ["Trans. Date", "Last Transaction Date"]

        df = pd.read_csv(self.transaction_file_path)
        df = df.drop(columns=["Change"], errors='ignore')
        df[int_columns] = df[int_columns].map(self.keep_only_numbers).astype("Int64")
        df[datetime_columns] = df[datetime_columns].map(self.convert_datetime)
        return df
    
    def process_estate_info_json(self, json_data):
        """
        Process estate info from JSON data.
        """
        pass

    @staticmethod
    def keep_only_numbers(cell):
        """
        Turns a cell with mixed characters into a cell with only numbers.
        """
        if isinstance(cell, str):
            # Keep only numbers (remove all non-digit characters)
            numbers = re.sub(r'\D', "", cell)
            return numbers if numbers else pd.NA
        return cell

    @staticmethod
    def convert_datetime(cell):
        """
        Converts a cell to datetime format.
        """
        if isinstance(cell, str):
            try:
                return pd.to_datetime(cell)
            except ValueError:
                return pd.NA
        return cell