from flask import Flask, request, jsonify
from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALSModel

app = Flask(__name__)

# Load trained models
cf_model = ALSModel.load("models/collaborative_filtering")

# Load Spark session
spark = SparkSession.builder.appName("RecommendationAPI").getOrCreate()

@app.route("/recommend", methods=["GET"])
def recommend():
    user_id = int(request.args.get("user_id"))
    num_recs = int(request.args.get("num_recs", 3))
    
    # Generate recommendations for the user
    recommendations = cf_model.recommendForUserSubset(
        spark.createDataFrame([(user_id,)], ["user_id"]), num_recs
    )
    
    # Extract product IDs from recommendations
    recs = recommendations.collect()[0]["recommendations"]
    product_ids = [rec["product_id"] for rec in recs]
    return jsonify({"user_id": user_id, "recommended_products": product_ids})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


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
