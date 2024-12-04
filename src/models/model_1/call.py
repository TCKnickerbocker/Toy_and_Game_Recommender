import snowflake.connector
import sys
sys.path.append("../")
sys.path.append("../configs")
import helper_functions
import model_config

conn = snowflake.connector.connect(model_config.CONNECTION_PARAMS)


productID_to_query = 'B09S19HKSB'
byTitleProductIDs = helper_functions.get_n_most_similar_products(conn, productID_to_query, similarity_tablename='product_title_similarity', userID=None)
print(byTitleProductIDs)
byDescriptionProductIDs = helper_functions.get_n_most_similar_products(conn, productID_to_query, similarity_tablename='product_description_similarity', userID=None)
print(byDescriptionProductIDs)

print("\n\n\nTop Recs by Title:")
print(helper_functions.get_n_most_similar_product_ids(conn, byTitleProductIDs, product_table='products_for_display'))
print("\n\n\nTop Recs by Description:")
print(helper_functions.get_n_most_similar_product_ids(conn, byDescriptionProductIDs, product_table='products_for_display'))

