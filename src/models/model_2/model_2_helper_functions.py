import concurrent.futures

def get_n_most_similar_product_ids_model_2(conn, product_id, similarity_tablename='product_description_similarity', oyt_tablename='oyt_scores_of_most_popular_products', n=8, user_id=None):
    """
    Fetch the top n most similar products to a given product_id from both product1_id and product2_id perspectives,
    excluding the current product_id from the results.
    
    Args:
    - conn: Snowflake connection object
    - product_id: The product ID for which to find the top n similar products
    - n: The number of similar products to retrieve (default is 8)
    - user_id: the user_id within the user_ratings table
    
    Returns:
    - List of product_ids that the user has not yet rated for the top n most similar products, excluding the current product_id.
    """
    
    # Validate that n is a positive integer
    if not isinstance(n, int) or n <= 0:
        raise ValueError("n must be a positive integer")
    
    # Validate inputs to prevent SQL injection
    if not isinstance(product_id, (int, str)):
        raise ValueError("product_id must be an integer or string")
    
    # Convert product_id and user_id to strings to safely insert into query
    product_id_str = str(product_id)
    user_id_str = str(user_id) if user_id is not None else None
    
    # Sanitize table names (assuming they are predefined and trusted)
    similarity_tablename = similarity_tablename.replace(';', '').replace("'", "''")
    oyt_tablename = oyt_tablename.replace(';', '').replace("'", "''")
    
    # Build the query string with parameterized values
    if user_id is not None:
        query = f"""
        WITH similar_products AS (
            SELECT 
                product2_id AS similar_product_id,
                similarity_score
            FROM {similarity_tablename}
            WHERE product1_id = %s
            AND product2_id NOT IN (
                SELECT parent_asin 
                FROM user_ratings 
                WHERE user_id = %s
            )
            UNION ALL
            SELECT 
                product1_id AS similar_product_id,
                similarity_score
            FROM {similarity_tablename}
            WHERE product2_id = %s
            AND product1_id NOT IN (
                SELECT parent_asin 
                FROM user_ratings 
                WHERE user_id = %s
            )
        )
        SELECT 
            sp.similar_product_id,
            sp.similarity_score,
            oyt.oyt_score,
            (sp.similarity_score + COALESCE(oyt.oyt_score, 0)) AS combined_score
        FROM 
            similar_products sp
        LEFT JOIN 
            {oyt_tablename} oyt
        ON 
            sp.similar_product_id = oyt.PRODUCT_ID
        ORDER BY 
            combined_score DESC
        LIMIT %s;
        """
        query_params = (product_id_str, user_id_str, product_id_str, user_id_str, n)
    else:
        query = f"""
        WITH similar_products AS (
            SELECT 
                product2_id AS similar_product_id,
                similarity_score
            FROM {similarity_tablename}
            WHERE product1_id = %s
            AND product2_id NOT IN (
                SELECT parent_asin 
                FROM user_ratings 
            )
            UNION ALL
            SELECT 
                product1_id AS similar_product_id,
                similarity_score
            FROM {similarity_tablename}
            WHERE product2_id = %s
            AND product1_id NOT IN (
                SELECT parent_asin 
                FROM user_ratings 
            )
        )
        SELECT 
            sp.similar_product_id,
            sp.similarity_score,
            oyt.oyt_score,
            (sp.similarity_score + COALESCE(oyt.oyt_score, 0)) AS combined_score
        FROM 
            similar_products sp
        LEFT JOIN 
            {oyt_tablename} oyt
        ON 
            sp.similar_product_id = oyt.PRODUCT_ID
        ORDER BY 
            combined_score DESC
        LIMIT %s;
        """
        query_params = (product_id_str, product_id_str, n)

    # Execute the query with parameterized values
    with conn.cursor() as cur:
        cur.execute(query, query_params)
        top_similar_products = cur.fetchall()
        
    # Extract the product IDs from the result
    similar_product_ids = [row[0] for row in top_similar_products]
    return similar_product_ids


def get_products_by_product_ids(conn, product_ids, product_table='products_for_display'):
    """
    Retrieve product details for multiple product IDs from Snowflake.
    The results are returned as a list of products, where each product is a dictionary.
    """
    # Function to fetch product data for a single product_id
    def fetch_product_data(product_id):
        with conn.cursor() as cur:
            cur.execute(f"""
            SELECT productid, title, image, summary
            FROM {product_table}
            WHERE productid = %s
            """, (product_id,))
            row = cur.fetchone()
            if row:
                return {
                    "productid": row[0],
                    "title": row[1],
                    "image": row[2],
                    "summary": row[3]
                }
            return None  # Return None if no data is found for the product_id

    # Use ThreadPoolExecutor to fetch data concurrently for all product_ids
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Map the product_ids to the fetch_product_data function
        results = list(executor.map(fetch_product_data, product_ids))

    # Filter out None results (in case some product_ids did not have data)
    products = [result for result in results if result is not None]
    return products

def get_recently_rated_products_info(conn, user_id, num_recently_rated):
    """
    Returns [(productID, user's rating, if user favorited product)]
    """
    query = """
    SELECT parent_asin, rating, favorite FROM user_ratings 
    WHERE user_id = %s
    ORDER BY review_id DESC
    LIMIT %s
    """
    try:
        with conn.cursor() as cur:
            cur.execute(query, (user_id, num_recently_rated))
            top_similar_products = cur.fetchall()
            recently_rated_products = [(row[0], row[1], row[2]) for row in top_similar_products]
            return recently_rated_products
    except Exception as e:
        print(f"Error getting recently_rated_products e: {e}")
        return None
