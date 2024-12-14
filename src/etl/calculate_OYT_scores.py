""" Goals;
# Get list of productIDs in reviews_of_most_popular_products
# product_ids[] = select productID from reviews_of_most_popular_products group by reviews_of_most_popular_products order by reviews_of_most_popular_products

# For each product_id in product_ids (mutlithreaded):
# number_of_reviews_for_product = select count(*) from reviews_of_most_popular_products where PRODUCTID = x
# select SENTIMENT, HELPFUL_VOTE from reviews_of_most_popular_products where PRODUCTID = x
# Put SENTIMENT, HELPFUL_VOTE into lists
# score = calculate_OYT_for_product(product_id, review_sentiments, nums_found_helpful, number_of_reviews_for_product)
# Insert (batch insert ?) product_id, score into oyt_scores_of_most_popular_products
"""
# Under 2 minutes to run for 1000 products on 8-core 2023 M3 Mac

import sys
import time
import numpy as np
import snowflake.connector
import concurrent.futures
import os

sys.path.append("./configs")
from etl_configs import CONNECTION_PARAMS


def calculate_OYT_for_product(product_id: str, review_sentiments: list, nums_found_helpful: list, number_of_reviews_for_product: int, base_weight: float = 1) -> float:
    """
    Calculate One You Trust (OYT) score for a product.
    
    Args:
        product_id (str): Unique identifier for the product
        review_sentiments (list): List of sentiment scores for reviews
        nums_found_helpful (list): List of number of helpful votes for corresponding reviews
        number_of_reviews_for_product (int): Total number of reviews for the product
        base_weight (float): Baseline helpfulness weight for reviews with zero helpful votes
    
    Returns:
        float: Calculated OYT score
    """
    try:
        # Normalize helpful votes
        max_helpful = max(nums_found_helpful) if nums_found_helpful else 1
        normalized_helpful = [(h / max_helpful) for h in nums_found_helpful]
        
        # Add baseline weight to normalized helpfulness
        blended_helpfulness = [(helpful + base_weight) / (1 + base_weight) for helpful in normalized_helpful]
        
        # Calculate weighted score
        weighted_scores = [sent * blended for sent, blended in zip(review_sentiments, blended_helpfulness)]
        
        # Return average of weighted scores
        return np.mean(weighted_scores) if weighted_scores else 0.0

    except Exception as e:
        print(f"Error calculating OYT for product {product_id}: {e}")
        return 0.0

def process_product_batch(conn, batch_offset, batch_size):
    """
    Process a batch of products to calculate their OYT scores.
    
    Args:
        conn (snowflake.connector.connection): Snowflake database connection
        batch_offset (int): Starting offset for the batch
        batch_size (int): Number of products to process in this batch
    
    Returns:
        list: Batch of (product_id, oyt_score) tuples
    """
    try:
        cur = conn.cursor()
        
        # Get unique product IDs
        product_query = f"""
        SELECT DISTINCT PRODUCTID 
        FROM reviews_of_most_popular_products
        ORDER BY PRODUCTID
        LIMIT {batch_size}
        OFFSET {batch_offset}
        """
        cur.execute(product_query)
        product_ids = [row[0] for row in cur.fetchall()]
        
        oyt_scores = []
        
        for product_id in product_ids:
            # Get review details for this product
            review_query = f"""
            SELECT sentiment_score, HELPFUL_VOTE 
            FROM review_sentiments_most_popular_products r1
            JOIN reviews_of_most_popular_products r2 ON r1.product_id = r2.PRODUCTID AND r1.user_id = r2.USER_ID
            WHERE r2.PRODUCTID = '{product_id}'
            """
            cur.execute(review_query)
            
            # Extract sentiment scores and helpful votes
            review_data = cur.fetchall()
            print(f"Got review data for batch with offset: {batch_offset}")
            if review_data:
                review_sentiments = [row[0] for row in review_data]
                nums_found_helpful = [row[1] or 0 for row in review_data]
                
                # Calculate OYT score
                oyt_score = calculate_OYT_for_product(
                    product_id, 
                    review_sentiments, 
                    nums_found_helpful, 
                    len(review_data)
                )
                
                oyt_scores.append((product_id, oyt_score))
        
        cur.close()
        return oyt_scores
    
    except snowflake.connector.Error as e:
        print(f"Snowflake Error in batch processing: {e}")
        return []
    except Exception as e:
        print(f"Unexpected Error in batch processing: {e}")
        return []

def calculate_OYT_scores(conn, batch_size=500, max_workers=8):
    """
    Calculate OYT scores for all products using multithreaded processing.
    
    Args:
        conn (snowflake.connector.connection): Snowflake database connection
        batch_size (int): Number of products to process in each batch
        max_workers (int): Maximum number of concurrent threads
    
    Returns:
        int: Total number of products processed
    """
    try:
        cur = conn.cursor()
        
        # Get total number of unique products
        count_query = "SELECT COUNT(DISTINCT PRODUCTID) FROM reviews_of_most_popular_products"
        cur.execute(count_query)
        total_products = cur.fetchone()[0]
        
        oyt_updates = []
        
        # Use ThreadPoolExecutor for concurrent batch processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create futures for each batch
            futures = [
                executor.submit(process_product_batch, conn, offset, batch_size)
                for offset in range(0, total_products, batch_size)
            ]
            
            # Collect results from futures
            for future in concurrent.futures.as_completed(futures):
                oyt_updates.extend(future.result())
        
        # Bulk update OYT scores
        if oyt_updates:
            # Create table for bulk update
            cur.execute("""
                CREATE TABLE IF NOT EXISTS oyt_scores_of_most_popular_products (
                    product_id VARCHAR(10),
                    oyt_score FLOAT(8)
                )
            """)
            
            # Insert updates into table
            cur.executemany(
                "INSERT INTO oyt_scores_of_most_popular_products (product_id, oyt_score) VALUES (%s, %s)",
                oyt_updates
            )
            
            conn.commit()
            print(f"Updated OYT scores for {len(oyt_updates)} products.")
            return len(oyt_updates)
        
        print("No products found to update.")
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
        
        # Calculate OYT scores
        total_products_processed = calculate_OYT_scores(
            conn, 
            batch_size=500,   
            max_workers=os.cpu_count() - 1 or 7
        )
        
        execution_time = time.time() - start_time
        print(f"Total execution time: {execution_time:.2f} seconds")
        print(f"Total products processed: {total_products_processed}")
    
    except Exception as e:
        print(f"Error in main execution: {e}")
    
    finally:
        # Close the connection
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
