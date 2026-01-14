def insert_dataclass_to_db(cursor, table_name, data_instance):
    """
    Takes a Data Class instance and automatically INSERTS it into a SQLite table.
    """
    # 1. Turn the Data Class into a dictionary
    data_dict = data_instance.to_dict()
    
    # 2. Extract keys (column names) and values
    columns = ', '.join(data_dict.keys())
    placeholders = ', '.join(['?'] * len(data_dict))
    values = tuple(data_dict.values())
    
    # 3. Build the SQL string dynamically
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    
    # 4. Execute it
    cursor.execute(sql, values)