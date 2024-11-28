from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, udf
from pyspark.sql.types import StringType
from azure.storage.blob import BlobServiceClient
import json
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Initialize Spark session
spark = SparkSession.builder \
    .appName("AmazonReviewsDataIngestion") \
    .config("spark.jars.packages", "net.snowflake:spark-snowflake_2.12:2.10.0-spark_3.0") \
    .getOrCreate()

# Initialize Sentiment Analysis
nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

# Azure Blob Storage Configuration
azure_storage_account_name = "your_storage_account_name"
azure_storage_account_key = "your_storage_account_key"
azure_container_name = "your_container_name"
azure_blob_path = "amazon_reviews_data.csv"  # Path to the dataset in Azure Blob Storage

# Snowflake connection options
sfOptions = {
    "sfURL" : "your_snowflake_account_url",
    "sfDatabase" : "your_snowflake_database",
    "sfSchema" : "your_snowflake_schema",
    "sfWarehouse" : "your_snowflake_warehouse",
    "sfRole" : "your_snowflake_role",
    "sfUser" : "your_snowflake_user",
    "sfPassword" : "your_snowflake_password"
}

# Define UDF for Sentiment Analysis
def analyze_sentiment(text):
    if text:
        sentiment = sia.polarity_scores(text)
        return sentiment['compound']
    return 0.0

sentiment_udf = udf(analyze_sentiment, StringType())

# Step 1: Read raw data from Azure Blob Storage
df = spark.read.option("header", "true").csv(f"wasbs://{azure_container_name}@{azure_storage_account_name}.blob.core.windows.net/{azure_blob_path}")

# Step 2: Preprocessing
# Example preprocessing: Extract important columns, handle missing data, and run sentiment analysis on the review text

df = df.select("reviewText", "productId", "reviewerID", "overall") \
    .withColumn("sentiment", sentiment_udf(col("reviewText"))) \
    .na.drop(subset=["reviewText", "productId", "reviewerID", "overall"])

# Step 3: Write data to Snowflake
df.write \
    .format("snowflake") \
    .options(**sfOptions) \
    .option("dbtable", "processed_amazon_reviews") \
    .mode("overwrite") \
    .save()

# Step 4: Verify the data is loaded into Snowflake
snowflake_df = spark.read \
    .format("snowflake") \
    .options(**sfOptions) \
    .option("dbtable", "processed_amazon_reviews") \
    .load()

snowflake_df.show(5)

# Stop Spark session
spark.stop()
