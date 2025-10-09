from abc import ABC
import duckdb
from typing import Optional
from pathlib import Path
from logger import housing_logger
from .sql_queries import generate_create_table_query

working_dir = Path(__file__).parent.parent.parent


class BaseProcessor(ABC):
    def __init__(self):
        # Init a local DuckDB database connection
        self.data_storage_path = working_dir / "data"
        self.data_storage_path.mkdir(exist_ok=True)
        self.db_path = self.data_storage_path / "housing_crawler.duckdb"
        self.conn: Optional[duckdb.DuckDBPyConnection] = None

    def connect_db(self) -> None:
        """
        Connect to the DuckDB database.
        Automatically creates the database file if it does not exist.
        """
        self.conn = duckdb.connect(self.db_path)
        housing_logger.info(f"Connected to database at {self.db_path}")

    def close_db(self) -> None:
        """
        Close the database connection.
        """
        if self.conn:
            self.conn.close()
            self.conn = None
            housing_logger.info("Database connection closed.")

    def save_dataframe_to_db(
        self, df, table_name: str, dtypes: dict = None, if_exists: str = "replace"
    ) -> None:
        """
        Save a pandas DataFrame to the DuckDB database.

        Parameters:
            df (pd.DataFrame): The DataFrame to save.
            table_name (str): The name of the table in the database.
            dtypes (dict): Optional dictionary specifying column data types.
            if_exists (str): What to do if the table already exists.
                             Options are 'fail', 'replace', or 'append'.
        """
        # Check if the database connection is established
        if self.conn is None:
            housing_logger.error("Database connection is not established.")
            return None
        housing_logger.info(f"Saving DataFrame to table '{table_name}' in database...")

        # Check if the table already exists
        if if_exists == "replace":
            self.conn.execute(f"DROP TABLE IF EXISTS {table_name}")
        elif if_exists == "fail":
            existing_tables = self.conn.execute("SHOW TABLES").fetchall()
            if (table_name,) in existing_tables:
                housing_logger.error(
                    f"Table '{table_name}' already exists. Aborting save."
                )
                return None
        elif if_exists == "append":
            pass
        else:
            housing_logger.error(
                f"""
                Invalid value for if_exists: {if_exists}. 
                Use 'fail', 'replace', or 'append' (Default: 'replace').
                """
            )
            return None

        # Save the DataFrame to the database, replace or append
        self.conn.register("temp_df", df)
        self.conn.execute(generate_create_table_query(table_name, dtypes))
        self.conn.unregister("temp_df")
        housing_logger.info(f"DataFrame saved to table '{table_name}' in database.")
