import snowflake.connector
from dotenv import load_dotenv
from better_profanity.profanity import contains_profanity as library_profanity_check
import time
import sys
import concurrent.futures
sys.path.append("./configs")
import etl_configs

def load_additional_inappropriate_phrases(filename='inappropriate_phrases.txt'):
    """
    Load additional inappropriate phrases from a file.
    
    Args:
        filename (str): Path to the file containing inappropriate phrases.
    
    Returns:
        set: A set of additional inappropriate phrases.
    """
    try:
        with open(filename, 'r') as f:
            # Read lines, strip whitespace, convert to lowercase
            additional_phrases = {phrase.strip().lower() for phrase in f.readlines() if phrase.strip()}
        return additional_phrases
    except FileNotFoundError:
        print(f"Warning: {filename} not found. No additional phrases loaded.")
        return set()
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return set()

ADDITIONAL_INAPPROPRIATE_PHRASES = load_additional_inappropriate_phrases()

def is_text_inappropriate(text):
    """
    Efficiently check if text contains profanity or additional inappropriate phrases.
    
    Args:
        text (str): Text to check for inappropriate content.
    
    Returns:
        bool: True if text contains profanity or inappropriate phrases, False otherwise.
    """
    if not isinstance(text, str):
        return False
    
    # Convert text to lowercase for comparison
    lower_text = text.lower()

    # Check for inappropriate phrases
    phrases_found = any(
        phrase in lower_text 
        for phrase in ADDITIONAL_INAPPROPRIATE_PHRASES
    )

    # Combine with existing profanity check
    return (
        phrases_found or 
        library_profanity_check(text)
    )

def process_batch(conn, source_table, offset, batch_size):
    """
    Process a specific batch of products for inappropriate content.
    
    Args:
        conn (snowflake.connector.connection): Active Snowflake connection.
        source_table (str): Name of the source table.
        offset (int): Starting offset for the batch.
        batch_size (int): Number of rows to process in this batch.
    
    Returns:
        list: List of productid values for inappropriate products in this batch.
    """
    try:
        cur = conn.cursor()
        
        batch_query = f"""
        SELECT productid, title, store, original_description, original_features 
        FROM {source_table} 
        ORDER BY productid
        LIMIT {batch_size}
        OFFSET {offset}
        """
        cur.execute(batch_query)
        columns = [desc[0] for desc in cur.description]
        
        product_ids_to_delete = []
        
        # Process batch
        for row in cur.fetchall():
            row_dict = dict(zip(columns, row))
            
            # Check delete product if inappropriate           
            if is_text_inappropriate(str(row_dict)):
                product_ids_to_delete.append(row_dict['PRODUCTID'])
        
        cur.close()
        return product_ids_to_delete
    
    except snowflake.connector.Error as e:
        print(f"Snowflake Error in batch processing: {e}")
        return []
    except Exception as e:
        print(f"Unexpected Error in batch processing: {e}")
        return []

def remove_inappropriate_products(conn, source_table, batch_size=1000, max_workers=8):
    """
    Efficiently remove products with inappropriate titles or store names using multithreading.
    
    Args:
        conn (snowflake.connector.connection): Active Snowflake connection.
        source_table (str): Name of the source table.
        batch_size (int): Number of rows to process in each batch.
        max_workers (int): Maximum number of concurrent threads.
    
    Returns:
        list: List of productid values for inappropriate products removed.
    """
    try:
        cur = conn.cursor()
        
        # Get total number of rows
        count_query = f"SELECT COUNT(*) FROM {source_table}"
        cur.execute(count_query)
        total_rows = cur.fetchone()[0]
        
        product_ids_to_delete = []
        
        # Use ThreadPoolExecutor for concurrent batch processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create futures for each batch
            futures = [
                executor.submit(process_batch, conn, source_table, offset, batch_size)
                for offset in range(0, total_rows, batch_size)
            ]
            
            # Collect results from futures
            for future in concurrent.futures.as_completed(futures):
                product_ids_to_delete.extend(future.result())
        
        # Bulk delete inappropriate products
        if product_ids_to_delete:
            # Optimize deletion by chunking large delete operations
            chunk_size = 500
            for i in range(0, len(product_ids_to_delete), chunk_size):
                chunk = product_ids_to_delete[i:i+chunk_size]
                ids_str = ', '.join(f"'{id}'" for id in chunk)
                
                delete_query = f"""
                DELETE FROM {source_table}
                WHERE productid IN ({ids_str})
                """
                cur.execute(delete_query)
            
            conn.commit()
            print(f"Removed {len(product_ids_to_delete)} inappropriate product entries.")
            return product_ids_to_delete
        
        print("No inappropriate products found.")
        return []
    
    except snowflake.connector.Error as e:
        print(f"Snowflake Error: {e}")
        return []
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return []
    finally:
        if 'cur' in locals() and cur:
            cur.close()

def main():
    conn = snowflake.connector.connect(etl_configs.CONNECTION_PARAMS)
    
    try:
        start_time = time.time()
        print(f"Loaded {len(ADDITIONAL_INAPPROPRIATE_PHRASES)} additional inappropriate phrases")
        
        # Remove inappropriate products and get their IDs
        removed_product_ids = remove_inappropriate_products(
            conn, 
            source_table='preprocessed_product_info',
            batch_size=1000,  # Adjust batch size as needed
            max_workers=8     # Adjust number of workers based on your system
        )
        
        execution_time = time.time() - start_time
        print(f"Total execution time: {execution_time:.2f} seconds")
        print(removed_product_ids)
        if removed_product_ids:
            print(f"Total inappropriate product IDs: {len(removed_product_ids)}")
    
    except Exception as e:
        print(f"Error in main execution: {e}")
    
    finally:
        # Close the connection
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
