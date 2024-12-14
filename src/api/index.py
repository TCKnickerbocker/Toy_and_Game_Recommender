from flask import Flask, request, jsonify, redirect, render_template, session, url_for
from dotenv import load_dotenv
import snowflake.connector
import os
import logger
<<<<<<< HEAD
import requests
import sys
sys.path.append("../models/generate_new_products")
from call_generate_model import call_generate_products
sys.path.append("../models/model_1")
from call_model_1 import call_model_1
sys.path.append("../models/model_2")
from call_model_2 import call_model_2
sys.path.append("../models/model_3")
from call_model_3 import call_model_3
sys.path.append("../models/model_4")
from call_model_4 import call_model_4



app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

# Load trained models
# cf_model = ALSModel.load("models/collaborative_filtering")

# Load Spark session
# spark = SparkSession.builder.appName("RecommendationAPI").getOrCreate()

load_dotenv()

def setup_connection():
    try:

        conn = snowflake.connector.connect(
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
            database=os.getenv("SNOWFLAKE_DATABASE"),
            schema=os.getenv("SNOWFLAKE_SCHEMA")
        )

        return conn
    except snowflake.connector.Error as e:
        print(f"Error connecting to Snowflake: {e}", file=sys.stderr)
        print(os.getenv("SNOWFLAKE_USER"))
        print(os.getenv("SNOWFLAKE_PASSWORD"))
        raise

# Checks if a user exists or not
def check_user_exists(user_id):
    try:
        conn = setup_connection()

        cur = conn.cursor()

        cur.execute("SELECT * FROM user_accounts WHERE user_id = %s", (user_id))

        results = cur.fetchall()
        return len(results) > 0
    except snowflake.connector.Error as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return False

def check_rating_exists(user_id, product_id):
    try:
        conn = setup_connection()

        cur = conn.cursor()

        cur.execute("SELECT * FROM user_ratings WHERE user_id = %s AND parent_asin = %s", (user_id, product_id))

        results = cur.fetchall()
        return len(results) > 0
    except snowflake.connector.Error as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return False

# Will delete all the user's ratings if they have more than 100
def check_user_rating_threshold(user_id):
    try:
        conn = setup_connection()

        cur = conn.cursor()

        cur.execute("""
            DELETE FROM user_ratings
            WHERE user_id IN (
                SELECT user_id
                FROM user_ratings
                GROUP BY user_id
                HAVING COUNT(*) > 100
            )
            AND user_id = %s;
            """, (user_id))
        conn.commit()
    except snowflake.connector.Error as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return
    
=======
import time
import random
import requests
from api_utils import setup_connection, check_user_exists, check_rating_exists, check_user_rating_threshold
import threading
from service_metrics import ServiceMetrics, start_metrics_server, track_metrics

load_dotenv()

from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # Enables CORS for all routes
app.secret_key = os.environ.get("APP_SECRET_KEY")
service_metrics = ServiceMetrics('api_metrics')

# Start metrics server in a separate thread
metrics_thread = threading.Thread(target=start_metrics_server)
metrics_thread.daemon = True
metrics_thread.start()
# i.e. prom query: api_metrics_requests_total
### NOTE: we currently have one function being tracked via @track_metrics(service_metrics, 'GET', '/example')


MODEL_1_URL = "http://model_1:5003/most_similar_products"
MODEL_2_URL = "http://model_2:5004/recommend_products_sentiment_model"
MODEL_3_URL = "http://model_3:5005/recommend_products_llm_model" 
MODEL_4_URL = "http://model_4:5006/recommend_products_similarity_oyt_llm_combined_model" 
# ^When in Docker, use model_n:<port>. When not in Docker, use localhost:<port>
>>>>>>> main



@app.route("/api/create_user", methods=["POST"])
def create_user():
    data = request.json

    user_id = data['user_id']
    email = data['email']

    try:
        conn = setup_connection()

        cur = conn.cursor()

        if check_user_exists(user_id):
            print("ISSUE: This user already exists")
            conn.commit()
            conn.close()
            return {"message": "User already exists"}, 400

        cur.execute("INSERT INTO user_accounts (user_id, email) VALUES (%s, %s)", (user_id, email))

        conn.commit()
    except snowflake.connector.Error as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return {"message": "User created successfully"}, 201

@app.route("/api/user_ratings", methods=["POST"])
def insert_user_reviews():
    data = request.json

    user_id = data['user_id']
    product_id = data['product_id']
    rating = data['rating']
    favorite = data['favorite']

    if check_rating_exists(user_id, product_id) is True:
        print("ISSUE: User rating already exists for this product")
        return {"message": "User rating already exists for this product"}, 400

    try:
        conn = setup_connection()

        cur = conn.cursor()

        check_user_rating_threshold(user_id)

        cur.execute("INSERT INTO user_ratings (user_id, parent_asin, rating, favorite) VALUES (%s, %s, %s, %s)", (user_id, product_id, rating, favorite))

        conn.commit()
    except snowflake.connector.Error as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return {"message": "Reviews inserted successfully"}, 201


"""
Get Initial N Products
    - Should return N products for the user to initially rate
    - Could be the N most popular products or N random products
"""
@app.route("/api/initial_products", methods=["GET"])
@track_metrics(service_metrics, 'GET', '/initial_products')
def initial_products():
    start_time = time.time()
    try:
        conn = setup_connection()
<<<<<<< HEAD
        # res = []

        # num_total_products = request.args.get('num_total_products', 8)
        # num_ai_generated_products = request.args.get('num_ai_generated_products', 0) 

        cur = conn.cursor()
        # if num_ai_generated_products > 0:
        #     cur.execute(f"SELECT * FROM ai_generated_products ORDER BY RANDOM() LIMIT {num_ai_generated_products}")  # TODO: replace w products_for_display ?
        #     res.extend(cur.fetchall())
        
        # # Get real products
        # num_real_products = num_total_products - len(res)
        # cur.execute(f"SELECT * FROM most_popular_products ORDER BY RANDOM() LIMIT {num_real_products}")  # TODO: replace w products_for_display ?
        # res.extend(cur.fetchall())

        # # Return a randomly ordered list of both
        # return random.shuffle(res)
=======
        cur = conn.cursor()
        results = []
>>>>>>> main

        # num_total_products = request.args.get('num_total_products', 8)
        # num_ai_generated_products = request.args.get('num_ai_generated_products', 0) 

        # if num_ai_generated_products > 0:
        #     cur.execute(f"SELECT * FROM ai_generated_products ORDER BY RANDOM() LIMIT {num_ai_generated_products}")  # TODO: replace w products_for_display ?
        #     results.extend(cur.fetchall())
        
        # # Get real products
        # num_real_products = num_total_products - len(res)
        # cur.execute(f"SELECT * FROM most_popular_products ORDER BY RANDOM() LIMIT {num_real_products}")  # TODO: replace w products_for_display ?
        # res.extend(cur.fetchall())

        # # Return a randomly ordered list of both
        # return random.shuffle(res)

        # Track database query latency
        query_start_time = time.time()
        cur.execute("SELECT * FROM most_popular_products ORDER BY RANDOM() LIMIT 8")
        query_latency = time.time() - query_start_time
        service_metrics.observe_database_query_latency('/initial_products', 'random_selection', query_latency)

        results = cur.fetchall()
        
        # Track recommendation generation
        service_metrics.track_recommendation_generation('/initial_products')
        
        # Observe total recommendation latency
        recommendation_latency = time.time() - start_time
        service_metrics.observe_recommendation_latency('/initial_products', recommendation_latency)

        return results
    except snowflake.connector.Error as e:
        # Track database errors
        service_metrics.track_recommendation_error('/initial_products', 'database_error')
        print(f"Error: {e}")
        conn.rollback()
        return {"message": "Something went wrong with fetching initial products"}, 400
    except Exception as e:
        # Track other types of errors
        service_metrics.track_recommendation_error('/initial_products', 'unexpected_error')
        print(f"Unexpected error: {e}")
        return {"message": "Unexpected error occurred"}, 500
    finally:
        conn.close()


@app.route("/api/most_similar_products", methods=["GET"])
<<<<<<< HEAD
def get_recommendations_model_1():
=======
@track_metrics(service_metrics, 'GET', '/most_similar_products')
def get_recommendations_model_1():
    """
    API endpoint to retrieve the most similar products based on a given product ID.
    Accepts query parameters for the product ID, number of results, and whether to
    use title-based similarity (else defaults to description-based similarity).
    
    Query Parameters:
        - product_id: str (required)
        - n: int (optional, default=8)
        - by_title: bool (optional, default=False)

    Returns:
        - JSON response containing the most similar products or an error message.
    """
    start_time = time.time()
    try:
        # Extract query parameters
        user_id = request.args.get('user_id', None)
        if not user_id:
            service_metrics.track_recommendation_error('/most_similar_products', 'missing_user_id')
            return jsonify({"error": "Missing required parameter: user_id"}), 400
        
        # Prepare parameters for external model call
        params = {
            'user_id': user_id,
            'num_recently_rated': int(request.args.get('num_recently_rated', 8)),
            'num_recs_to_give': int(request.args.get('num_recs_to_give', 8)),
            'by_title': request.args.get('by_title', 'false').lower() == 'true'
        }

        # Track external model call latency
        model_call_start_time = time.time()
        response = requests.get(MODEL_1_URL, params=params)
        model_call_latency = time.time() - model_call_start_time
        service_metrics.observe_external_model_call_latency(MODEL_1_URL, model_call_latency)

        if response.status_code == 200:
            # Track successful recommendation generation
            service_metrics.track_recommendation_generation('/most_similar_products')
            
            # Observe total recommendation latency
            recommendation_latency = time.time() - start_time
            service_metrics.observe_recommendation_latency('/most_similar_products', recommendation_latency)
            
            return jsonify(response.json()), 200
        else:
            # Track model call errors
            service_metrics.track_recommendation_error('/most_similar_products', 'model_call_failure')
            return jsonify({
                "error": "Failed to retrieve recommendations from model 1", 
                "details": response.text
            }), 500
        
    except Exception as e:
        # Track unexpected errors
        service_metrics.track_recommendation_error('/most_similar_products', 'unexpected_error')
        print(f"Error in /api/most_similar_products: {e}")
        return jsonify({
            "error": "Failed to retrieve most similar products", 
            "details": str(e)
        }), 500


@app.route("/api/recommend_products_sentiment_model", methods=["GET"])
@track_metrics(service_metrics, 'GET', '/recommend_products_sentiment_model')
def get_recommendations_model_2():
>>>>>>> main
    """
    API endpoint to retrieve the most similar products based on a given product ID.
    Accepts query parameters for the product ID, number of results, and whether to
    use title-based similarity (else defaults to description-based similarity).
    
    Query Parameters:
        - product_id: str (required)
        - n: int (optional, default=8)
        - by_title: bool (optional, default=False)

    Returns:
        - JSON response containing the most similar products or an error message.
    """
    try:
<<<<<<< HEAD
        print("MODEL 1")
        # Extract query parameters
        user_id = request.args.get('user_id', None)  # User ID required, but no default
=======
        start_time = time.time()
        user_id = request.args.get('user_id', None)
>>>>>>> main
        if not user_id:
            service_metrics.track_recommendation_error('/recommend_products_sentiment_model', 'missing_user_id')
            return jsonify({"error": "Missing required parameter: user_id"}), 400

<<<<<<< HEAD
        # Prepare query parameters for the second container's API
        # params = {
        #     'user_id': user_id,
        #     'num_recently_rated': num_recently_rated,
        #     'num_recs_to_give': num_recs_to_give,
        #     'by_title': by_title
        # }

        # Call the second container's API
        # response = requests.get(MODEL_1_URL, params=params)
        response = call_model_1(user_id, num_recently_rated, num_recs_to_give, by_title)

        # if response.status_code == 200:
            # Return the success response from the second container's API
        # return jsonify(response.json()), 200
        return response
        # else:
        #     return jsonify({"error": "Failed to retrieve recommendations from model 1", "details": response.text}), 500
        
=======
        # Extract other parameters
        num_recently_rated = int(request.args.get('num_recently_rated', 8))
        num_recs_to_give = int(request.args.get('num_recs_to_give', 8))
        by_title = request.args.get('by_title', 'false').lower() == 'true'

        params = {
            'user_id': user_id,
            'num_recently_rated': num_recently_rated,
            'num_recs_to_give': num_recs_to_give,
            'by_title': by_title
        }

        model_call_start_time = time.time()
        response = requests.get(MODEL_2_URL, params=params)
        model_call_latency = time.time() - model_call_start_time
        service_metrics.observe_external_model_call_latency(MODEL_2_URL, model_call_latency)

        if response.status_code == 200:
            # Track successful recommendation generation
            service_metrics.track_recommendation_generation('/recommend_products_sentiment_model')
            # Observe total recommendation latency
            recommendation_latency = time.time() - start_time
            service_metrics.observe_recommendation_latency('/recommend_products_sentiment_model', recommendation_latency)
            return jsonify(response.json()), 200
        else:
            service_metrics.track_recommendation_error('/recommend_products_sentiment_model', 'model_call_failure')
            return jsonify({"error": "Failed to retrieve recommendations from model 2", "details": response.text}), 500

>>>>>>> main
    except Exception as e:
        service_metrics.track_recommendation_error('/recommend_products_sentiment_model', 'unexpected_error')
        return jsonify({"error": "Failed to retrieve most similar products", "details": str(e)}), 500


@app.route("/api/recommend_products_llm_model", methods=["GET"])
@track_metrics(service_metrics, 'GET', '/recommend_products_llm_model')
def get_recommendations_model_3():
    """
    API endpoint to retrieve the most similar products based on a given product ID.
    Accepts query parameters for the product ID, number of results, and whether to
    use title-based similarity (else defaults to description-based similarity).
    
    Query Parameters:
        - product_id: str (required)
        - n: int (optional, default=8)
        - by_title: bool (optional, default=False)

    Returns:
        - JSON response containing the most similar products or an error message.
    """
    try:
        start_time = time.time()
        user_id = request.args.get('user_id', None)
        if not user_id:
            service_metrics.track_recommendation_error('/recommend_products_llm_model', 'missing_user_id')
            return jsonify({"error": "Missing required parameter: user_id"}), 400

        # Extract other parameters
        num_recently_rated = int(request.args.get('num_recently_rated', 8))
        num_recs_to_give = int(request.args.get('num_recs_to_give', 8))
        by_title = request.args.get('by_title', 'false').lower() == 'true'

        params = {
            'user_id': user_id,
            'num_recently_rated': num_recently_rated,
            'num_recs_to_give': num_recs_to_give,
            'by_title': by_title
        }

        model_call_start_time = time.time()
        response = requests.get(MODEL_3_URL, params=params)
        model_call_latency = time.time() - model_call_start_time
        service_metrics.observe_external_model_call_latency(MODEL_3_URL, model_call_latency)

        if response.status_code == 200:
            # Track successful recommendation generation
            service_metrics.track_recommendation_generation('/recommend_products_llm_model')
            # Observe total recommendation latency
            recommendation_latency = time.time() - start_time
            service_metrics.observe_recommendation_latency('/recommend_products_llm_model', recommendation_latency)
            return jsonify(response.json()), 200
        else:
            service_metrics.track_recommendation_error('/recommend_products_llm_model', 'model_call_failure')
            return jsonify({"error": "Failed to retrieve recommendations from model 3", "details": response.text}), 500

    except Exception as e:
        service_metrics.track_recommendation_error('/recommend_products_llm_model', 'unexpected_error')
        return jsonify({"error": "Failed to retrieve most similar products", "details": str(e)}), 500


@app.route("/api/recommend_products_similarity_oyt_llm_combined_model", methods=["GET"])
@track_metrics(service_metrics, 'GET', '/recommend_products_similarity_oyt_llm_combined_model')
def get_recommendations_model_4():
    """
    API endpoint to retrieve the most similar products based on a given product ID.
    Accepts query parameters for the product ID, number of results, and whether to
    use title-based similarity (else defaults to description-based similarity).
    
    Query Parameters:
        - product_id: str (required)
        - n: int (optional, default=8)
        - by_title: bool (optional, default=False)

    Returns:
        - JSON response containing the most similar products or an error message.
    """
    try:
        start_time = time.time()
        user_id = request.args.get('user_id', None)
        if not user_id:
            service_metrics.track_recommendation_error('/recommend_products_similarity_oyt_llm_combined_model', 'missing_user_id')
            return jsonify({"error": "Missing required parameter: user_id"}), 400

        # Extract other parameters
        num_recently_rated = int(request.args.get('num_recently_rated', 8))
        num_recs_to_give = int(request.args.get('num_recs_to_give', 8))
        by_title = request.args.get('by_title', 'false').lower() == 'true'

        params = {
            'user_id': user_id,
            'num_recently_rated': num_recently_rated,
            'num_recs_to_give': num_recs_to_give,
            'by_title': by_title
        }

        model_call_start_time = time.time()
        response = requests.get(MODEL_4_URL, params=params)
        model_call_latency = time.time() - model_call_start_time
        service_metrics.observe_external_model_call_latency(MODEL_4_URL, model_call_latency)

        if response.status_code == 200:
            # Track successful recommendation generation
            service_metrics.track_recommendation_generation('/recommend_products_similarity_oyt_llm_combined_model')
            # Observe total recommendation latency
            recommendation_latency = time.time() - start_time
            service_metrics.observe_recommendation_latency('/recommend_products_similarity_oyt_llm_combined_model', recommendation_latency)
            return jsonify(response.json()), 200
        else:
            service_metrics.track_recommendation_error('/recommend_products_similarity_oyt_llm_combined_model', 'model_call_failure')
            return jsonify({"error": "Failed to retrieve recommendations from model 4", "details": response.text}), 500

    except Exception as e:
        service_metrics.track_recommendation_error('/recommend_products_similarity_oyt_llm_combined_model', 'unexpected_error')
        return jsonify({"error": "Failed to retrieve most similar products", "details": str(e)}), 500


MODEL_2_URL = "http://localhost:5004/recommend_products_sentiment_model"  # TODO adjust front-end to use
@app.route("/api/recommend_products_sentiment_model", methods=["GET"])
def get_recommendations_model_2():
    """
    API endpoint to retrieve the most similar products based on a given product ID.
    Accepts query parameters for the product ID, number of results, and whether to
    use title-based similarity (else defaults to description-based similarity).
    
    Query Parameters:
        - product_id: str (required)
        - n: int (optional, default=8)
        - by_title: bool (optional, default=False)

    Returns:
        - JSON response containing the most similar products or an error message.
    """
    try:
        print("MODEL 2")
        # Extract query parameters
        user_id = request.args.get('user_id', None)  # User ID required, but no default
        if not user_id:
            return jsonify({"error": "Missing required parameter: user_id"}), 400
        
        num_recently_rated = int(request.args.get('num_recently_rated', 8))  # Default to 8 if not provided
        num_recs_to_give = int(request.args.get('num_recs_to_give', 8))  # Default to 8 if not provided
        by_title = request.args.get('by_title', 'false').lower() == 'true'  # Convert to boolean

        # Prepare query parameters for the second container's API
        # params = {
        #     'user_id': user_id,
        #     'num_recently_rated': num_recently_rated,
        #     'num_recs_to_give': num_recs_to_give,
        #     'by_title': by_title
        # }

        # Call the second container's API
        # response = requests.get(MODEL_2_URL, params=params)
        response = call_model_2(user_id, num_recently_rated, num_recs_to_give, by_title)

        # if response.status_code == 200:
            # Return the success response from the second container's API
        # return jsonify(response.json()), 200
        return response
        # else:
        #     return jsonify({"error": "Failed to retrieve recommendations from model 1", "details": response.text}), 500
        
    except Exception as e:
        # Log & return the error
        print(f"Error in /api/most_similar_products: {e}")
        return jsonify({"error": "Failed to retrieve most similar products", "details": str(e)}), 500

MODEL_3_URL = "http://localhost:5005/recommend_products_llm_model"  # TODO adjust front-end to use
@app.route("/api/recommend_products_llm_model", methods=["GET"])
def get_recommendations_model_3():
    """
    API endpoint to retrieve the most similar products based on a given product ID.
    Accepts query parameters for the product ID, number of results, and whether to
    use title-based similarity (else defaults to description-based similarity).
    
    Query Parameters:
        - product_id: str (required)
        - n: int (optional, default=8)
        - by_title: bool (optional, default=False)

    Returns:
        - JSON response containing the most similar products or an error message.
    """
    try:
        print("MODEL 3")
        # Extract query parameters
        user_id = request.args.get('user_id', None)  # User ID required, but no default
        if not user_id:
            return jsonify({"error": "Missing required parameter: user_id"}), 400
        
        num_recently_rated = int(request.args.get('num_recently_rated', 8))  # Default to 8 if not provided
        num_recs_to_give = int(request.args.get('num_recs_to_give', 8))  # Default to 8 if not provided
        by_title = request.args.get('by_title', 'false').lower() == 'true'  # Convert to boolean

        # Prepare query parameters for the second container's API
        # params = {
        #     'user_id': user_id,
        #     'num_recently_rated': num_recently_rated,
        #     'num_recs_to_give': num_recs_to_give,
        #     'by_title': by_title
        # }

        # Call the second container's API
        # response = requests.get(MODEL_3_URL, params=params)
        response = call_model_3(user_id, num_recently_rated, num_recs_to_give, by_title)

        # if response.status_code == 200:
            # Return the success response from the second container's API
        # return jsonify(response.json()), 200
        return response
        # else:
        #     return jsonify({"error": "Failed to retrieve recommendations from model 1", "details": response.text}), 500
        
    except Exception as e:
        # Log & return the error
        print(f"Error in /api/most_similar_products: {e}")
        return jsonify({"error": "Failed to retrieve most similar products", "details": str(e)}), 500


MODEL_4_URL = "http://localhost:5006/recommend_products_similarity_oyt_llm_combined_model"  # TODO adjust front-end to use
@app.route("/api/recommend_products_similarity_oyt_llm_combined_model", methods=["GET"])
def get_recommendations_model_4():
    """
    API endpoint to retrieve the most similar products based on a given product ID.
    Accepts query parameters for the product ID, number of results, and whether to
    use title-based similarity (else defaults to description-based similarity).
    
    Query Parameters:
        - product_id: str (required)
        - n: int (optional, default=8)
        - by_title: bool (optional, default=False)

    Returns:
        - JSON response containing the most similar products or an error message.
    """
    try:
        print("MODEL 4")
        # Extract query parameters
        user_id = request.args.get('user_id', None)  # User ID required, but no default
        if not user_id:
            return jsonify({"error": "Missing required parameter: user_id"}), 400
        
        num_recently_rated = int(request.args.get('num_recently_rated', 8))  # Default to 8 if not provided
        num_recs_to_give = int(request.args.get('num_recs_to_give', 8))  # Default to 8 if not provided
        by_title = request.args.get('by_title', 'false').lower() == 'true'  # Convert to boolean

        # Prepare query parameters for the second container's API
        # params = {
        #     'user_id': user_id,
        #     'num_recently_rated': num_recently_rated,
        #     'num_recs_to_give': num_recs_to_give,
        #     'by_title': by_title
        # }

        # Call the second container's API
        # response = requests.get(MODEL_4_URL, params=params)
        response = call_model_4(user_id, num_recently_rated, num_recs_to_give, by_title)

        # if response.status_code == 200:
            # Return the success response from the second container's API
        # return jsonify(response.json()), 200
        return response
        # else:
        #     return jsonify({"error": "Failed to retrieve recommendations from model 1", "details": response.text}), 500
        
    except Exception as e:
        # Log & return the error
        print(f"Error in /api/most_similar_products: {e}")
        return jsonify({"error": "Failed to retrieve most similar products", "details": str(e)}), 500


"""
Generate Fake Product
    - Will call the NLP Model to generate a fake product based on the user's ratings
"""
<<<<<<< HEAD
PRODUCT_GENERATOR_URL = "http://localhost:5007/generate_fake_product"  # Replace as needed
=======
PRODUCT_GENERATOR_URL = "http://generate_new_products:5007/generate_fake_product"  
>>>>>>> main
@app.route("/api/generate_fake_product", methods=["GET"])
@track_metrics(service_metrics, 'GET', '/generate_fake_product')
def generate_fake_products():
    try:
        start_time = time.time()
        
        # Get user ID and number of products from query parameters
        user_id = request.args.get('user_id')
        num_products = int(request.args.get('num_products', 1))  # Default to 1 if not provided

        # Safety catch for too many products
        if num_products > 8:
            service_metrics.track_recommendation_error('/generate_fake_product', 'too_many_products_requested')
            return jsonify({'SAFETY CATCH: tried to generate too many products'}), 403

        # Prepare the request payload
        # payload = {
        #     "user_id": user_id,
        #     "num_products": num_products
        # }

<<<<<<< HEAD
        # Call the product generation API in the other container
        # response = requests.post(PRODUCT_GENERATOR_URL, json=payload)
        response = call_generate_products(user_id, num_products)

        # Check if the request was successful
        # if response.status_code == 200:
        # return jsonify(response.json()), 200
        return response
        # else:
            # Handle API errors from the first container
            # return jsonify({
            #     "error": "Failed to generate products from the generator service",
            #     "details": response.json()
            # }), response.status_code
=======
        # Track external model call latency
        model_call_start_time = time.time()
        response = requests.get(PRODUCT_GENERATOR_URL, json=payload)
        model_call_latency = time.time() - model_call_start_time
        service_metrics.observe_external_model_call_latency(PRODUCT_GENERATOR_URL, model_call_latency)

        if response.status_code == 200:
            # Track successful product generation
            service_metrics.track_recommendation_generation('/generate_fake_product')

            # Observe total recommendation latency
            recommendation_latency = time.time() - start_time
            service_metrics.observe_recommendation_latency('/generate_fake_product', recommendation_latency)
            
            return jsonify(response.json()), 200
        else:
            # Track model call errors
            service_metrics.track_recommendation_error('/generate_fake_product', 'model_call_failure')
            return jsonify({
                "error": "Failed to generate products from the generator service",
                "details": response.json()
            }), response.status_code
>>>>>>> main

    except Exception as e:
        # Track unexpected errors
        service_metrics.track_recommendation_error('/generate_fake_product', 'unexpected_error')
        logger.error(f"Error generating fake products: {e}")
        
        # Return an error response
        return jsonify({
            "error": "Failed to generate products",
            "details": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)

