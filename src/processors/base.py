from abc import ABC, abstractmethod
import sqlite3
from typing import Optional
from pathlib import Path
from logger import housing_logger

working_dir = Path(__file__).parent.parent

class BaseProcessor(ABC):
    def __init__(self):
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor = None
        self.db_path = working_dir / "housing_crawler.db"
    
    def connect_db(self) -> None:
        """
        Connect to the SQLite database. 
        Automatically creates the database file if it does not exist.
        """
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        housing_logger.info(f"Connected to database at {self.db_path}")
        
    def close_db(self) -> None:
        """
        Close the database connection.
        """
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def save_dataframe_to_db(self, df, table_name: str, if_exists: str = "replace") -> None:
        """
        Save a pandas DataFrame to the SQLite database.
        
        Parameters:
            df (pd.DataFrame): The DataFrame to save.
            table_name (str): The name of the table in the database.
            if_exists (str): What to do if the table already exists. 
                             Options are 'fail', 'replace', or 'append'.
        """
        if self.conn is None:
            housing_logger.error("Database connection is not established.")
            return None
        df.to_sql(table_name, self.conn, if_exists=if_exists, index=False)
        housing_logger.info(f"DataFrame saved to table '{table_name}' in database.")
