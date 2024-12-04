import json
import concurrent.futures

import boto3
import requests
import os
from urllib.parse import urlparse
import logger


def get_n_most_similar_product_ids(conn, product_id, similarity_tablename='product_description_similarity', n=8, user_id=None):
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
    
    # Build the query string with the validated n value
    if user_id:
        query = f"""
        (
            SELECT product2_id AS similar_product_id
            FROM {similarity_tablename}
            WHERE product1_id = %s
            AND product2_id != %s
            AND product2_id NOT IN (SELECT parent_asin FROM user_ratings WHERE user_id = '{user_id}')
            ORDER BY similarity_score DESC
            LIMIT %s
        )
        UNION
        (
            SELECT product1_id AS similar_product_id
            FROM {similarity_tablename}
            WHERE product2_id = %s
            AND product1_id != %s
            AND product1_id NOT IN (SELECT parent_asin FROM user_ratings WHERE user_id = '{user_id}')
            ORDER BY similarity_score DESC
            LIMIT %s
        )
        ORDER BY similar_product_id
        LIMIT %s;
        """
    else:
        query = f"""
        (
            SELECT product2_id AS similar_product_id
            FROM {similarity_tablename}
            WHERE product1_id = %s
            AND product2_id != %s
            ORDER BY similarity_score DESC
            LIMIT %s
        )
        UNION
        (
            SELECT product1_id AS similar_product_id
            FROM {similarity_tablename}
            WHERE product2_id = %s
            AND product1_id != %s
            ORDER BY similarity_score DESC
            LIMIT %s
        )
        ORDER BY similar_product_id
        LIMIT %s;
        """

    
    # Execute the query with parameterized values
    with conn.cursor() as cur:
        cur.execute(query, (product_id, product_id, n, product_id, product_id, n, n))
        top_similar_products = cur.fetchall()
        
    # Extract just the product IDs from the result
    similar_product_ids = [row[0] for row in top_similar_products]
    
    return similar_product_ids


def get_products_by_product_ids(conn, product_ids, product_table='most_popular_products'):
    """
    Retrieve product details for multiple product IDs from Snowflake.
    The results are returned as JSON, ready to be passed to the frontend.
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

    # Convert the results to JSON format
    return json.dumps(products)


# TODO fix
def store_product_image_in_s3(product_id, original_image_url, image_snowflake_tablename, s3name):
    """
    Download an image from a URL and store it in an S3 bucket.

    :param full_product_data: Dictionary containing product and image details
    :param s3name: Name or identifier for the S3 bucket
    :return: S3 URL of the stored image or None if storage fails
    """
    try:
        # Get the image URL from the product data
        temp_image_url = original_image_url
        if not temp_image_url:
            logger.warning("No image URL found in store_image_in_s3")
            return None

        # Download the image
        response = requests.get(temp_image_url)
        if response.status_code != 200:
            logger.error(f"Failed to download image from {temp_image_url}")
            return None

        # Prepare file details
        file_extension = os.path.splitext(urlparse(temp_image_url).path)[1] or '.png'
        local_filename = f"{product_id}{file_extension}"

        # Save temporary local file
        with open(local_filename, 'wb') as f:
            f.write(response.content)

        # Initialize S3 client, determine path
        s3_client = boto3.client('s3')
        s3_key = f"product_images/{local_filename}"

        # Upload to S3
        s3_client.upload_file(
            local_filename, 
            s3name, 
            s3_key, 
            ExtraArgs={
                'ContentType': response.headers.get('content-type', 'image/png')
            }
        )

        # Generate S3 URL
        s3_url = f"https://{s3name}.s3.amazonaws.com/{s3_key}"

        # Clean up local file
        os.remove(local_filename)

        logger.info(f"Image stored in S3 at {s3_url}")
        return s3_url

    except Exception as e:
        logger.error(f"Error storing image in S3: {e}")
        return None
    
