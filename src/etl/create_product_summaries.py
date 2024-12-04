import snowflake.connector
from openai import OpenAI
import concurrent.futures
import logging
from typing import List, Dict, Tuple
import sys
sys.path.append("./configs")
import etl_configs

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(etl_configs.OPENAI_API_KEY)

class ProductSummaryGenerator:
    def __init__(self, connection_params, max_workers=10):
        """
        Initialize the summary generator with Snowflake connection parameters and multithreading settings.

        :param connection_params: Dictionary of Snowflake connection parameters
        :param max_workers: Maximum number of concurrent worker threads
        """
        self.connection_params = connection_params
        self.max_workers = max_workers

    def fetch_product_data(self, conn, source_table='most_popular_products') -> List[Dict]:
        """
        Fetch product data for summary generation.

        :param conn: Snowflake connection object
        :param source_table: Name of the source table
        :return: List of dictionaries containing product data
        """
        with conn.cursor() as cur:
            # Fetch product data including previously generated description
            query = f"""
            ALTER TABLE {source_table}
            ADD COLUMN IF NOT EXISTS summary VARCHAR;
            """
            query = f"""
            SELECT productId, Title, Description, Store, Price, original_description, original_features
            FROM {source_table}
            where summary is null
            """
            cur.execute(query)
            rows = cur.fetchall()

        return [
            {
                "productId": row[0], 
                "title": row[1], 
                "description": row[2], 
                "store": row[3],
                "price": row[4],
                "original_description": row[5],
                "original_features": row[6]
                
            }
            for row in rows
        ]

    def generate_attractive_summary(self, product: Dict, model="gpt-3.5-turbo", temperature=0.7) -> Tuple[str, str]:
        """
        Generate an attractive, conversion-focused summary for a product.

        :param product: Dictionary containing product details
        :param model: OpenAI model to use
        :param temperature: Sampling temperature for OpenAI
        :return: Tuple of (productId, generated summary)
        """
        try:
            title = product["title"]
            description = product["description"]
            store = product["store"]
            price = product["price"]
            productId = product["productId"]
            original_description = product["original_description"]
            original_features = product["original_features"]
            

            prompt = f"""
            Create a compelling, concise product summary that drives online sales. 
            The summary should be engaging, highlight key benefits, and motivate a purchase.

            Product Details:
            - Title: {title}
            - Current Description: {description}
            - Original Description: {original_description}
            - Features: {original_features}
            - Store: {store}
            - Price: ${price}
            

            Generate a summary that:
            1. Starts with an attention-grabbing hook
            2. Briefly explains what the product is beyond the title (assume that users have already read the product's title)
            3. Highlights 2-3 unique selling points 
            4. Uses persuasive language
            5. Matches the tone of the product's target audience
            6. Keeps the summary under 120 words
            7. Includes a subtle call-to-action

            Format the summary with clear, punchy language that makes the product interesting and desirable. Try to use a limited number of emojis.
            """

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a professional copywriter specializing in creating compelling product descriptions that inform shoppers and drive online sales."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=150
            )
            
            new_summary = response.choices[0].message.content.strip()
            print("Title: ", title)
            print("new_summary: ", new_summary)
            return (productId, new_summary)

        except Exception as e:
            logger.error(f"Error processing product {product.get('productId')}: {e}")
            return (product["productId"], "")

    def update_product_summaries(self, conn, source_table, updated_data: List[Tuple[str, str]]):
        """
        Update the table with new product summaries.

        :param conn: Snowflake connection object
        :param source_table: Name of the source table
        :param updated_data: List of tuples (productId, new_summary)
        """
        with conn.cursor() as cur:
            update_query = f"""
            UPDATE {source_table}
            SET Summary = %s
            WHERE productId = %s
            """
            cur.executemany(update_query, [(summary, pid) for pid, summary in updated_data])
            conn.commit()

    def generate_summaries(self, source_table):
        """
        Main processing function to generate attractive product summaries using multithreading.

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
                    executor.submit(self.generate_attractive_summary, product) 
                    for product in products
                ]

                # Collect results as they complete
                updated_data = []
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        if result[1]:  # Only add if summary is not empty
                            updated_data.append(result)
                    except Exception as e:
                        logger.error(f"Error in future processing: {e}")

                logger.info(f"Successfully generated {len(updated_data)} product summaries")

            # Update the table with new summaries
            self.update_product_summaries(conn, source_table, updated_data)
            logger.info("Product summary generation complete")

def main():
    source_table = "most_popular_products"
    
    # Initialize summary generator
    summary_generator = ProductSummaryGenerator(etl_configs.CONNECTION_PARAMS, max_workers=8) 
    summary_generator.generate_summaries(source_table)

if __name__ == "__main__":
    main()
