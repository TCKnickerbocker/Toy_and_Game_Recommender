from flask import Flask, request, jsonify, redirect, render_template, session, url_for
# from pyspark.sql import SparkSession
# from pyspark.ml.recommendation import ALSModel
from dotenv import load_dotenv, find_dotenv
import snowflake.connector
import os
from os import environ as env
import sys

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

        cur.execute("CREATE OR REPLACE TABLE user_ratings (REVIEW_ID INT IDENTITY PRIMARY KEY, USER_ID VARCHAR(255), PARENT_ASIN VARCHAR(50), RATING FLOAT, FAVORITE BOOLEAN, FOREIGN KEY (user_id) REFERENCES user_accounts(user_id) ON DELETE CASCADE);")

        if check_user_exists(user_id) == True:
            print("ISSUE: This user already exists")
            conn.commit()
            conn.close()
            return {"message": "User already exists"}, 400
        else:
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

"""
Get N Most Similar Products Based on Past Ratings
    - We'll now need to return the most similar products based on what the user's previously rated an item
    - Maybe use the ratings as weights in some sort of equation?
"""
@app.route("/api/most_similar_products", methods=["GET"])
def most_similar_products():

    return

"""
Generate Fake Product
    - Will call the NLP Model to generate a fake product based on the user's ratings
"""
@app.route("/api/generate_fake_product", methods=["GET"])
def generate_fake_product():

    return

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
