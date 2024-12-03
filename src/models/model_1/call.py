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


productID_to_query = 'B09S19HKSB'
byTitleProductIDs = helper_functions.get_n_most_similar_products(conn, productID_to_query, similarity_tablename='product_title_similarity')
print(byTitleProductIDs)
byDescriptionProductIDs = helper_functions.get_n_most_similar_products(conn, productID_to_query, similarity_tablename='product_description_similarity')
print(byDescriptionProductIDs)

print("\n\n\nTop Recs by Title:")
print(helper_functions.get_n_most_similar_product_ids(conn, byTitleProductIDs, product_table='most_popular_products'))
print("\n\n\nTop Recs by Description:")
print(helper_functions.get_n_most_similar_product_ids(conn, byDescriptionProductIDs, product_table='most_popular_products'))

