import snowflake.connector
import sys
sys.path.append("../")
sys.path.append("../configs")
import helper_functions
import model_config

def call_model_1(product_id, by_title=False, n=8): 
    """
    Retrieve a list of the most similar product IDs based on description or title 
    and return the corresponding product details.

    This function queries a Snowflake database to fetch the `n` most similar 
    products to a given product ID using either a title-based or description-based 
    similarity table.

    :param productID: str
        The ID of the product for which similar products are to be retrieved.
    :param by_title: bool, optional (default=False)
        If True, similarity is calculated based on product titles. 
        If False, similarity is calculated based on product descriptions.
    :param n: int, optional (default=8)
        The number of most similar product IDs to retrieve.
    :return: list
        A list of product details corresponding to the most similar product IDs.
    """
    conn = snowflake.connector.connect(model_config.CONNECTION_PARAMS)
    if by_title:
        similar_product_ids = helper_functions.get_n_most_similar_product_ids(conn, product_id, n=n, similarity_tablename='product_title_similarity', userID=None)
    else:
        similar_product_ids = helper_functions.get_n_most_similar_product_ids(conn, product_id, n=n, similarity_tablename='product_description_similarity', userID=None)
    print(f"Got productIDs {similar_product_ids}. Returning call_model_1.")
    return helper_functions.get_products_by_product_ids(similar_product_ids)


if __name__ == "__main__":
    call_model_1()
