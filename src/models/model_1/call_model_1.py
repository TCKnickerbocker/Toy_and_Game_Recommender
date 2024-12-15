from flask import Flask, request, jsonify
import snowflake.connector
from snowflake.connector.errors import DatabaseError
import model_1_helper_functions
import model_1_alg
from model_1_configs import CONNECTION_PARAMS

import time
import logging
import concurrent.futures
import threading
import os

app = Flask(__name__)


# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
print("Flask app started for model 1")

def get_db_connection():
    """
    Create a database connection with proper error handling.

    Returns:
        snowflake.connector.connection.SnowflakeConnection: Database connection
    """
    try:
        conn = snowflake.connector.connect(**CONNECTION_PARAMS)
        return conn
    except DatabaseError as e:
        logger.error(f"Database connection error: {e}")
        raise

def call_model_1(user_id, num_recently_rated, num_recs_to_give, by_title=False): 
    """
    Retrieve a list of the most similar product IDs based on description or title.
    
    Includes performance tracking, error handling, and multithreading.
    """
    start_time = time.time()
    print("Model 1 params are: ", user_id, num_recently_rated, num_recs_to_give)
    try:
        print("trying in model 1")
        # Use function for getting database connection
        with get_db_connection() as conn:
            # Determine number of worker threads based on available CPU cores
            max_workers = min(os.cpu_count(), num_recently_rated)
            print("Conn in model_1: ", conn)
            print(num_recently_rated)
            print(type(num_recently_rated))
            print(user_id)
            print(type(user_id))
            # Track time for getting recently rated products
            # recently_rated_products = model_1_helper_functions.get_recently_rated_products_info(
            #     conn, user_id, num_recently_rated
            # )
            recently_rated_products = model_1_helper_functions.get_recently_rated_products_info(conn, 'dummyUser', 8) 
            print("got recently rated product info in model 1")
            # Multithreaded processing of recently rated products
            most_similar_products = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Create a dictionary to store futures
                future_to_product = {}
                
                # Submit tasks for each recently rated product
                for rating_info in recently_rated_products:
                    product_id = rating_info[0]
                    future = executor.submit(
                        model_1_helper_functions.get_n_most_similar_product_ids_model_1, 
                        conn, 
                        product_id, 
                        n=num_recs_to_give, 
                        similarity_tablename='product_title_similarity' if by_title else 'product_description_similarity', 
                        user_id=user_id
                    )
                    future_to_product[future] = (product_id, rating_info)
                print("Collecting futures in model 1")
                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_product):
                    product_id, rating_info = future_to_product[future]
                    try:
                        similar_product_ids = future.result()
                        most_similar_products[product_id] = [
                            rating_info[1], rating_info[2], similar_product_ids
                        ]
                    except Exception as exc:
                        print(f'Product {product_id} generated an exception: {exc}')
            print("Threads returned in model 1. Recommending products")
            product_ids_to_rec = model_1_alg.recommend_products(
                most_similar_products, num_recs_to_give
            )
            print("More returned in model 1. Getting products by id")
            x = model_1_helper_functions.get_products_by_product_ids(conn, product_ids_to_rec)
            print("Returning proucts to api layer from model 1")
            return x
    
    except Exception as e:
        print(f"Error in call_model_1: {e}")
        raise
    finally:
        # Record total latency
        latency = time.time() - start_time


@app.route("/call_model_1", methods=["GET"])
def most_similar_products():
    """
    API endpoint to retrieve the most similar products.
    Enhanced with error handling.
    """
    try:
        # Extract query parameters
        user_id = request.args.get('user_id', "dummyUser")
        num_recently_rated = int(request.args.get('num_recently_rated', 8))
        num_recs_to_give = int(request.args.get('num_recs_to_give', 8))
        by_title = request.args.get('by_title', 'false').lower() == 'true'

        # Call the model function
        products_json = call_model_1(
            user_id=user_id, 
            num_recently_rated=num_recently_rated, 
            num_recs_to_give=num_recs_to_give, 
            by_title=by_title
        )
        
        # Return a success response
        return jsonify(products_json), 200

    except Exception as e:
        logger.error(f"API endpoint error: {e}")
        return jsonify({
            "error": "Failed to retrieve most similar products", 
            "details": str(e)
        }), 500


# Start metrics server & run app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5003)
    # most_similar_products()
    # conn = get_db_connection()
    # print("Got conn")
    # recently_rated_products = model_1_helper_functions.get_recently_rated_products_info(
    #     conn, 'dummyUser', 8
    # )    
    # print("Results: ", recently_rated_products)
    # recently_rated_products = model_1_helper_functions.get_recently_rated_products_info(conn, 'dummyUser', 8)
    # print(recently_rated_products)
    # call_model_1('dummyUser', 8, 8)