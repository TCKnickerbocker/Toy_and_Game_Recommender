# TODO: change create or replace to create if not exists
import os
import snowflake.connector
from dotenv import load_dotenv
import time
import spacy
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

# Load pre-trained sentence transformer & tokenizer
model = SentenceTransformer('all-mpnet-base-v2')
nlp = spacy.load("en_core_web_sm")

def calculate_similarity(text1, text2):
    """
    Calculate cosine similarity between two texts with stopword filtering.
    
    Args:
        text1 (str): First text to compare
        text2 (str): Second text to compare
    
    Returns:
        float: Cosine similarity score
    """
    # Handle None or empty inputs
    if not text1 or not text2:
        return 0.0
    
    # Tokenize
    doc1 = nlp(str(text1))
    doc2 = nlp(str(text2))
    
    # Filter out stopwords & convert to lowercase
    filtered_tokens1 = [token.text.lower() for token in doc1 if not token.is_stop]
    filtered_tokens2 = [token.text.lower() for token in doc2 if not token.is_stop]
    
    # Handle cases with no meaningful tokens
    if not filtered_tokens1 or not filtered_tokens2:
        return 0.0
    
    # Encode texts to vectors
    try:
        embeddings = model.encode([filtered_tokens1, filtered_tokens2])
    
        # Calculate cosine similarity (scipy faster than numpy, scikit for this)
        similarity_score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(min(similarity_score, 1.0))  # Cap at 1.0 for numerical stability
    except Exception:
        return 0.0

def create_similarity_tables(conn):
    """
    Create tables to store different types of product similarities.
    
    Args:
        conn (snowflake.connector.connection): Active Snowflake connection
    """
    cur = conn.cursor()
    
    # Create tables with unique constraint to prevent redundant entries
    create_table_queries = [
        """
        CREATE TABLE IF NOT EXISTS product_title_similarity (
            product1_id VARCHAR(10),
            product2_id VARCHAR(10),
            similarity_score FLOAT(8),
            UNIQUE (product1_id, product2_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS product_details_similarity (
            product1_id VARCHAR(10),
            product2_id VARCHAR(10),
            similarity_score FLOAT(8),
            UNIQUE (product1_id, product2_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS product_store_similarity (
            product1_id VARCHAR(10),
            product2_id VARCHAR(10),
            similarity_score FLOAT(8),
            UNIQUE (product1_id, product2_id)
        )
        """
    ]
    
    for query in create_table_queries:
        cur.execute(query)
    
    conn.commit()
    cur.close()

def generate_product_similarity_matrix(conn, source_table='most_popular_products', batch_size=1000):
    """
    Generate comprehensive similarity matrices for all product pairs.
    
    Args:
        conn (snowflake.connector.connection): Active Snowflake connection
        source_table (str): Name of the source table containing product information
        batch_size (int): Number of products to process in each batch
    """
    try:
        # Create necessary tables
        create_similarity_tables(conn)
        
        cur = conn.cursor()
        
        # Get total count and product IDs to ensure comprehensive coverage
        fetch_ids_query = f"""
        SELECT productid, 
               COALESCE(title, '') AS title, 
               COALESCE(details, '') AS details, 
               COALESCE(store, '') AS store
        FROM {source_table}
        ORDER BY productid
        """
        cur.execute(fetch_ids_query)
        
        # Fetch all products
        all_products = cur.fetchall()
        total_products = len(all_products)
        
        # Prepare similarity insertion cursors
        title_cur = conn.cursor()
        details_cur = conn.cursor()
        store_cur = conn.cursor()
        
        # Track processed pairs to avoid redundant calculations
        processed_pairs = set()
        
        # Generate pairwise similarities
        for i in range(total_products):
            for j in range(i+1, total_products):
                product1_id, title1, details1, store1 = all_products[i]
                product2_id, title2, details2, store2 = all_products[j]
                
                # Ensure consistent pair ordering to prevent duplicates
                pair_key = tuple(sorted([product1_id, product2_id]))
                if pair_key in processed_pairs:
                    continue
                
                # Calculate similarities
                title_sim = calculate_similarity(title1, title2)
                details_sim = calculate_similarity(details1, details2)
                store_sim = calculate_similarity(store1, store2)
                
                # Mark pair as processed
                processed_pairs.add(pair_key)
                
                # Insert ALL similarities, including zero values
                title_cur.execute(
                    "INSERT INTO product_title_similarity (product1_id, product2_id, similarity_score) VALUES (%s, %s, %s)",
                    (product1_id, product2_id, title_sim)
                )
                
                details_cur.execute(
                    "INSERT INTO product_details_similarity (product1_id, product2_id, similarity_score) VALUES (%s, %s, %s)",
                    (product1_id, product2_id, details_sim)
                )
                
                store_cur.execute(
                    "INSERT INTO product_store_similarity (product1_id, product2_id, similarity_score) VALUES (%s, %s, %s)",
                    (product1_id, product2_id, store_sim)
                )
                
                # Periodic commit to manage resources
                if (i * total_products + j) % batch_size == 0:
                    conn.commit()
                    print(f"Processed {i}/{total_products} products")
            print(f"Added all for productid {product1_id}")
        
        # Final commit
        conn.commit()
        
        # Close cursors
        cur.close()
        title_cur.close()
        details_cur.close()
        store_cur.close()
        
        print("Completed comprehensive similarity matrix generation")
    
    except snowflake.connector.Error as e:
        print(f"Snowflake Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")

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
        
        # Generate product similarity matrices
        generate_product_similarity_matrix(conn)
        
        execution_time = time.time() - start_time
        print(f"Total execution time: {execution_time:.2f} seconds")
    
    except Exception as e:
        print(f"Error in main execution: {e}")
    
    finally:
        # Close the connection
        if conn:
            conn.close()

if __name__ == "__main__":
    main()






import os
import snowflake.connector
from dotenv import load_dotenv
import time
import spacy
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import combinations
import threading
from queue import Queue
import logging

load_dotenv()

class ProductSimilarityProcessor:
    def __init__(self, connection_params):
        """
        Initialize the processor with thread-safe components.
        
        :param connection_params: Dictionary of Snowflake connection parameters
        """
        self.connection_params = connection_params
        
        # Thread-local storage for models to avoid race conditions
        self.thread_local = threading.local()
        
        # Logging setup
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Thread-safe queues for batch processing
        self.title_queue = Queue()
        self.details_queue = Queue()
        self.store_queue = Queue()

    def _get_model(self):
        """
        Get thread-local sentence transformer and spacy model.
        """
        if not hasattr(self.thread_local, 'model'):
            self.thread_local.model = SentenceTransformer('all-mpnet-base-v2')
            self.thread_local.nlp = spacy.load("en_core_web_sm")
        return self.thread_local.model, self.thread_local.nlp

    def calculate_similarity(self, text1, text2):
        """
        Thread-safe similarity calculation with improved error handling.
        """
        if not text1 or not text2:
            return 0.0
        
        model, nlp = self._get_model()
        
        try:
            doc1 = nlp(str(text1))
            doc2 = nlp(str(text2))
            
            # Filter out stopwords
            filtered_tokens1 = [token.text.lower() for token in doc1 if not token.is_stop]
            filtered_tokens2 = [token.text.lower() for token in doc2 if not token.is_stop]
            
            if not filtered_tokens1 or not filtered_tokens2:
                return 0.0
            
            # Compute embeddings
            embeddings = model.encode([
                " ".join(filtered_tokens1), 
                " ".join(filtered_tokens2)
            ])
            
            # Compute cosine similarity
            similarity_score = cosine_similarity(
                [embeddings[0]], [embeddings[1]]
            )[0][0]
            
            return float(min(similarity_score, 1.0))
        
        except Exception as e:
            self.logger.error(f"Similarity calculation error: {e}")
            return 0.0

    def create_similarity_tables(self, conn):
        """
        Create tables to store product similarities.
        """
        with conn.cursor() as cur:
            create_table_queries = [
                """
                CREATE OR REPLACE TABLE product_title_similarity (
                    product1_id VARCHAR(10),
                    product2_id VARCHAR(10),
                    similarity_score FLOAT(8),
                    UNIQUE (product1_id, product2_id)
                )
                """,
                """
                CREATE OR REPLACE TABLE product_details_similarity (
                    product1_id VARCHAR(10),
                    product2_id VARCHAR(10),
                    similarity_score FLOAT(8),
                    UNIQUE (product1_id, product2_id)
                )
                """,
                """
                CREATE OR REPLACE TABLE product_store_similarity (
                    product1_id VARCHAR(10),
                    product2_id VARCHAR(10),
                    similarity_score FLOAT(8),
                    UNIQUE (product1_id, product2_id)
                )
                """
            ]
            
            for query in create_table_queries:
                cur.execute(query)
            conn.commit()

    def batch_insert(self, conn, table_name, queue):
        """
        Batch insert from a thread-safe queue.
        
        :param conn: Database connection
        :param table_name: Name of the table to insert into
        :param queue: Queue containing rows to insert
        """
        batch_rows = []
        while not queue.empty():
            try:
                row = queue.get(block=False)
                batch_rows.append(row)
                queue.task_done()
                
                # Insert in batches of 1000
                if len(batch_rows) >= 1000:
                    with conn.cursor() as cur:
                        insert_query = f"""
                        INSERT INTO {table_name} 
                        (product1_id, product2_id, similarity_score) 
                        VALUES (%s, %s, %s)
                        """
                        cur.executemany(insert_query, batch_rows)
                    conn.commit()
                    batch_rows = []
            except Exception as e:
                self.logger.error(f"Batch insert error in {table_name}: {e}")
        
        # Insert any remaining rows
        if batch_rows:
            with conn.cursor() as cur:
                insert_query = f"""
                INSERT INTO {table_name} 
                (product1_id, product2_id, similarity_score) 
                VALUES (%s, %s, %s)
                """
                cur.executemany(insert_query, batch_rows)
            conn.commit()

    def process_product_pair(self, product1, product2):
        """
        Calculate similarities for a product pair and add to queues.
        
        :param product1: First product tuple
        :param product2: Second product tuple
        """
        product1_id, title1, details1, store1 = product1
        product2_id, title2, details2, store2 = product2

        # Calculate similarities
        title_sim = self.calculate_similarity(title1, title2)
        details_sim = self.calculate_similarity(details1, details2)
        store_sim = self.calculate_similarity(store1, store2)

        # Add to thread-safe queues
        self.title_queue.put((product1_id, product2_id, title_sim))
        self.details_queue.put((product1_id, product2_id, details_sim))
        self.store_queue.put((product1_id, product2_id, store_sim))

    def generate_product_similarity_matrix(self, source_table='most_popular_products'):
        """
        Generate comprehensive similarity matrices with advanced parallelism.
        
        :param source_table: Source table name for product data
        """
        # Create a new connection for this method
        with snowflake.connector.connect(**self.connection_params) as conn:
            # Create necessary tables
            self.create_similarity_tables(conn)

            # Fetch product data
            with conn.cursor() as cur:
                fetch_query = f"""
                SELECT productid, 
                       COALESCE(title, '') AS title, 
                       COALESCE(details, '') AS details, 
                       COALESCE(store, '') AS store
                FROM {source_table}
                ORDER BY productid
                """
                cur.execute(fetch_query)
                all_products = cur.fetchall()

            # Generate all product pairs
            product_pairs = list(combinations(all_products, 2))
            total_pairs = len(product_pairs)

            # Process pairs in parallel
            with ThreadPoolExecutor(max_workers=os.cpu_count() or 8) as executor:
                futures = [
                    executor.submit(self.process_product_pair, pair[0], pair[1]) 
                    for pair in product_pairs
                ]

                # Track progress
                for i, future in enumerate(as_completed(futures), 1):
                    future.result()
                    if i % 1000 == 0:
                        self.logger.info(f"Processed {i}/{total_pairs} pairs")

            # Parallel batch inserts
            batch_insert_threads = [
                threading.Thread(target=self.batch_insert, args=(conn, 'product_title_similarity', self.title_queue)),
                threading.Thread(target=self.batch_insert, args=(conn, 'product_details_similarity', self.details_queue)),
                threading.Thread(target=self.batch_insert, args=(conn, 'product_store_similarity', self.store_queue))
            ]

            # Start and join batch insert threads
            for thread in batch_insert_threads:
                thread.start()
            for thread in batch_insert_threads:
                thread.join()

def main():
    # Load connection parameters from environment
    connection_params = {
        'user': os.getenv("SNOWFLAKE_USER"),
        'password': os.getenv("SNOWFLAKE_PASSWORD"),
        'account': os.getenv("SNOWFLAKE_ACCOUNT"),
        'warehouse': os.getenv("SNOWFLAKE_WAREHOUSE"),
        'database': os.getenv("SNOWFLAKE_DATABASE"),
        'schema': os.getenv("SNOWFLAKE_SCHEMA")
    }

    processor = ProductSimilarityProcessor(connection_params)

    start_time = time.time()
    processor.generate_product_similarity_matrix()
    print(f"Total execution time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()