# TODO: Load dotenv, fix configs in this file
import snowflake.connector
from pyspark.sql import DataFrame
from spark_config import create_spark_session

def get_snowflake_connection():
    """
    Establish a connection to Snowflake.
    """
    conn = snowflake.connector.connect(
        user="YOUR_USERNAME",
        password="YOUR_PASSWORD",
        account="YOUR_ACCOUNT"
    )
    return conn

def write_to_snowflake(df: DataFrame, table_name: str, snowflake_options: dict):
    """
    Write a Spark DataFrame to a Snowflake table.
    """
    df.write \
        .format("snowflake") \
        .options(**snowflake_options) \
        .option("dbtable", table_name) \
        .mode("overwrite") \
        .save()

if __name__ == "__main__":
    # Example usage (assumes Spark DataFrame `cleaned_df` is available)
    snowflake_options = {
        "sfURL": "YOUR_ACCOUNT.snowflakecomputing.com",
        "sfDatabase": "YOUR_DATABASE",
        "sfSchema": "YOUR_SCHEMA",
        "sfWarehouse": "YOUR_WAREHOUSE",
        "sfRole": "YOUR_ROLE",
        "sfUser": "YOUR_USERNAME",
        "sfPassword": "YOUR_PASSWORD"
    }
    
    # Example DataFrame write
    spark = create_spark_session()
    example_df = spark.createDataFrame([("Toy A", 4.5), ("Toy B", 3.0)], ["product_name", "rating"])
    write_to_snowflake(example_df, "toy_ratings", snowflake_options)
