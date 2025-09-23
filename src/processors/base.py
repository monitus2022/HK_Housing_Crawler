from abc import ABC, abstractmethod
import sqlite3
from typing import Optional

class BaseProcessor(ABC):
    def __init__(self):
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor = None
        self.db_path = ""
    
    def check_db_existence(self) -> bool:
        """
        Check if the SQLite database exists.
        """
        return False
    
    def connect_db(self):
        """
        Connect to the SQLite database.
        """
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
    def close_db(self):
        """
        Close the database connection.
        """
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None    
                
    @abstractmethod
    def process_data(self):
        """
        Abstract method to process data. Must be implemented by subclasses.
        """
        pass
    