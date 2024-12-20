from flask import Flask, request, jsonify, redirect, render_template, session, url_for
from dotenv import load_dotenv
import snowflake.connector
import os
import logger
import time
import random
import requests
from api_utils import (
    setup_connection,
    check_user_exists,
    check_rating_exists,
    check_user_rating_threshold,
)
import threading
from service_metrics import ServiceMetrics, start_metrics_server, track_metrics

load_dotenv()

from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enables CORS for all routes
app.secret_key = os.environ.get("APP_SECRET_KEY")
service_metrics = ServiceMetrics("api_metrics")

# Start metrics server in a separate thread
# metrics_thread = threading.Thread(target=start_metrics_server)
# metrics_thread.daemon = True
# metrics_thread.start()
# i.e. prom query: api_metrics_requests_total
### NOTE: we currently have one function being tracked via @track_metrics(service_metrics, 'GET', '/example')


MODEL_1_URL = "http://model_1:5003/call_model_1"
MODEL_2_URL = "http://model_2:5004/call_model_2"
MODEL_3_URL = "http://model_3:5005/call_model_3"
MODEL_4_URL = "http://model_4:5006/call_model_4"
# ^When in Docker, use model_n:<port>. When not in Docker, use localhost:<port>


@app.route("/api/create_user", methods=["POST"])
def create_user():
    data = request.json

    user_id = data["user_id"]
    email = data["email"]

    try:
        conn = setup_connection()

        cur = conn.cursor()

        if check_user_exists(user_id):
            print("ISSUE: This user already exists")
            conn.commit()
            conn.close()
            return {"message": "User already exists"}, 400

        cur.execute(
            "INSERT INTO user_accounts (user_id, email) VALUES (%s, %s)",
            (user_id, email),
        )

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

    values = []

    for review in data:
        user_id = review["user_id"]
        product_id = review["product_id"]
        rating = review["rating"]
        favorite = review["favorite"]

        if check_rating_exists(user_id, product_id) is True:
            print("ISSUE: User rating already exists for this product")
            return {"message": "User rating already exists for this product"}, 400

        # check_user_rating_threshold(user_id)
        values.append((user_id, product_id, rating, favorite))

    try:
        conn = setup_connection()

        cur = conn.cursor()

        insert_query = """
            INSERT INTO user_ratings (user_id, parent_asin, rating, favorite) 
            VALUES (%s, %s, %s, %s)
        """

        cur.executemany(insert_query, values)

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
# @track_metrics(service_metrics, 'GET', '/initial_products')
def initial_products():
    start_time = time.time()
    try:
        conn = setup_connection()
        cur = conn.cursor()
        results = []

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
        service_metrics.observe_database_query_latency(
            "/initial_products", "random_selection", query_latency
        )

        results = cur.fetchall()

        # Track recommendation generation
        service_metrics.track_recommendation_generation("/initial_products")

        # Observe total recommendation latency
        recommendation_latency = time.time() - start_time
        service_metrics.observe_recommendation_latency(
            "/initial_products", recommendation_latency
        )
        return results

    except snowflake.connector.Error as e:
        # Track database errors
        service_metrics.track_recommendation_error(
            "/initial_products", "database_error"
        )
        print(f"Error: {e}")
        conn.rollback()
        return {"message": "Something went wrong with fetching initial products"}, 400
    except Exception as e:
        # Track other types of errors
        service_metrics.track_recommendation_error(
            "/initial_products", "unexpected_error"
        )
        print(f"Unexpected error: {e}")
        return {"message": "Unexpected error occurred"}, 500
    finally:
        conn.close()


@app.route("/api/call_model_1", methods=["GET"])
# @track_metrics(service_metrics, 'GET', '/call_model_1')
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
        print("In API. About to call model 1")
        # Extract query parameters
        user_id = request.args.get("user_id", None)
        # if not user_id:
        #     service_metrics.track_recommendation_error('/call_model_1', 'missing_user_id')
        #     return jsonify({"error": "Missing required parameter: user_id"}), 400

        # Prepare parameters for external model call
        params = {
            "user_id": user_id,
            "num_recently_rated": int(request.args.get("num_recently_rated", 8)),
            "num_recs_to_give": int(request.args.get("num_recs_to_give", 8)),
            "by_title": request.args.get("by_title", "false").lower() == "true",
        }

        # Track external model call latency
        model_call_start_time = time.time()
        response = requests.get(MODEL_1_URL, params=params)
        print("Got response ", response, " from model 1. in API")
        model_call_latency = time.time() - model_call_start_time
        service_metrics.observe_external_model_call_latency(
            MODEL_1_URL, model_call_latency
        )

        if response.status_code == 200:
            # Track successful recommendation generation
            service_metrics.track_recommendation_generation("/call_model_1")

            # Observe total recommendation latency
            recommendation_latency = time.time() - start_time
            service_metrics.observe_recommendation_latency(
                "/call_model_1", recommendation_latency
            )
            print("Returning 200 from API")
            return jsonify(response.json()), 200
        else:
            # Track model call errors
            service_metrics.track_recommendation_error(
                "/call_model_1", "model_call_failure"
            )
            return jsonify(
                {
                    "error": "Failed to retrieve recommendations from model 1",
                    "details": response.text,
                }
            ), 500

    except Exception as e:
        # Track unexpected errors
        service_metrics.track_recommendation_error(
            "/call_model_1", "unexpected_error"
        )
        print(f"Error in /api/call_model_1: {e}")
        return jsonify(
            {"error": "Failed to retrieve most similar products", "details": str(e)}
        ), 500


@app.route("/api/call_model_2", methods=["GET"])
# @track_metrics(service_metrics, 'GET', '/call_model_2')
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
        start_time = time.time()
        user_id = request.args.get("user_id", None)
        # if not user_id:
        #     service_metrics.track_recommendation_error('/call_model_2', 'missing_user_id')
        #     return jsonify({"error": "Missing required parameter: user_id"}), 400

        # Extract other parameters
        num_recently_rated = int(request.args.get("num_recently_rated", 8))
        num_recs_to_give = int(request.args.get("num_recs_to_give", 8))
        by_title = request.args.get("by_title", "false").lower() == "true"

        params = {
            "user_id": user_id,
            "num_recently_rated": num_recently_rated,
            "num_recs_to_give": num_recs_to_give,
            "by_title": by_title,
        }

        model_call_start_time = time.time()
        response = requests.get(MODEL_2_URL, params=params)
        model_call_latency = time.time() - model_call_start_time
        service_metrics.observe_external_model_call_latency(
            MODEL_2_URL, model_call_latency
        )

        if response.status_code == 200:
            # Track successful recommendation generation
            service_metrics.track_recommendation_generation("/call_model_2")
            # Observe total recommendation latency
            recommendation_latency = time.time() - start_time
            service_metrics.observe_recommendation_latency(
                "/call_model_2", recommendation_latency
            )
            return jsonify(response.json()), 200
        else:
            service_metrics.track_recommendation_error(
                "/call_model_2", "model_call_failure"
            )
            return jsonify(
                {
                    "error": "Failed to retrieve recommendations from model 2",
                    "details": response.text,
                }
            ), 500

    except Exception as e:
        service_metrics.track_recommendation_error("/call_model_2", "unexpected_error")
        return jsonify(
            {"error": "Failed to retrieve most similar products", "details": str(e)}
        ), 500


@app.route("/api/call_model_3", methods=["GET"])
# @track_metrics(service_metrics, 'GET', '/call_model_3')
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
        user_id = request.args.get("user_id", None)
        # if not user_id:
        #     service_metrics.track_recommendation_error('/call_model_3', 'missing_user_id')
        #     return jsonify({"error": "Missing required parameter: user_id"}), 400

        # Extract other parameters
        num_recently_rated = int(request.args.get("num_recently_rated", 8))
        num_recs_to_give = int(request.args.get("num_recs_to_give", 8))
        by_title = request.args.get("by_title", "false").lower() == "true"

        params = {
            "user_id": user_id,
            "num_recently_rated": num_recently_rated,
            "num_recs_to_give": num_recs_to_give,
            "by_title": by_title,
        }

        model_call_start_time = time.time()
        response = requests.get(MODEL_3_URL, params=params)
        model_call_latency = time.time() - model_call_start_time
        service_metrics.observe_external_model_call_latency(
            MODEL_3_URL, model_call_latency
        )

        if response.status_code == 200:
            # Track successful recommendation generation
            service_metrics.track_recommendation_generation("/call_model_3")
            # Observe total recommendation latency
            recommendation_latency = time.time() - start_time
            service_metrics.observe_recommendation_latency(
                "/call_model_3", recommendation_latency
            )
            return jsonify(response.json()), 200
        else:
            service_metrics.track_recommendation_error(
                "/call_model_3", "model_call_failure"
            )
            return jsonify(
                {
                    "error": "Failed to retrieve recommendations from model 3",
                    "details": response.text,
                }
            ), 500

    except Exception as e:
        service_metrics.track_recommendation_error("/call_model_3", "unexpected_error")
        return jsonify(
            {"error": "Failed to retrieve most similar products", "details": str(e)}
        ), 500


@app.route("/api/call_model_4", methods=["GET"])
# @track_metrics(service_metrics, 'GET', '/call_model_4')
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
        user_id = request.args.get("user_id", None)
        # if not user_id:
        #     service_metrics.track_recommendation_error('/call_model_4', 'missing_user_id')
        #     return jsonify({"error": "Missing required parameter: user_id"}), 400

        # Extract other parameters
        num_recently_rated = int(request.args.get("num_recently_rated", 8))
        num_recs_to_give = int(request.args.get("num_recs_to_give", 8))
        by_title = request.args.get("by_title", "false").lower() == "true"

        params = {
            "user_id": user_id,
            "num_recently_rated": num_recently_rated,
            "num_recs_to_give": num_recs_to_give,
            "by_title": by_title,
        }

        model_call_start_time = time.time()
        response = requests.get(MODEL_4_URL, params=params)
        model_call_latency = time.time() - model_call_start_time
        service_metrics.observe_external_model_call_latency(
            MODEL_4_URL, model_call_latency
        )

        if response.status_code == 200:
            # Track successful recommendation generation
            service_metrics.track_recommendation_generation("/call_model_4")
            # Observe total recommendation latency
            recommendation_latency = time.time() - start_time
            service_metrics.observe_recommendation_latency(
                "/call_model_4",
                recommendation_latency,
            )
            return jsonify(response.json()), 200
        else:
            service_metrics.track_recommendation_error(
                "/call_model_4",
                "model_call_failure",
            )
            return jsonify(
                {
                    "error": "Failed to retrieve recommendations from model 4",
                    "details": response.text,
                }
            ), 500

    except Exception as e:
        service_metrics.track_recommendation_error("/call_model_4", "unexpected_error")
        return jsonify(
            {"error": "Failed to retrieve most similar products", "details": str(e)}
        ), 500


"""
Generate Fake Product
    - Will call the NLP Model to generate a fake product based on the user's ratings
"""
PRODUCT_GENERATOR_URL = "http://generate_new_products:5007/generate_fake_product"


@app.route("/api/generate_fake_product", methods=["GET"])
# @track_metrics(service_metrics, 'GET', '/generate_fake_product')
def generate_fake_products():
    try:
        start_time = time.time()

        # Get user ID and number of products from query parameters
        user_id = request.args.get("user_id")
        num_products = int(
            request.args.get("num_products", 1)
        )  # Default to 1 if not provided

        # Safety catch for too many products
        if num_products > 8:
            service_metrics.track_recommendation_error(
                "/generate_fake_product", "too_many_products_requested"
            )
            return jsonify({"SAFETY CATCH: tried to generate too many products"}), 403

        # Prepare the request payload
        payload = {"user_id": user_id, "num_products": num_products}

        # Track external model call latency
        model_call_start_time = time.time()
        response = requests.get(PRODUCT_GENERATOR_URL, json=payload)
        model_call_latency = time.time() - model_call_start_time
        service_metrics.observe_external_model_call_latency(
            PRODUCT_GENERATOR_URL, model_call_latency
        )

        if response.status_code == 200:
            # Track successful product generation
            service_metrics.track_recommendation_generation("/generate_fake_product")

            # Observe total recommendation latency
            recommendation_latency = time.time() - start_time
            service_metrics.observe_recommendation_latency(
                "/generate_fake_product", recommendation_latency
            )

            return jsonify(response.json()), 200
        else:
            # Track model call errors
            service_metrics.track_recommendation_error(
                "/generate_fake_product", "model_call_failure"
            )
            return jsonify(
                {
                    "error": "Failed to generate products from the generator service",
                    "details": response.json(),
                }
            ), response.status_code

    except Exception as e:
        # Track unexpected errors
        service_metrics.track_recommendation_error(
            "/generate_fake_product", "unexpected_error"
        )
        logger.error(f"Error generating fake products: {e}")

        # Return an error response
        return jsonify({"error": "Failed to generate products", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
