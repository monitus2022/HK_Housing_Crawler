import duckdb
from typing import Optional, Union
from pathlib import Path
from logger import housing_logger
from .sql_queries import generate_create_table_query
from config import housing_crawler_config
import sqlite3


class BaseProcessor:
    def __init__(self):
        # Set up data storage paths
        self.working_dir = Path(__file__).parent.parent.parent.resolve()
        self.data_storage_path = self.working_dir / housing_crawler_config.storage.root_path
        self.database_path = self.data_storage_path / housing_crawler_config.storage.databases.path
        self.files_path = self.data_storage_path / housing_crawler_config.storage.files.path
        for path in [self.data_storage_path, self.database_path, self.files_path]:
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    housing_logger.error(f"Failed to create directory {path}: {e}")

        # Database paths
        self.duckdb_path = self.database_path / housing_crawler_config.storage.databases.file_names.duckdb
        self.sqlite_path = self.database_path / housing_crawler_config.storage.databases.file_names.sqlite

        # Database connection
        self.conn: Optional[Union[duckdb.DuckDBPyConnection, sqlite3.Connection]] = None

    def connect_db(self, db_type: str = "duckdb") -> None:
        """
        Connect to the DuckDB/SQLite database.
        Automatically creates the database file if it does not exist.
        """
        if db_type == "sqlite":
            self.conn = sqlite3.connect(self.sqlite_path)
            housing_logger.info(f"Connected to SQLite database at {self.sqlite_path}")
        elif db_type == "duckdb":
            self.conn = duckdb.connect(self.duckdb_path)
            housing_logger.info(f"Connected to database at {self.duckdb_path}")
        else:
            housing_logger.error(f"Unsupported database type: {db_type}")
            self.conn = None
            raise ValueError(f"Unsupported database type: {db_type}")

    def close_db(self) -> None:
        """
        Close the database connection.
        """
        if self.conn:
            self.conn.close()
            self.conn = None
            housing_logger.info("Database connection closed.")

    def save_dataframe_to_db(self, df, db_type: str = "duckdb", **kwargs) -> None:
        """
        Save a pandas DataFrame to the specified database type.

        Parameters:
            df (pd.DataFrame): The DataFrame to save.
            db_type (str): The type of database to save to. Options are 'duckdb' or 'sqlite'.
            **kwargs: Additional keyword arguments for the specific save function.
        """
        if db_type == "sqlite":
            self._save_dataframe_to_sqlite(df, **kwargs)
        elif db_type == "duckdb":
            self._save_dataframe_to_duckdb(df, **kwargs)
        else:
            housing_logger.error(f"Unsupported database type: {db_type}")
            raise ValueError(f"Unsupported database type: {db_type}")

    def _save_dataframe_to_sqlite(
        self, df, table_name: str, dtypes: dict = None, if_exists: str = "replace"
    ) -> None:
        """
        Save a pandas DataFrame to the SQLite database.

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
        self.conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {', '.join([f"{col} {dtype}" for col, dtype in dtypes.items()])}
            )
            """,
        )
        df.to_sql(table_name, self.conn, if_exists=if_exists, index=False)
        housing_logger.info(f"DataFrame saved to table '{table_name}' in database.")

    def _save_dataframe_to_duckdb(
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
