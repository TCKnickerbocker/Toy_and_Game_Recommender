import snowflake.connector



def get_n_most_similar_product_titles(conn, product_id, n=50):
    """
    Fetch the top n most similar products to a given product_id from both product1_id and product2_id perspectives,
    excluding the current product_id from the results.
    
    Args:
    - conn: Snowflake connection object
    - product_id: The product ID for which to find the top n similar products
    - n: The number of similar products to retrieve (default is 50)
    
    Returns:
    - List of tuples containing (similar_product_id, similarity_score) for the top n most similar products,
      excluding the current product_id.
    """
    
    # Validate that n is a positive integer
    if not isinstance(n, int) or n <= 0:
        raise ValueError("n must be a positive integer")
    
    # Build the query string with the validated n value
    query = """
    (
        SELECT product2_id AS similar_product_id, similarity_score
        FROM product_title_similarity
        WHERE product1_id = %s
          AND product2_id != %s
        ORDER BY similarity_score DESC
        LIMIT %s
    )
    UNION
    (
        SELECT product1_id AS similar_product_id, similarity_score
        FROM product_title_similarity
        WHERE product2_id = %s
          AND product1_id != %s
        ORDER BY similarity_score DESC
        LIMIT %s
    )
    ORDER BY similarity_score DESC
    LIMIT %s;
    """
    
    # Execute the query with parameterized values
    with conn.cursor() as cur:
        cur.execute(query, (product_id, product_id, n, product_id, product_id, n, n))
        top_similar_products = cur.fetchall()
    
    return top_similar_products
