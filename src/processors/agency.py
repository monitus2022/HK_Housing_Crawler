from .base import BaseProcessor
import sqlite3
import pandas as pd

class AgencyProcessor(BaseProcessor):
    def __init__(self):
        super().__init__()
        if not self.check_db_existence():
            self.create_db()
        self.connect_db()