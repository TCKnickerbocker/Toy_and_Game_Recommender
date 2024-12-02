import os
import pandas as pd
from dotenv import load_dotenv
import snowflake.connector
import json

# Load environment variables
load_dotenv()

def update_image_column(
    table_name="most_popular_products", 
    modify_column=True
):
    """
    Updates the image column in the specified Snowflake table based on prioritized image URLs.

    Args:
        table_name (str): Name of the table to update. Defaults to "most_popular_products".
        variant (str): The variant to filter by. Defaults to "MAIN".
        modify_column (bool): Whether to ensure the image column is of type VARCHAR. Defaults to True.

    Returns:
        None
    """
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA")
    )

    try:
        cur = conn.cursor()

        # F
        select_query = f"""
        select productid, image from {table_name};
        """
        cur.execute(select_query)
        results = cur.fetchall()
        # Convert to DataFrame for easier handling
        df = pd.DataFrame(results, columns=["productid", "selected_image"])
        for _, row in df.iterrows():
            try:
                tmp = json.loads(row['selected_image'])
                # index 0 is main image by default            
                img = tmp[0]['hi_res'] if tmp[0]['hi_res'] is not None else tmp[0]['large']
                row['selected_image'] = img
            except:  # noqa: E722
                continue
            
        # Update the `image` column with filtered data
        for _, row in df.iterrows():
            update_query = f"""
            UPDATE {table_name}
            SET image = '{row['selected_image']}'
            WHERE productid = '{row['productid']}';
            """
            cur.execute(update_query)

        # Optionally ensure the `image` column type is VARCHAR
        if modify_column:
            alter_query = f"""
            ALTER TABLE {table_name}
            MODIFY COLUMN image VARCHAR;
            """
            cur.execute(alter_query)

        # Commit the transaction
        conn.commit()

        # Verify the updates
        cur.execute(f"SELECT productid, image FROM {table_name} LIMIT 1;")
        updated_results = cur.fetchall()
        print("Updated Results:", updated_results)

    except snowflake.connector.Error as e:
        print(f"Error: {e}")

    finally:
        # Close the cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    update_image_column()
