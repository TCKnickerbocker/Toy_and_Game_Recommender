from dotenv import load_dotenv
import snowflake.connector
import os
import sys
sys.path.append("../")
import helper_functions

# Load environment variables
load_dotenv()

conn = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA")
)


productIDs = helper_functions.get_n_most_similar_products(conn, 'B09S19HKSB', similarity_tablename='product_title_similarity')
print(productIDs)
productIDs = helper_functions.get_n_most_similar_products(conn, 'B09S19HKSB', similarity_tablename='product_description_similarity')
print(productIDs)



