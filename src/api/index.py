from flask import Flask, request, jsonify
# from pyspark.sql import SparkSession
# from pyspark.ml.recommendation import ALSModel
from dotenv import load_dotenv
import snowflake.connector
import os

app = Flask(__name__)

# Load trained models
# cf_model = ALSModel.load("models/collaborative_filtering")

# Load Spark session
# spark = SparkSession.builder.appName("RecommendationAPI").getOrCreate()

load_dotenv()

conn = snowflake.connector.connect(
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA")
)

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

@app.route("/api/healthchecker", methods=["GET"])
def healthchecker():
    return {"status": "success", "message": "Integrate Flask Framework with Next.js"}

@app.route("/create_user", methods=["POST"])
def create_user():
    data = request.json

    app.logger.info(f"testing info log {data}")

    user_id = data['user_id']
    email = data['email']

    try:
        cur = conn.cursor()

        cur.execute("INSERT INTO user_accounts (user_id, email) VALUES ('%s', '%s')", (user_id, email))

        conn.commit()
    except snowflake.connector.Error as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return {"message": "User created successfully"}, 201
    

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)


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
