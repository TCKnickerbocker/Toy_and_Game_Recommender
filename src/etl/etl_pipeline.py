# Required imports
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import snowflake.connector
from typing import List, Dict

def create_spark_session() -> SparkSession:
    """
    Create and configure Spark session
    """
    return SparkSession.builder \
        .appName("Product Reviews Analysis") \
        .getOrCreate()

def load_data(spark: SparkSession, path: str):
    """
    Load data from JSON file
    """
    return spark.read.json(path)

def preprocess_reviews(df):
    """
    Clean and preprocess the reviews dataframe
    """
    return df.dropDuplicates().na.drop()

def process_product_names(spark: SparkSession, df):
    """
    Analyze sentiment of product names
    """
    product_names = [row["product_name"] for row in df.select("product_name").distinct().collect()]
    
    # Create sentiment results DataFrame directly
    sentiment_results = [(name, analyze_sentiment(name)) for name in product_names]
    sentiment_df = spark.createDataFrame(sentiment_results, ["product_name", "sentiment"])
    
    return df.join(sentiment_df, "product_name", "left")

def write_to_snowflake(df, table_name: str, options: Dict[str, str]):
    """
    Write DataFrame to Snowflake
    """
    df.write \
        .format("snowflake") \
        .options(**options) \
        .option("dbtable", table_name) \
        .mode("overwrite") \
        .save()

def etl_pipeline():
    """
    Full ETL pipeline: preprocess, analyze sentiment, and store in Snowflake
    """
    spark = create_spark_session()
    raw_data_path = "data/raw/kids_toys_reviews.json"
    
    # Configure Snowflake connection with environment variables 
    snowflake_options = {
        "sfURL": "${SNOWFLAKE_URL}",
        "sfDatabase": "${SNOWFLAKE_DATABASE}",
        "sfSchema": "${SNOWFLAKE_SCHEMA}",
        "sfWarehouse": "${SNOWFLAKE_WAREHOUSE}",
        "sfRole": "${SNOWFLAKE_ROLE}",
        "sfUser": "${SNOWFLAKE_USER}",
        "sfPassword": "${SNOWFLAKE_PASSWORD}"
    }

    # Load and preprocess
    df = load_data(spark, raw_data_path)
    cleaned_df = preprocess_reviews(df)

    # Analyze sentiment
    enriched_df = process_product_names(spark, cleaned_df)

    # Save to Snowflake
    write_to_snowflake(enriched_df, "kids_toys_reviews", snowflake_options)

if __name__ == "__main__":
    etl_pipeline()

