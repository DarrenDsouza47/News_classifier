import sqlite3
import json

def export_to_json(db_name, table_name, json_file_name):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # SQL query to select all records from the specified table
    query = f"SELECT * FROM {table_name};"
    
    try:
        # Execute the query
        cursor.execute(query)

        # Fetch all records
        records = cursor.fetchall()

        # Get the column names
        column_names = [description[0] for description in cursor.description]

        # Convert records to a list of dictionaries
        data = []
        for record in records:
            row = {column_names[i]: record[i] for i in range(len(column_names))}
            data.append(row)

        # Write the data to a JSON file
        with open(json_file_name, 'w') as json_file:
            json.dump(data, json_file, indent=4)

        print(f"Data exported to {json_file_name} successfully.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()

# Example usage
export_to_json('news_articles.db', 'articles', 'articles_dump.json')
