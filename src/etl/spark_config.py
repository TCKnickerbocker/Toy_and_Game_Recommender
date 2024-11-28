from pyspark.sql import SparkSession

def create_spark_session(app_name="Amazon Product Recommender Spark Session"):
    """
    Creates and configures a Spark session.
    """
    return (
        SparkSession.builder
        .appName(app_name)
        .config("spark.executor.memory", "2g")
        .config("spark.driver.memory", "2g")
        .config("spark.executor.cores", "2")
        .config("spark.sql.shuffle.partitions", "200")
        .getOrCreate()
    )
