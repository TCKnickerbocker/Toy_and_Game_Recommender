# TODO: Replace with our actual model logic
from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALS
from pyspark.ml.feature import CountVectorizer, StringIndexer
from pyspark.ml.linalg import Vectors
from pyspark.sql.functions import col, explode

def train_collaborative_filtering_model(ratings_df):
    """
    Train a collaborative filtering model using Alternating Least Squares (ALS).
    """
    als = ALS(
        userCol="user_id",
        itemCol="product_id",
        ratingCol="rating",
        rank=10,
        maxIter=10,
        regParam=0.1
    )
    model = als.fit(ratings_df)
    return model

def train_content_based_model(products_df, reviews_df):
    """
    Train a content-based recommendation model using product names and review text.
    """
    # Combine product name and review text into a single column
    reviews_df = reviews_df.withColumn("text_data", col("product_name") + " " + col("cleaned_review"))
    
    # Vectorize the text data
    cv = CountVectorizer(inputCol="text_data", outputCol="features")
    vectorized_model = cv.fit(reviews_df)
    vectorized_df = vectorized_model.transform(reviews_df)
    return vectorized_model, vectorized_df

def generate_dummy_data(spark):
    """
    Create dummy data for collaborative filtering and content-based models.
    """
    ratings_data = [
        (1, 101, 5.0), (1, 102, 3.0), (2, 101, 4.0), (2, 103, 2.0), (3, 102, 4.0)
    ]
    products_data = [
        (101, "Magic Puzzle"), (102, "Smart Robot"), (103, "Wooden Blocks")
    ]
    reviews_data = [
        (1, 101, "Amazing puzzle for kids!", 5),
        (1, 102, "Good robot but overpriced.", 3),
        (2, 103, "Not engaging enough for kids.", 2)
    ]
    
    ratings_df = spark.createDataFrame(ratings_data, ["user_id", "product_id", "rating"])
    products_df = spark.createDataFrame(products_data, ["product_id", "product_name"])
    reviews_df = spark.createDataFrame(reviews_data, ["user_id", "product_id", "reviewText", "rating"])
    
    return ratings_df, products_df, reviews_df

if __name__ == "__main__":
    spark = SparkSession.builder.appName("AmazonRecommender").getOrCreate()
    
    # Generate dummy data
    ratings_df, products_df, reviews_df = generate_dummy_data(spark)
    
    # Train collaborative filtering model
    cf_model = train_collaborative_filtering_model(ratings_df)
    
    # Train content-based model
    cb_model, vectorized_reviews = train_content_based_model(products_df, reviews_df)
    
    # Generate sample recommendations
    user_recommendations = cf_model.recommendForAllUsers(3)
    user_recommendations.show()
    
    # Save models to disk (placeholder)
    cf_model.write().overwrite().save("models/collaborative_filtering")
    vectorized_reviews.write.mode("overwrite").parquet("models/content_based_reviews.parquet")
