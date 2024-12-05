from flask import Flask, request, jsonify, redirect, render_template, session, url_for
# from pyspark.sql import SparkSession
# from pyspark.ml.recommendation import ALSModel
from dotenv import load_dotenv, find_dotenv
import snowflake.connector
import os
from os import environ as env
import logger
import sys
sys.path.append("../models")
sys.path.append("../models/generate_new_products")
sys.path.append("../models/model_1")
from call_generate_model import call_generate_products
from call_model_1 import call_model_1


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



# @app.route("/recommend", methods=["GET"])
# def recommend():
#     user_id = int(request.args.get("user_id"))
#     num_recs = int(request.args.get("num_recs", 3))
    
#     # Generate recommendations for the user
#     recommendations = cf_model.recommendForUserSubset(
#         spark.createDataFrame([(user_id,)], ["user_id"]), num_recs
#     )
    
#     # Extract product IDs from recommendations
#     recs = recommendations.collect()[0]["recommendations"]
#     product_ids = [rec["product_id"] for rec in recs]
#     return jsonify({"user_id": user_id, "recommended_products": product_ids})

@app.route("/api/create_user", methods=["POST"])
def create_user():
    data = request.json

    user_id = data['user_id']
    email = data['email']

    try:
        conn = setup_connection()

        cur = conn.cursor()

        if check_user_exists(user_id) == True:
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

    if check_rating_exists(user_id, product_id) == True:
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


# TODO: FUNCTIONS TO CREATE

"""
Get Initial N Products
    - Should return N products for the user to initially rate
    - Could be the N most popular products or N random products
"""
@app.route("/api/initial_products", methods=["GET"])
def initial_products():
    try:
        conn = setup_connection()

        cur = conn.cursor()

        cur.execute("SELECT * FROM most_popular_products ORDER BY RANDOM() LIMIT 8")

        return cur.fetchall()
    except snowflake.connector.Error as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return {"message": "Something went wrong with fetching initial products"}, 400

@app.route("/api/most_similar_products", methods=["GET"])
def most_similar_products():
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
        # Extract query parameters
        user_id = request.args.get('user_id')
        # return jsonify({"error": "Missing required parameter: user_id"}), 400  # TODO: Have return error if no user_id when in prod
        
        # num_recently_rated = int(request.args.get('num_recently_rated', 8))  # Default to 8 if not provided
        # num_recs_to_give = int(request.args.get('num_recs_to_give', 8))  # Default to 8 if not provided
        
        by_title = request.args.get('by_title', 'false').lower() == 'true'  # Convert to boolean

        # Call the model function
        products_json = call_model_1(user_id=user_id, num_recently_rated=8, num_recs_to_give=8, by_title=by_title)
        # print(f"API Returning: {products_json}")
        # Return a success response
        return jsonify(products_json), 200
    except Exception as e:
        # Log & return the error
        print(f"Error in /api/most_similar_products: {e}")
        return jsonify({"error": "Failed to retrieve most similar products", "details": str(e)}), 500

"""
Generate Fake Product
    - Will call the NLP Model to generate a fake product based on the user's ratings
"""
@app.route("/api/generate_fake_product", methods=["GET"])
def generate_fake_products():
    try:
        user_id = request.args.get('user_id')
        num_products = request.args.get('num_products')
        if num_products > 8:
            return jsonify({'SAFETY CATCH: tried to generate too many products'}), 403
        # Call the product generation function
        generated_products = call_generate_products.call_generate_products(user_id=user_id, num_products=num_products)
        return jsonify(generated_products), 200

    except Exception as e:
        # Log the error
        logger.error(f"Error generating fake products: {e}")
        
        # Return an error response
        return jsonify({
            "error": "Failed to generate products",
            "details": str(e)
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)


'''
from prometheus_flask_exporter import PrometheusMetrics

# Initialize Prometheus metrics
metrics = PrometheusMetrics(app)

# Add custom metric: track recommendations served
recommendation_counter = metrics.counter(
    'recommendations_served', 'Number of recommendations served',
    labels={'status': lambda r: r.status_code}  # Label metric by HTTP status
)

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({"status": "healthy"})

@app.route('/ready', methods=['GET'])
def ready():
    return jsonify({"status": "ready"})

'''
