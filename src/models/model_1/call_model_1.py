from flask import Flask, request, jsonify
import snowflake.connector
from snowflake.connector.errors import DatabaseError
import model_1_helper_functions
import model_1_alg
from model_1_configs import CONNECTION_PARAMS

# Prometheus monitoring
from prometheus_client import Counter, Histogram, start_http_server
import time
import logging
import concurrent.futures
import threading
import os

app = Flask(__name__)

# Prometheus Metrics
RECOMMENDATIONS_TOTAL = Counter(
    'recommendations_total', 
    'Total number of recommendation requests',
    ['method', 'endpoint']
)
RECOMMENDATION_LATENCY = Histogram(
    'recommendation_latency_seconds', 
    'Time spent generating recommendations',
    ['method', 'endpoint']
)
RECOMMENDATION_ERRORS = Counter(
    'recommendation_errors_total', 
    'Total number of recommendation errors',
    ['method', 'endpoint', 'error_type']
)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        RECOMMENDATION_ERRORS.labels(
            method='GET', 
            endpoint='/most_similar_products', 
            error_type='db_connection'
        ).inc()
        raise

def call_model_1(user_id, num_recently_rated, num_recs_to_give, by_title=False): 
    """
    Retrieve a list of the most similar product IDs based on description or title.
    
    Includes performance tracking, error handling, and multithreading.
    """
    start_time = time.time()
    
    try:
        # Use context manager for connection
        with get_db_connection() as conn:
            # Determine number of worker threads based on available CPU cores
            max_workers = min(os.cpu_count(), num_recently_rated)
            end_time0 = time.time()
            print(f"Getting connection and max_workers: {end_time0 - start_time:.2f} seconds")
            
            most_similar_products = {}
            recently_rated_products = model_1_helper_functions.get_recently_rated_products_info(
                conn, user_id, num_recently_rated
            )
            end_time1 = time.time()
            print(f"Getting recently rated took: {end_time1 - end_time0:.2f} seconds")
            
            # Multithreaded processing of recently rated products
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Create a dictionary to store futures
                future_to_product = {}
                
                # Submit tasks for each recently rated product
                for rating_info in recently_rated_products:
                    product_id = rating_info[0]
                    # Submit the similarity lookup as a task
                    future = executor.submit(
                        model_1_helper_functions.get_n_most_similar_product_ids_model_1, 
                        conn, 
                        product_id, 
                        n=num_recs_to_give, 
                        similarity_tablename='product_title_similarity' if by_title else 'product_description_similarity', 
                        user_id=user_id
                    )
                    future_to_product[future] = (product_id, rating_info)
                
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
            end_time2 = time.time()
            print(f"get_n_most_similar_product_ids_model_1 for {num_recently_rated} products took: {end_time2 - end_time1:.2f} seconds")
            
            # Get products to recommend 
            product_ids_to_rec = model_1_alg.recommend_products(
                most_similar_products, num_recs_to_give
            )
            
            # Performance tracking
            end_time3 = time.time()
            print(f"recommend_products took: {end_time3 - end_time2:.2f} seconds")
            
            x = model_1_helper_functions.get_products_by_product_ids(conn, product_ids_to_rec)
            end_time4 = time.time()
            print(f"get_products_by_product_ids took: {end_time4 - end_time3:.2f} seconds")
            
            end_time5 = time.time()
            print(f"Total time for {num_recs_to_give} products with {num_recently_rated} recent ratings: {end_time5 - start_time:.2f} seconds")
            return x
    
    except Exception as e:
        print(f"Error in call_model_1: {e}")
        RECOMMENDATION_ERRORS.labels(
            method='GET', 
            endpoint='/most_similar_products', 
            error_type='recommendation_generation'
        ).inc()
        raise
    finally:
        # Record latency
        latency = time.time() - start_time
        RECOMMENDATION_LATENCY.labels(
            method='GET', 
            endpoint='/most_similar_products'
        ).observe(latency)

@app.route("/most_similar_products", methods=["GET"])
def most_similar_products():
    """
    API endpoint to retrieve the most similar products.
    Enhanced with metrics and improved error handling.
    """
    # Increment total recommendations counter
    RECOMMENDATIONS_TOTAL.labels(
        method='GET', 
        endpoint='/most_similar_products'
    ).inc()

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

def run_metrics_server(port=9100):
    """
    Start Prometheus metrics server on a specified port
    
    Args:
        port (int): Port to expose metrics server. Defaults to 9100.
    """
    print(f"Starting model_1 prometheus metrics on port {port}")
    start_http_server(port)  # Metrics exposed on port
    

# Start metrics server & run app
if __name__ == "__main__":
    # Use environment variable for metrics port, default to 9100
    # metrics_port = int(os.getenv('METRICS_PORT', 9100))
    
    # metrics_thread = threading.Thread(target=run_metrics_server, kwargs={'port': metrics_port})
    # metrics_thread.start()
    call_model_1("dummyUser", 8, 8)
    # app.run(debug=True, host="0.0.0.0", port=5003)
