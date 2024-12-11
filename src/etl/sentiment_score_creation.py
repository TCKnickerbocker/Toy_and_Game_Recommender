# ~2.5 hours for 85k reviews on 8-core 2023 M3 Mac
# TODO: Add safe retry mechanisms for connection to avoid timeouts halting all execution
import sys
import time
import numpy as np
import snowflake.connector
import concurrent.futures
import os

sys.path.append("./configs")
from etl_configs import CONNECTION_PARAMS

from transformers import AutoModelForSequenceClassification
from transformers import AutoTokenizer, AutoConfig
from scipy.special import softmax

# Initialize sentiment analysis model
MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
tokenizer = AutoTokenizer.from_pretrained(MODEL)
config = AutoConfig.from_pretrained(MODEL)
model = AutoModelForSequenceClassification.from_pretrained(MODEL)


def calculate_sentiment(text):
    """
    Calculate sentiment score for a given text.
    
    Args:
        text (str): Review text to analyze.
    
    Returns:
        float: Sentiment score (-1 to 1, where -1 is most negative, 1 is most positive)
    """
    if not isinstance(text, str) or len(text.strip()) == 0:
        return 0.0
    
    try:
        # Tokenize input
        encoded_input = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
        
        # Get model output
        output = model(**encoded_input)
        scores = output[0][0].detach().numpy()
        scores = softmax(scores)
        
        # Calculate weighted sentiment score
        # Negative: config.id2label[0], Neutral: config.id2label[1], Positive: config.id2label[2]
        sentiment_score = (
            -1 * scores[0] +  # Negative
            0.5 * scores[1] +   # Neutral 
            # ^adding (albeit by a somewhat arbitrary value) because some users leave informative reviews, even when they enjoyed a product
            1 * scores[2]     # Positive
        )
        
        return float(np.round(sentiment_score, 8))
    
    except Exception as e:
        print(f"Error calculating sentiment for text: {e}")
        return 0.0

def process_batch(conn, batch_offset, batch_size):
    """
    Process a batch of reviews and calculate their sentiment scores.
    
    Args:
        conn (snowflake.connector.connection): Snowflake database connection
        batch_offset (int): Starting offset for the batch
        batch_size (int): Number of reviews to process in this batch
    
    Returns:
        list: Batch of (review_id, sentiment_score) tuples
    """
    try:
        cur = conn.cursor()
        
        # Fetch batch of reviews that have not been processed before
        batch_query = f"""
        SELECT PRODUCTID, USER_ID, TITLE, REVIEW_TEXT 
        FROM reviews_of_most_popular_products
        WHERE (PRODUCTID, USER_ID) NOT IN (
            SELECT product_id, user_id 
            FROM review_sentiments_most_popular_products
        )
        ORDER BY PRODUCTID
        LIMIT {batch_size}
        OFFSET {batch_offset}
        """
        cur.execute(batch_query)
        
        # Calculate sentiment for each review
        sentiment_updates = []
        for row in cur.fetchall():
            product_id, user_id, title, review_text = row
            sentiment_score = calculate_sentiment(title + "\n\n" + review_text)
            sentiment_updates.append((product_id, user_id, sentiment_score))
        
        cur.close()
        return sentiment_updates
    
    except snowflake.connector.Error as e:
        print(f"Snowflake Error in batch processing: {e}")
        return []
    except Exception as e:
        print(f"Unexpected Error in batch processing: {e}")
        return []

def update_sentiment_scores(conn, batch_size=500, max_workers=8):
    """
    Update sentiment scores for all reviews using multithreaded processing.
    
    Args:
        conn (snowflake.connector.connection): Snowflake database connection
        batch_size (int): Number of reviews to process in each batch
        max_workers (int): Maximum number of concurrent threads
    
    Returns:
        int: Total number of reviews processed
    """
    try:
        cur = conn.cursor()
        
        # Get total number of unprocessed reviews
        count_query = """
        SELECT COUNT(*) 
        FROM reviews_of_most_popular_products
        WHERE (PRODUCTID, USER_ID) NOT IN (
            SELECT product_id, user_id 
            FROM review_sentiments_most_popular_products
        )
        """
        cur.execute(count_query)
        total_reviews = cur.fetchone()[0]
        
        sentiment_updates = []
        
        # Use ThreadPoolExecutor for concurrent batch processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create futures for each batch
            futures = [
                executor.submit(process_batch, conn, offset, batch_size)
                for offset in range(0, total_reviews, batch_size)
            ]
            
            # Collect results from futures
            for future in concurrent.futures.as_completed(futures):
                sentiment_updates.extend(future.result())
        
        # Bulk update sentiment scores
        if sentiment_updates:
            # Create table for bulk update if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS review_sentiments_most_popular_products (
                    product_id VARCHAR(10),
                    user_id VARCHAR(50),
                    sentiment FLOAT(8),
                    PRIMARY KEY (product_id, user_id)
                )
            """)
            
            # Insert updates into table, ignoring duplicates
            cur.executemany(
                "INSERT INTO review_sentiments_most_popular_products (product_id, user_id, sentiment) VALUES (%s, %s, %s)",
                sentiment_updates
            )
            
            conn.commit()
            print(f"Updated sentiment values for {len(sentiment_updates)} reviews.")
            return len(sentiment_updates)
        
        print("No unprocessed reviews found.")
        return 0
    
    except snowflake.connector.Error as e:
        print(f"Snowflake Error: {e}")
        return 0
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return 0
    finally:
        if 'cur' in locals() and cur:
            cur.close()

def main():
    # Establish Snowflake connection
    conn = snowflake.connector.connect(**CONNECTION_PARAMS)
    
    try:
        start_time = time.time()
        
        # Update sentiment scores
        total_processed = update_sentiment_scores(
            conn, 
            batch_size=500,   
            max_workers=os.cpu_count() - 1 or 7
        )
        
        execution_time = time.time() - start_time
        print(f"Total execution time: {execution_time:.2f} seconds")
        print(f"Total reviews processed: {total_processed}")
    
    except Exception as e:
        print(f"Error in main execution: {e}")
    
    finally:
        # Close the connection
        if conn:
            conn.close()

if __name__ == "__main__":
    main()