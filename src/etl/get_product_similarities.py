import os
import json
import snowflake.connector
from dotenv import load_dotenv
import time
import argparse
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
        self.embeddings_cache = {}
        self.texts_queue = Queue()

        # Logging setup
        logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def load_embeddings(self, embeddings_filepath):
        """
        Load embeddings from a JSON file into memory.
        
        :param embeddings_filepath: Path to the embeddings file
        """
        try:
            with open(embeddings_filepath, 'r') as f:
                self.embeddings_cache = json.load(f)
            self.logger.info(f"Loaded embeddings from {embeddings_filepath}")
        except Exception as e:
            self.logger.error(f"Error loading embeddings from {embeddings_filepath}: {e}")
            raise

    def calculate_similarity(self, product1_id, product2_id):
        """
        Calculate cosine similarity between two product embeddings.
        
        :param product1_id: ID of the first product
        :param product2_id: ID of the second product
        :return: similarity score (float)
        """
        if product1_id not in self.embeddings_cache or product2_id not in self.embeddings_cache:
            return 0.0

        embedding1 = self.embeddings_cache[product1_id]
        embedding2 = self.embeddings_cache[product2_id]

        # Compute cosine similarity between embeddings
        similarity_score = cosine_similarity([embedding1], [embedding2])[0][0]
        return float(min(max(round(similarity_score, 8), 0.0), 1.0))

    def create_similarity_tables(self, conn, table_name):
        """
        Create tables to store product similarities.
        
        :param conn: Snowflake connection
        :param table_name: Name of the output similarity table
        """
        with conn.cursor() as cur:
            create_table_query = f"""
                CREATE OR REPLACE TABLE {table_name} (
                    product1_id VARCHAR(10),
                    product2_id VARCHAR(10),
                    similarity_score FLOAT(12),
                    UNIQUE (product1_id, product2_id)
                );
            """
            cur.execute(create_table_query)
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
                                    insert_query = f"""
                                    INSERT INTO {table_name} (product1_id, product2_id, similarity_score)
                                    VALUES (%s, %s, %s)
                                    """
                                    cur.executemany(insert_query, batch_rows)

                            conn.commit()
                            self.logger.info(f"Inserted batch of {len(batch_rows)} rows")
                            batch_rows = []

                    except queue.Empty:
                        break

                if batch_rows:
                    with conn.cursor() as cur:
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
                break

            except Exception as e:
                self.logger.error(f"Batch insert attempt {attempt + 1} failed: {e}", exc_info=True)
                if attempt < max_retries - 1:
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
        product1_id, text1 = product1
        product2_id, text2 = product2

        # Calculate similarity between product embeddings
        similarity_score = self.calculate_similarity(product1_id, product2_id)

        # Add similarity to queue
        self.texts_queue.put((product1_id, product2_id, similarity_score))

    def generate_product_similarity_matrix(
        self, 
        embeddings_filepath, 
        source_table, 
        target_column, 
        output_table
    ):
        """
        Generate similarity matrix by processing all product pairs and storing them in Snowflake.
        
        :param embeddings_filepath: Path to embeddings JSON file
        :param source_table: Source table name for product data
        :param target_column: Column to use for text similarity
        :param output_table: Name of the output similarity table
        """
        # Load embeddings from file
        self.load_embeddings(embeddings_filepath)

        with snowflake.connector.connect(**self.connection_params) as conn:
            # Create output similarity table
            self.create_similarity_tables(conn, output_table)

            with conn.cursor() as cur:
                fetch_query = f"""
                SELECT productid, {target_column}
                FROM {source_table}
                ORDER BY productid
                """
                cur.execute(fetch_query)
                all_products = cur.fetchall()

            product_pairs = list(combinations(all_products, 2))
            total_pairs = len(product_pairs)

            with ThreadPoolExecutor(max_workers=os.cpu_count() or 8) as executor:
                futures = [
                    executor.submit(self.process_product_pair, pair[0], pair[1]) 
                    for pair in product_pairs
                ]

                for i, future in enumerate(as_completed(futures), 1):
                    future.result()
                    if i % 1000 == 0:
                        self.logger.info(f"Processed {i}/{total_pairs} pairs")

            # Parallel batch insert
            batch_insert_threads = [
                threading.Thread(
                    target=self.batch_insert, 
                    args=(conn, output_table, self.texts_queue)
                )
            ]

            for thread in batch_insert_threads:
                thread.start()
            for thread in batch_insert_threads:
                thread.join()


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Product Similarity Processor")
    
    # Define command-line arguments with default values
    parser.add_argument(
        "--source-table", 
        default="most_popular_products", 
        help="Source table name in Snowflake"
    )
    parser.add_argument(
        "--target-column", 
        default="description", 
        help="Column to use for similarity comparison"
    )
    parser.add_argument(
        "--embeddings-file", 
        default="./embeddings/product_description_embeddings.json", 
        help="Path to the embeddings JSON file"
    )
    parser.add_argument(
        "--output-table", 
        default="product_description_similarity", 
        help="Name of the output similarity table"
    )
    
    # Parse arguments
    args = parser.parse_args()

    # Configure Snowflake connection parameters
    connection_params = {
        'user': os.getenv("SNOWFLAKE_USER"),
        'password': os.getenv("SNOWFLAKE_PASSWORD"),
        'account': os.getenv("SNOWFLAKE_ACCOUNT"),
        'warehouse': os.getenv("SNOWFLAKE_WAREHOUSE"),
        'database': os.getenv("SNOWFLAKE_DATABASE"),
        'schema': os.getenv("SNOWFLAKE_SCHEMA"),
    }

    # Initialize processor
    processor = ProductSimilarityProcessor(connection_params)

    # Start timing
    start_time = time.time()

    # Generate similarity matrix with parsed arguments
    processor.generate_product_similarity_matrix(
        embeddings_filepath=args.embeddings_file,
        source_table=args.source_table,
        target_column=args.target_column,
        output_table=args.output_table
    )

    # Print total execution time
    print(f"Total execution time: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    main()
