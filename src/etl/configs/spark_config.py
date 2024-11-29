from pyspark.sql import SparkSession

def create_spark_session(app_name="Amazon Product Recommender Spark Session"):
    """
    Creates and configures a Spark session.
    """
    return SparkSession.builder.appName('abc').getOrCreate()
    return (
        SparkSession.builder
        .appName(app_name)
        .config("spark.jars.packages", "net.snowflake:snowflake-jdbc:3.8.0,net.snowflake:spark-snowflake_2.11:2.4.14-spark_2.4") \
        .config("spark.executor.memory", "2g")
        .config("spark.driver.memory", "2g")
        .config("spark.executor.cores", "2")
        .config("spark.sql.shuffle.partitions", "200")
        .getOrCreate()
    )
