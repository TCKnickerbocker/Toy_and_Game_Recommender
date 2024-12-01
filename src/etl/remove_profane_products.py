import os
import snowflake.connector
from dotenv import load_dotenv
from better_profanity import profanity
import time

load_dotenv()

'''
Hard-coded fix:
load_additional_inappropriate_phrases is used because profanity.contains_profanity does not flag certain phrases 
as inappropriate which we deem to be inappropriate for children.
'''
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
        profanity.contains_profanity(text) or 
        phrases_found
    )

def remove_inappropriate_products(conn, source_table, batch_size=1000):
    """
    Efficiently remove products with inappropriate titles or store names.
    
    Args:
        conn (snowflake.connector.connection): Active Snowflake connection.
        source_table (str): Name of the source table.
        batch_size (int): Number of rows to process in each batch.
    
    Returns:
        list: List of productid values for inappropriate products removed.
    """
    try:
        cur = conn.cursor()
        
        fetch_query = f"""
        SELECT productid, title, store 
        FROM {source_table} 
        ORDER BY productid
        """
        cur.execute(fetch_query)
        columns = [desc[0] for desc in cur.description]
        
        product_ids_to_delete = []
        offset = 0
        
        while True:
            # Process data in batches to reduce memory load
            batch_query = f"""
            {fetch_query}
            LIMIT {batch_size}
            OFFSET {offset}
            """
            cur.execute(batch_query)
            
            batch_rows = cur.fetchall()
            if not batch_rows:
                break
            
            # Process batch
            for row in batch_rows:
                row_dict = dict(zip(columns, row))
                
                # Check for inappropriate content
                inappropriate_checks = [
                    is_text_inappropriate(str(row_dict.get('TITLE', ''))),
                    is_text_inappropriate(str(row_dict.get('STORE', '')))
                ]
                
                if any(inappropriate_checks):
                    product_ids_to_delete.append(row_dict['PRODUCTID'])
            
            offset += batch_size
        
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
    # Connect to Snowflake
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA")
    )
    
    try:
        start_time = time.time()
        
        print(f"Loaded {len(ADDITIONAL_INAPPROPRIATE_PHRASES)} additional inappropriate phrases")
        
        # Remove inappropriate products and get their IDs
        removed_product_ids = remove_inappropriate_products(
            conn, 
            source_table='preprocessed_product_info'
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