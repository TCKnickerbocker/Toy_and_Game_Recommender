# NOTE: this file works.
import os
import pandas as pd
from dotenv import load_dotenv
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

# Load environment variables
load_dotenv()


# Connect to Snowflake using variables from .env
conn = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"), # questionable
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA")  # questionable
)


if __name__ == "__main__":
    # Example DataFrame
    example_data = {
        "product_name": ["Toy A", "Toy B", "Toy C", "Toy D"],
        "rating": [4.5, 3.0, 4.8, 3.5],
        "stock_quantity": [10, 15, 5, 20]
    }
    example_df = pd.DataFrame(example_data)

    # Table name
    table_name = "test_toy_ratings"
    
    try:
        # Create a cursor
        cur = conn.cursor()

        # Convert DataFrame to SQL insert statement
        for index, row in example_df.iterrows():
            insert_query = f"""
            INSERT INTO {table_name} (product_name, rating, stock_quantity)
            VALUES ('{row['product_name']}', {row['rating']}, {row['stock_quantity']})
            """
            cur.execute(insert_query)
        
        # Commit the transaction
        conn.commit()

        # Fetch and print results to verify
        cur.execute(f"SELECT * FROM {table_name}")
        results = cur.fetchall()
        print(results)

    except snowflake.connector.Error as e:
        print(f"Error: {e}")

    finally:
        # Close the cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()
    print(results)
