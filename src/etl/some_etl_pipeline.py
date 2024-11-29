
from etl.configs.spark_config import create_spark_session
from etl.configs.sentiment_analysis import analyze_sentiment
from examples.example_snowflake_read_and_write import write_to_snowflake
import spark

def process_product_names(df):
    """
    Analyze sentiment of product names.
    """
    product_names = [row["product_name"] for row in df.select("product_name").distinct().collect()]
    sentiment_results = analyze_sentiment(product_names)
    
    # Add sentiment results to DataFrame
    sentiment_df = spark.createDataFrame(sentiment_results)
    return df.join(sentiment_df, df.product_name == sentiment_df.text, "left").drop("text")

def etl_pipeline():
    """
    Full ETL pipeline: preprocess, analyze sentiment, and store in Snowflake.
    """
    spark = create_spark_session()
    raw_data_path = "data/raw/kids_toys_reviews.json"
    snowflake_options = {
        "sfURL": "YOUR_ACCOUNT.snowflakecomputing.com",
        "sfDatabase": "YOUR_DATABASE",
        "sfSchema": "YOUR_SCHEMA",
        "sfWarehouse": "YOUR_WAREHOUSE",
        "sfRole": "YOUR_ROLE",
        "sfUser": "YOUR_USERNAME",
        "sfPassword": "YOUR_PASSWORD"
    }

    # Load and preprocess
    df = load_data(spark, raw_data_path)
    cleaned_df = preprocess_reviews(df)

    # Analyze sentiment
    enriched_df = process_product_names(cleaned_df)

    # Save to Snowflake
    write_to_snowflake(enriched_df, "kids_toys_reviews", snowflake_options)

if __name__ == "__main__":
    etl_pipeline()
