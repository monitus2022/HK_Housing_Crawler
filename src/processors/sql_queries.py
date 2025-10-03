class SqlQueries:
    
    @staticmethod
    def create_table_queries(fields: dict[str, str]) -> str:
        """
        Generate a CREATE TABLE SQL query based on the provided fields.
        
        Args:
            fields (dict): A dict with col names: data types
        """
        columns = ",\n    ".join([f"{col} {dtype}" for col, dtype in fields.items()])
        return f"""
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {columns}
        );
        """

    @staticmethod
    def insert_query(table_name: str, fields: dict[str, str]) -> str:
        """
        Dynamically generate INSERT query
        
        Args:
            fields (dict): A dict with col names: data types
        """
        field_names = list(fields.keys())
        placeholders = ['?' for _ in fields]
        
        query = f"""
        INSERT INTO {table_name} ({', '.join(field_names)})
        VALUES ({', '.join(placeholders)});
        """
        return query


    @staticmethod
    def update_by_id_query(fields: dict[str, str]) -> str:
        """
        Generate an UPDATE BY ID SQL query for the properties table.
        """
        set_clause = ", ".join([f"{col} = ?" for col in fields.keys()])
        return f"""
        UPDATE properties
        SET {set_clause}
        WHERE id = ?;
        """
        