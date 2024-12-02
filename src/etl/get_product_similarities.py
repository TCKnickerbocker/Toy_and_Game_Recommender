# TODO: Change create or replace table to create table if not exists
# For 1000 items -> 1000c2 calculations ~ 500,000. 8 cores, takes ~4.7 hours locally

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
        Initialize the processor with logging and thread-safe components.
        
        :param connection_params: Dictionary of Snowflake connection parameters
        """
        self.connection_params = connection_params
        
        # Thread-local storage for models to avoid race conditions
        self.thread_local = threading.local()
        
        # Logging setup
        logging.basicConfig(
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Queues for batch processing
        self.title_queue = Queue()

    def _get_model(self):
        """
        Get thread-local sentence transformer and spaCy model.
        """
        if not hasattr(self.thread_local, 'model'):
            self.thread_local.model = SentenceTransformer('all-mpnet-base-v2')
            self.thread_local.nlp = spacy.load("en_core_web_sm")
        return self.thread_local.model, self.thread_local.nlp

    def _preprocess_text(self, text, nlp):
        """
        Efficient text preprocessing (tokenization and lemmatization).
        """
        doc = nlp(str(text).lower())
        # Use list comprehension for filtering stopwords and non-alphabetic tokens
        return [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]

    def calculate_similarity(self, text1, text2):
        """
        Optimized thread-safe similarity calculation with improved performance.
        """
        # Early exit
        if not text1 or not text2:
            return 0.0
        
        # Use thread-local models
        model, nlp = self._get_model()

        try:
            # Preprocess text, return if short titles
            filtered_tokens1 = self._preprocess_text(text1, nlp)
            filtered_tokens2 = self._preprocess_text(text2, nlp)

            # Quick exit if no meaningful tokens
            if len(filtered_tokens1) < 2 or len(filtered_tokens2) < 2:
                return 0.0
            
            # Batch encode for efficiency
            embeddings = model.encode([
                " ".join(filtered_tokens1),
                " ".join(filtered_tokens2)
            ], show_progress_bar=False)
            
            # Compute cosine similarity
            similarity_score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(min(max(round(similarity_score, 8), 0.0), 1.0))
        
        except Exception as e:
            self.logger.error(f"Similarity calculation error for texts '{text1[:50]}' and '{text2[:50]}': {e}")
            return 0.0

    def create_similarity_tables(self, conn):
        """
        Create tables to store product similarities.
        """
        with conn.cursor() as cur:
            # Only create table for title similarity
            create_table_queries = [
                """
                CREATE OR REPLACE TABLE product_title_similarity (
                    product1_id VARCHAR(10),
                    product2_id VARCHAR(10),
                    similarity_score FLOAT(12),
                    UNIQUE (product1_id, product2_id)
                );

                CREATE INDEX idx_similarity_score_product1 ON product_title_similarity (product1_id, similarity_score DESC);
                CREATE INDEX idx_similarity_score_product2 ON product_title_similarity (product2_id, similarity_score DESC);

                """
                # Commented out details and store similarity tables
                # """
                # CREATE OR REPLACE TABLE product_details_similarity (
                #     product1_id VARCHAR(10),
                #     product2_id VARCHAR(10),
                #     similarity_score FLOAT(12),
                #     UNIQUE (product1_id, product2_id)
                # );
                
                # CREATE INDEX idx_similarity_score_product1 ON product_title_similarity (product1_id, similarity_score DESC);
                # CREATE INDEX idx_similarity_score_product2 ON product_title_similarity (product2_id, similarity_score DESC);

                # """,
                # """
                # CREATE OR REPLACE TABLE product_store_similarity (
                #     product1_id VARCHAR(10),
                #     product2_id VARCHAR(10),
                #     similarity_score FLOAT(12),
                #     UNIQUE (product1_id, product2_id)
                # );
                
                # CREATE INDEX idx_similarity_score_product1 ON product_title_similarity (product1_id, similarity_score DESC);
                # CREATE INDEX idx_similarity_score_product2 ON product_title_similarity (product2_id, similarity_score DESC);

                # """
            ]
            
            for query in create_table_queries:
                cur.execute(query)
            conn.commit()

    def batch_insert(self, conn, table_name, queue, replace=False):
        start = time.time()
        max_retries = 3
        for attempt in range(max_retries):
            try:
                batch_rows = []
                processed_rows = 0

                while not queue.empty():
                    try:
                        row = queue.get(block=False)
                        # Ensure similarity_score is converted to float
                        row = (row[0], row[1], float(row[2]))
                        batch_rows.append(row)
                        processed_rows += 1
                        queue.task_done()

                        if len(batch_rows) >= 1000:
                            with conn.cursor() as cur:
                                if replace:
                                    # Use MERGE (old method)
                                    insert_query = f"""
                                    MERGE INTO {table_name} AS target
                                    USING (
                                        SELECT %s AS product1_id, 
                                            %s AS product2_id, 
                                            %s AS similarity_score
                                    ) AS source
                                    ON (target.product1_id = source.product1_id 
                                        AND target.product2_id = source.product2_id)
                                    WHEN MATCHED THEN 
                                        UPDATE SET similarity_score = source.similarity_score
                                    WHEN NOT MATCHED THEN 
                                        INSERT (product1_id, product2_id, similarity_score)
                                        VALUES (source.product1_id, source.product2_id, source.similarity_score)
                                    """
                                    cur.executemany(insert_query, batch_rows)
                                else:
                                    # Use Bulk Insert (no matching)
                                    insert_query = f"""
                                    INSERT INTO {table_name} (product1_id, product2_id, similarity_score)
                                    VALUES (%s, %s, %s)
                                    """
                                    cur.executemany(insert_query, batch_rows)

                            conn.commit()
                            self.logger.info(f"Inserted batch of {len(batch_rows)} rows")
                            batch_rows = []

                    except queue.Empty:
                        break  # Exit inner loop if queue becomes empty

                # Insert any remaining rows
                if batch_rows:
                    with conn.cursor() as cur:
                        if replace:
                            # Use MERGE (old method)
                            insert_query = f"""
                            MERGE INTO {table_name} AS target
                            USING (
                                SELECT %s AS product1_id, 
                                    %s AS product2_id, 
                                    %s AS similarity_score
                            ) AS source
                            ON (target.product1_id = source.product1_id 
                                AND target.product2_id = source.product2_id)
                            WHEN MATCHED THEN 
                                UPDATE SET similarity_score = source.similarity_score
                            WHEN NOT MATCHED THEN 
                                INSERT (product1_id, product2_id, similarity_score)
                                VALUES (source.product1_id, source.product2_id, source.similarity_score)
                            """
                            cur.executemany(insert_query, batch_rows)
                        else:
                            # Use Bulk Insert (no matching)
                            insert_query = f"""
                            INSERT INTO {table_name} (product1_id, product2_id, similarity_score)
                            VALUES (%s, %s, %s)
                            """
                            cur.executemany(insert_query, batch_rows)

                    conn.commit()
                    self.logger.info(f"Inserted final batch of {len(batch_rows)} rows")

                self.logger.info(f"Total rows processed in this batch insert: {processed_rows}")
                end = time.time()
                print(f"Batch insert took {end - start} seconds")
                break  # Success, exit the retry loop

            except Exception as e:
                self.logger.error(
                    f"Batch insert attempt {attempt + 1} failed: {e}", exc_info=True
                )
                if attempt < max_retries - 1:
                    # Recreate the connection
                    conn = snowflake.connector.connect(**self.connection_params)
                    self.logger.warning(f"Reconnection attempt {attempt + 1}")
                else:
                    self.logger.error("Failed to reconnect after maximum retries")
                    raise


    def process_product_pair(self, product1, product2):
        """
        Calculate similarities for a product pair and add to queues.
        
        :param product1: First product tuple
        :param product2: Second product tuple
        """
        # Adjusted to only process title
        product1_id, title1 = product1
        product2_id, title2 = product2

        # Calculate only title similarity
        title_sim = self.calculate_similarity(title1, title2)

        # Add only title similarity to queue
        self.title_queue.put((product1_id, product2_id, title_sim))

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
                FROM {source_table}
                ORDER BY productid
                limit 10
                """
                cur.execute(fetch_query)
                all_products = cur.fetchall()

            # Generate all product pairs
            product_pairs = list(combinations(all_products, 2))
            total_pairs = len(product_pairs)

            # Process pairs in parallel
            with ThreadPoolExecutor(max_workers=os.cpu_count() or 8) as executor:  # Avoid overheating on local machine
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
            # Only insert title similarity
            batch_insert_threads = [
                threading.Thread(target=self.batch_insert, args=(conn, 'product_title_similarity', self.title_queue))
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
        'schema': os.getenv("SNOWFLAKE_SCHEMA"),
    }

    processor = ProductSimilarityProcessor(connection_params)

    start_time = time.time()
    processor.generate_product_similarity_matrix()
    print(f"Total execution time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()