from typing import Optional

def generate_create_table_query(
    table_name: str, columns: Optional[dict] = None
) -> str:
    """
    Generate a CREATE TABLE SQL query.

    Parameters:
        table_name (str): The name of the table to create.
        columns (dict): A dictionary where keys are column names and values are data types.

    Returns:
        str: The generated CREATE TABLE SQL query.
    """
    if not columns:
        query = f"CREATE TABLE {table_name} AS SELECT * FROM temp_df"
    else:
        cols_with_types = ", ".join(
            [f"{col} {dtype}" for col, dtype in columns.items()]
        )
        create_query = f"CREATE TABLE {table_name} ({cols_with_types})"
        insert_query = f"INSERT INTO {table_name} SELECT * FROM temp_df"
        query = f"{create_query}; {insert_query};"
    return query