import os
import time
import json

def insert_dataclass_to_db(cursor, table_name, data_instance):
    """
    Takes a Data Class instance and automatically INSERTS it into a SQLite table.
    """
    #declare the exceptions that should not be passed to the db
    exceptions = ['max_id', 'current_id',]

    #turn the Data Class into a dictionary
    data_dict = data_instance.to_dict()

    #filter the data to remove the exceptions
    filtered_data = {k: v for k, v in data_dict.items() if k not in exceptions}
    
    #extract keys (column names) and values
    columns = ', '.join(filtered_data.keys())
    placeholders = ', '.join(['?'] * len(filtered_data))
    values = tuple(filtered_data.values())
    
    #build the SQL string dynamically
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    
    #execute
    cursor.execute(sql, values)

def safe_atomic_replace(data, temp_path, final_path, retries=5):
    for i in range(retries):
        try:
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=4)
            os.replace(temp_path, final_path)
            return True
        except PermissionError:
            # File is likely being read by the Bridge
            time.sleep(0.05) 
    print(f"FAILED to replace {final_path} after {retries} attempts.")
    return False