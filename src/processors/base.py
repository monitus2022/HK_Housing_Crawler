from abc import ABC, abstractmethod
import sqlite3
from typing import Optional
from pathlib import Path

working_dir = Path(__file__).parent.parent

class BaseProcessor(ABC):
    def __init__(self):
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor = None
        self.db_path = working_dir / "database.db"
    
    def connect_db(self) -> None:
        """
        Connect to the SQLite database. 
        Automatically creates the database file if it does not exist.
        """
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
    def close_db(self) -> None:
        """
        Close the database connection.
        """
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
    
    def create_table_if_not_exists(self) -> None:
        """
        Create necessary tables if they do not exist.
        """
        pass
