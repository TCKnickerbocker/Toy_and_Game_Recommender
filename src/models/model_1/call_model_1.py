import snowflake.connector
import random
import numpy as np
import sys
sys.path.append("../")
sys.path.append("../configs")
import helper_functions
import model_1_funcs
from model_config import CONNECTION_PARAMS

def call_model_1(user_id, num_recently_rated, num_recs_to_give, by_title=False): 
    """
    Retrieve a list of the most similar product IDs based on description or title 
    and return the corresponding product details.

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
    conn = snowflake.connector.connect(**CONNECTION_PARAMS)
    most_similar_products = {}
    recently_rated_products = helper_functions.get_recently_rated_products_info(conn, user_id, num_recently_rated)  # [(productID, user's rating, if user favorited product)]
    # For each recently rated product_id, get similar product ids:    
    for rating_info in recently_rated_products:
        product_id = rating_info[0]
        if by_title:
            similar_product_ids = helper_functions.get_n_most_similar_product_ids(conn, product_id, n=num_recs_to_give, similarity_tablename='product_title_similarity', user_id=user_id)
        else:
            similar_product_ids = helper_functions.get_n_most_similar_product_ids(conn, rating_info[0], n=num_recs_to_give, similarity_tablename='product_description_similarity', user_id=user_id)
        most_similar_products[product_id] = [rating_info[1], rating_info[2], similar_product_ids]  # user's rating, whether user favorited, ordered list of similar product ids
        
    # Get products to recommend 
    product_ids_to_rec = model_1_funcs.recommend_products(most_similar_products, num_recs_to_give)
    print(f"Recommending product_ids: {product_ids_to_rec}. Returning call_model_1.")
    return helper_functions.get_products_by_product_ids(conn, product_ids_to_rec)


if __name__ == "__main__":
    res = call_model_1('dummyUser', 8, 3)
