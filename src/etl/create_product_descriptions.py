import os
import snowflake.connector
from dotenv import load_dotenv
from openai import OpenAI
import concurrent.futures
import logging
from typing import List, Dict, Tuple

load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize OpenAI API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ProductDescriptionUpdater:
    def __init__(self, connection_params, max_workers=10):
        """
        Initialize the updater with Snowflake connection parameters and multithreading settings.

        :param connection_params: Dictionary of Snowflake connection parameters
        :param max_workers: Maximum number of concurrent worker threads
        """
        self.connection_params = connection_params
        self.max_workers = max_workers

    def fetch_product_data(self, conn, source_table) -> List[Dict]:
        """
        Fetch product data (Title, Description, Store, productId) from the source table.

        :param conn: Snowflake connection object
        :param source_table: Name of the source table
        :return: List of dictionaries containing product data
        """
        with conn.cursor() as cur:
            # Ensure description column exists
            query = f"""
            ALTER TABLE {source_table}
            ADD COLUMN IF NOT EXISTS description VARCHAR
            """
            cur.execute(query)
            
            # Fetch product data
            query = f"""
            SELECT productId, Title, Details, Store
            FROM {source_table}
            where Description is null
            """
            cur.execute(query)
            rows = cur.fetchall()

        return [
            {"productId": row[0], "title": row[1], "details": row[2], "store": row[3]}
            for row in rows
        ]

    def extract_key_info(self, product: Dict, model="gpt-3.5-turbo", temperature=0.2) -> Tuple[str, str]:
        """
        Extract key information for a single product.

        :param product: Dictionary containing product details
        :param model: OpenAI model to use
        :param temperature: Sampling temperature for OpenAI
        :return: Tuple of (productId, extracted description)
        """
        try:
            title = product["title"]
            description = product["details"]
            store = product["store"]
            productId = product["productId"]

            prompt = f"""
            Extract the key information from the following inputs for creating text embeddings:
            
            Title:
            {title}
            
            Details:
            {description}
            
            Store:
            {store}
            
            Extraction should follow this format:
            - Summarized product name and key details (e.g., product type, audience).
            - Highlight key usage or purpose.
            - Extract category if available.
            - Mention weight in qualitative terms (e.g., light, moderate, heavy).
            - Mention size qualitatively (e.g., small, medium, large).
            - Include the age group/range that this product is intended for
            - Add release date in a human-readable format if available.
            - Include the store or manufacturer name.
            - Keywords people might use to describe the product (racing, pokemon, anime)
            - Add specific keywords to capture the sentiment of this product (upbeat, entertainment, learning) 
            - Function of the product
            - Any additional relevant details, such as the number of players, game time, 
            """

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for extracting structured information from product data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
            )
            
            new_description = response.choices[0].message.content.strip()
            return (productId, new_description)

        except Exception as e:
            logger.error(f"Error processing product {product.get('productId')}: {e}")
            return (product["productId"], "")

    def update_product_descriptions(self, conn, source_table, updated_data: List[Tuple[str, str]]):
        """
        Update the table with new descriptions.

        :param conn: Snowflake connection object
        :param source_table: Name of the source table
        :param updated_data: List of tuples (productId, new_description)
        """
        with conn.cursor() as cur:
            update_query = f"""
            UPDATE {source_table}
            SET Description = %s
            WHERE productId = %s
            """
            cur.executemany(update_query, [(desc, pid) for pid, desc in updated_data])
            conn.commit()

    def process_products(self, source_table):
        """
        Main processing function to update product descriptions using multithreading.

        :param source_table: Name of the source table
        """
        with snowflake.connector.connect(**self.connection_params) as conn:
            # Fetch product data
            products = self.fetch_product_data(conn, source_table)
            logger.info(f"Found {len(products)} products to process")

            # Process products concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit tasks for each product
                futures = [
                    executor.submit(self.extract_key_info, product) 
                    for product in products
                ]

                # Collect results as they complete
                updated_data = []
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        if result[1]:  # Only add if description is not empty
                            updated_data.append(result)
                    except Exception as e:
                        logger.error(f"Error in future processing: {e}")

                logger.info(f"Successfully processed {len(updated_data)} product descriptions")

            # Update the table
            self.update_product_descriptions(conn, source_table, updated_data)
            logger.info("Product description update complete")

def main():
    # Configure connection parameters from environment variables
    connection_params = {
        'user': os.getenv("SNOWFLAKE_USER"),
        'password': os.getenv("SNOWFLAKE_PASSWORD"),
        'account': os.getenv("SNOWFLAKE_ACCOUNT"),
        'warehouse': os.getenv("SNOWFLAKE_WAREHOUSE"),
        'database': os.getenv("SNOWFLAKE_DATABASE"),
        'schema': os.getenv("SNOWFLAKE_SCHEMA"),
    }

    source_table = "most_popular_products"
    
    # Initialize updater with optional max_workers parameter
    updater = ProductDescriptionUpdater(connection_params, max_workers=10)
    updater.process_products(source_table)

if __name__ == "__main__":
    main()
