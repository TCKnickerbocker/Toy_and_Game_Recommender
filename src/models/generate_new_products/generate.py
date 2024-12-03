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

class CreativeProductGenerator:
    def __init__(self, connection_params, max_workers=5):
        """
        Initialize the creative product generator with Snowflake connection parameters.

        :param connection_params: Dictionary of Snowflake connection parameters
        :param max_workers: Maximum number of concurrent worker threads
        """
        self.connection_params = connection_params
        self.max_workers = max_workers

    def fetch_inspiration_products(self, conn, limit=10, user_id=None) -> List[Dict]:
        """
        Fetch product data to inspire new product creation.

        :param conn: Snowflake connection object
        :param limit: Number of products to fetch for inspiration
        :param user_id: Optional user ID to filter products (not used in this version)
        :return: List of dictionaries containing product data
        """
        # TODO: Test query (it is probably wrong)
        with conn.cursor(as_dict=True) as cur:
            query = f"""
            SELECT 
                p.productId,
                p.title, 
                p.summary,
                p.description,
                u.RATING
            FROM 
                most_popular_products p
            LEFT JOIN 
                user_ratings u ON p.productId = u.PARENT_ASIN AND u.user_id = '{user_id}'
            ORDER BY 
                u.RATING DESC NULLS LAST
            LIMIT {limit}
            """
            cur.execute(query, {'limit': limit})
            rows = cur.fetchall()

        return [
            {
                "product_id": row['PRODUCTID'],
                "title": row['TITLE'], 
                "summary": row['SUMMARY'],
                "image": row['IMAGE'],
                "rating": row['AVG_RATING']
            }
            for row in rows
        ]

    def generate_product_concept(self, inspiration_products: List[Dict], model="gpt-3.5-turbo", temperature=0.8) -> Dict:
        """
        Generate a creative new product concept based on existing product inspirations.

        :param inspiration_products: List of dictionaries with product details
        :param model: OpenAI model to use
        :param temperature: Sampling temperature for OpenAI
        :return: Dictionary with new product concept details
        """
        try:
            # Prepare inspiration summary
            user_history = "\n".join([
                f"""- {p['title']}
                (User's rating: {p['rating']}): 
                {p['summary']}
                {p['description']}
                """
                for p in inspiration_products
            ])

            prompt = f"""
            Make a creative, fun, unique and interesting new toy or game 
            that is appropriate for kids and will appeal to this user given their past ratings:

            {user_history}

            Generate a completely new toy or game that is appropriate for children that:
            1. Has a catchy, memorable name
            2. Includes a compelling initial product description
            3. Targets a specific audience or use case

            Provide the following details:
            - Product Name
            - Product Summary (max 120 words)
            - Product Description (max 120 words)
            - Target Audience
            - Key Innovative Features
            
            Please be as creative as possible while still making something that will appeal to this person!
            """

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an innovative product design consultant who creates unique product concepts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=250
            )
            
            new_product_concept = response.choices[0].message.content.strip()
            return {"concept_text": new_product_concept}

        except Exception as e:
            logger.error(f"Error generating product concept: {e}")
            return {"concept_text": ""}

    def generate_product_image(self, product_concept: Dict, model="dall-e-3", quality="standard", size="1024x1024") -> Dict:
        """
        Generate a product image using DALL-E based on the product concept.

        :param product_concept: Dictionary containing product concept details
        :param model: DALL-E model to use
        :param quality: Image quality
        :param size: Image size
        :return: Dictionary with image generation details
        """
        try:
            # Extract product details from the concept text
            prompt = f"""
            
            Create a high-quality product image for a new toy or game.
            Generate a professional, visually appealing image to associate with this product that captures the essence of this product concept:

            {product_concept['concept_text']}

            Focus on creating a clear, attractive visualization that would appear in a product catalog or marketing material.
            This will be displayed as our product image on Amazon.
            """

            response = client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                quality=quality,
                n=1
            )

            # Get the image URL
            image_url = response.data[0].url
            
            return {
                "image_url": image_url,
                "revised_prompt": response.data[0].revised_prompt
            }

        except Exception as e:
            logger.error(f"Error generating product image: {e}")
            return {"image_url": "", "revised_prompt": ""}

    def store_new_product(self, conn, product_data: Dict, source_table='ai_generated_products'):
        """
        Store the newly generated product in the Snowflake database.

        :param conn: Snowflake connection object
        :param source_table: Name of the target table
        :param product_data: Dictionary containing new product details
        """
        with conn.cursor() as cur:
            # Ensure the table has necessary columns
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {source_table} (
                productId VARCHAR(12) PRIMARY KEY,
                Title VARCHAR,
                Description TEXT,
                ImageUrl VARCHAR,
                ImagePrompt TEXT,
                Concept TEXT
            )
            """
            cur.execute(create_table_query)

            # TODO: fix to ensure unique Generate a unique product ID
            product_id = "1"
            print(f"Product id: {product_id}")
            # Insert the new product
            insert_query = f"""
            INSERT INTO {source_table} 
            (productId, Title, Description, ImageUrl, ImagePrompt, Concept)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            # Extract details from the concept (you might want to improve parsing)
            lines = product_data['concept_text'].split('\n')
            title = lines[0].replace("Product Name: ", "").strip()
            description = "\n".join(line for line in lines[1:] if "Description:" in line).replace("Product Description:", "").strip()

            cur.execute(insert_query, (
                product_id, 
                title, 
                description, 
                product_data.get('image_url', ''),
                product_data.get('revised_prompt', ''),
                product_data['concept_text']
            ))
            conn.commit()

            logger.info(f"New product {product_id} stored successfully")

    def generate_creative_products(self, source_table='most_popular_products', target_table='generated_products', num_products=5):
        """
        Main processing function to generate creative new products.

        :param source_table: Name of the source table for inspiration
        :param target_table: Name of the table to store new products
        :param num_products: Number of products to generate
        """
        with snowflake.connector.connect(**self.connection_params) as conn:
            # Fetch inspiration products
            inspiration_products = self.fetch_inspiration_products(conn, source_table)
            logger.info(f"Using {len(inspiration_products)} products for inspiration")

            # Process products concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit tasks for product generation
                futures = []
                for _ in range(num_products):
                    # Generate product concept
                    concept_future = executor.submit(
                        self.generate_product_concept, 
                        inspiration_products
                    )
                    futures.append(concept_future)

                # Process and store generated products
                for future in concurrent.futures.as_completed(futures):
                    try:
                        product_concept = future.result()
                        
                        # Generate image for the concept
                        product_image = self.generate_product_image(product_concept)
                        
                        # Merge concept and image data
                        full_product_data = {**product_concept, **product_image}
                        
                        # Store the new product
                        self.store_new_product(conn, target_table, full_product_data)

                    except Exception as e:
                        logger.error(f"Error processing product generation: {e}")

            logger.info(f"Creative product generation complete")

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
    target_table = "generated_products"
    
    # Initialize creative product generator
    product_generator = CreativeProductGenerator(connection_params, max_workers=5)
    product_generator.generate_creative_products(
        source_table=source_table, 
        target_table=target_table, 
        num_products=1
    )

if __name__ == "__main__":
    main()
