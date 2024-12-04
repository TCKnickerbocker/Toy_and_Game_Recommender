import re
import snowflake.connector
from openai import OpenAI
import concurrent.futures
import logging
from typing import List, Dict
import uuid
import sys
sys.path.append("../configs")
import model_config

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=model_config.OPENAI_API_KEY)

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
        with conn.cursor() as cur:
            query = f"""
            SELECT 
                p.productId,
                p.title, 
                p.summary,
                p.description,
                u.RATING as users_rating
            FROM 
                most_popular_products p
            LEFT JOIN 
                user_ratings u ON p.productId = u.PARENT_ASIN
            WHERE 
                u.user_id = '{user_id}'
            ORDER BY 
                u.RATING DESC NULLS LAST
            LIMIT {limit};
            """
            cur.execute(query)
            rows = cur.fetchall()

        return [
            {
                "product_id": row[0],
                "title": row[1], 
                "summary": row[2],
                "description": row[3],
                "rating": row[4]
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
                f"""- {p['title']} \n
                (User's rating: {p['rating']}): \n
                Description: {p['summary']} \n
                Specs: {p['description']} \n
                """
                for p in inspiration_products
            ])

            prompt = f"""
            Make a new new game or toy that will appeal to this user given their past ratings:

            {user_history}

            Generate a completely new unique, interesting, and creative game or toy that:
            1. Has a catchy, memorable name
            2. Includes a compelling and interesting initial product description
            3. Targets a specific audience or use case

            Provide the following details in the specified format. Please note that the '@@@' MUST precede its respective sections:
            @@@ Product Name (product name here)
            @@@ Product Description (max 120 words, should contain an engaging for the new product and resemble the descriptions above)
            @@@ Product Specs (max 120 words, should contain specifications for the new product and resemble the specs above)
            @@@ Price (a rough estimation as a float)
            
            Like:
            @@@ Monopoly
            @@@ 💸 Some text
            @@@ Specs of Monopoly
            @@@ 45.345
            Please be as creative as possible while reasonably inferring that the product will appeal to some dimension of this person's preferences.
            """

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an innovative product design consultant who creates unique product concepts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=300
            )
            
            new_product_concept = response.choices[0].message.content.strip()
            print(new_product_concept)
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

            Focus on creating a clear visualization that would appear in a product catalog or marketing material.
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
            print(image_url)
            return {
                "image_url": image_url,
                "revised_prompt": response.data[0].revised_prompt
            }

        except Exception as e:
            logger.error(f"Error generating product image: {e}")
            return {"image_url": "", "revised_prompt": ""}

    def _safe_extract_text(self, lines, pattern, default=""):
        """
        Safely extract text matching a pattern from lines.
        
        :param lines: List of lines to search
        :param pattern: Regex pattern to match
        :param default: Default value if no match is found
        :return: Extracted text or default
        """
        for line in lines:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                # Remove the pattern and strip whitespace
                extracted = re.sub(pattern, '', line, flags=re.IGNORECASE).strip()
                return extracted if extracted else default
        return default

    def store_new_product(self, conn, product_data: Dict, source_table='ai_generated_products'):
            """
            Store the newly generated product in the Snowflake database.

            :param conn: Snowflake connection object
            :param source_table: Name of the target table
            :param product_data: Dictionary containing new product details
            """
            try:
                # Generate a unique product ID
                product_id = str(uuid.uuid4())[:12]
                print(f"Storing new product with ID: {product_id}")
                
                with conn.cursor() as cur:
                    # Ensure the table has necessary columns
                    create_table_query = f"""
                    CREATE TABLE IF NOT EXISTS {source_table} (
                        productId VARCHAR(12) PRIMARY KEY,
                        Title VARCHAR,
                        Summary VARCHAR(1024),
                        Description VARCHAR(2048),
                        ImageUrl TEXT,
                        ImagePrompt TEXT,
                        Concept TEXT
                    )
                    """
                    cur.execute(create_table_query)
                    
                    # Extract details from the concept text
                    concept_text = product_data['concept_text']
                    
                    pattern = r"@@@\s*(.*?)\s*(?=@@@|$)"

                    # Find all sections
                    sections = re.findall(pattern, concept_text, re.DOTALL)
                    title, summary, description, price = None, None, None, None
                    
                    for idx, section in enumerate(sections, 1):
                        if idx==1:
                            title = section.strip()
                        elif idx==2:
                            summary=section.strip()
                        elif idx==3:
                            description=section.strip()
                        elif idx==4:
                            price=section.strip()                        
                        
                    # Sanitize inputs to prevent SQL injection
                    title = title.replace("'", "''")
                    summary = summary.replace("'", "''")
                    description = description.replace("'", "''")
                    price = price.replace("'", "''")
                    
                    # Insert the new product
                    insert_query = f"""
                    INSERT INTO {source_table} 
                    (productId, Title, Summary, Description, ImageUrl, Concept)
                    VALUES (
                        '{product_id}', 
                        '{title}', 
                        '{summary}', 
                        '{description}', 
                        '{product_data.get('image_url', '')}',
                        '{concept_text.replace("'", "''")}')
                    """
                    
                    # Execute the query with the provided values
                    cur.execute(insert_query)
                    conn.commit()

                    logging.info(f"New product {product_id} stored successfully")
                    
                    return product_id
            
            except Exception as e:
                logging.error(f"Error storing new product: {e}")
                return None

    def generate_creative_products(self, source_table='most_popular_products', target_table='generated_products', num_products=5, user_id=None):
        """
        Main processing function to generate creative new products.

        :param source_table: Name of the source table for inspiration
        :param target_table: Name of the table to store new products
        :param num_products: Number of products to generate
        """
        with snowflake.connector.connect(**self.connection_params) as conn:
            # Fetch inspiration products
            inspiration_products = self.fetch_inspiration_products(conn, limit=10, user_id=user_id)
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
                        print("Getting product data")
                        # Merge concept and image data
                        full_product_data = {**product_concept, **product_image}
                        
                        # Store the new product
                        self.store_new_product(conn, full_product_data, target_table)

                    except Exception as e:
                        logger.error(f"Error processing product generation: {e}")

            logger.info(f"Product generation complete")
