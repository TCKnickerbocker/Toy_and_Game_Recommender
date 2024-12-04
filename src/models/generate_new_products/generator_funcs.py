import re
import snowflake.connector
from openai import OpenAI
import concurrent.futures
from typing import List, Dict
import uuid

import sys
sys.path.append("../configs")
from model_config import LOGGER, OPENAI_API_KEY


# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

class CreativeProductGenerator:
    def __init__(self, connection_params, max_workers=5):
        """
        Initialize the creative product generator with Snowflake connection parameters.

        :param connection_params: Dictionary of Snowflake connection parameters
        :param max_workers: Maximum number of concurrent worker threads
        """
        self.connection_params = connection_params
        self.max_workers = max_workers

    def fetch_inspiration_products(self, conn, history_limit=8, user_id=None) -> List[Dict]:
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
                RANDOM(), u.RATING DESC NULLS LAST
            LIMIT {history_limit};
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
            Make a new game or toy that will appeal to this user given their past ratings:

            {user_history}

            Generate a new, interesting, and creative game or toy that:
            1. Has a catchy, memorable name
            2. Includes a compelling and engaging initial product description
            3. Targets a specific audience or use case

            Provide the following details in the specified format. Please note that the '@@@' MUST precede its respective sections:
            @@@ Product Title (product name here)
            @@@ Product Description (max 120 words, should contain an engaging for the new product and resemble the descriptions above)
            @@@ Product Specs (max 120 words, should contain specifications for the new product and resemble the specs above)
            
            Like:
            @@@ Monopoly
            @@@ 💸 Some text
            @@@ Specs of Monopoly
            Please be as creative as possible while reasonably inferring that the product will appeal to some dimension of this person's preferences.
            Some domains you may want to consider are: board games, toys, video games, games for families. Try to avoid the topic of outer space.
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
            LOGGER.error(f"Error generating product concept: {e}")
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
            LOGGER.error(f"Error generating product image: {e}")
            return {"image_url": "", "revised_prompt": ""}

    def store_new_product(self, conn, product_data: List[Dict], source_table='ai_generated_products'):
        """
        Store newly generated products in the Snowflake database.

        :param conn: Snowflake connection object
        :param products_data: List of dictionaries, each containing new product details
        :param source_table: Name of the target table
        """
        try:
            with conn.cursor() as cur:
                # Ensure the table has necessary columns
                create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {source_table} (
                    productId VARCHAR(12) PRIMARY KEY,
                    Title VARCHAR,
                    Summary VARCHAR(1024),
                    Description VARCHAR(2048),
                    ImageUrl TEXT,
                    ImagePrompt TEXT
                )
                """
                cur.execute(create_table_query)

                # Prepare insert query
                insert_query = f"""
                INSERT INTO {source_table} 
                (productId, Title, Summary, Description, ImageUrl, ImagePrompt)
                VALUES 
                """

                # Collect insert values
                values_list = []
                product_id = str(uuid.uuid4())[:12]
                concept_text = product_data['concept_text']

                # Parse concept text into components
                pattern = r"@@@\s*(.*?)\s*(?=@@@|$)"
                sections = re.findall(pattern, concept_text, re.DOTALL)
                title = sections[0].strip().replace("'", "''") if len(sections) > 0 else ''
                summary = sections[1].strip().replace("'", "''") if len(sections) > 1 else ''
                description = sections[2].strip().replace("'", "''") if len(sections) > 2 else ''
                
                image_url = product_data.get('image_url', '').replace("'", "''")
                revised_prompt = product_data.get('revised_prompt', '').replace("'", "''")

                # Add to the values list
                values_list.append(
                    f"('{product_id}', '{title}', '{summary}', '{description}', '{image_url}', '{revised_prompt}')"
                )
                # Combine all values into the query
                final_insert_query = insert_query + ",\n".join(values_list)
                cur.execute(final_insert_query)
                conn.commit()

                logging.info(f"Product {title} with id {product_id} store successfully")
                return product_id

        except Exception as e:
            logging.error(f"Error storing new products: {e}")
            return None


    def generate_creative_products(self, target_table='generated_products', num_products=4, user_id=None) -> List[Dict]:
        """
        Main processing function to generate creative new products.

        :param target_table: Name of the table to store new products
        :param num_products: Number of products to generate
        :return: List of generated product dictionaries
        """
        generated_products = []

        with snowflake.connector.connect(**self.connection_params) as conn:
            # Fetch inspiration products
            inspiration_products = self.fetch_inspiration_products(conn, history_limit=10, user_id=user_id)
            LOGGER.info(f"Using {len(inspiration_products)} products for inspiration")

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
                        
                        # Store the new product in Snowflake
                        product_id = self.store_new_product(conn, full_product_data, target_table)
                        
                        # Parse the concept text into a more structured format
                        parsed_product = self._parse_product_concept(full_product_data['concept_text'])
                        
                        # Add additional fields
                        parsed_product.update({
                            'productId': product_id,
                            'imageUrl': full_product_data.get('image_url', ''),
                            'imagePrompt': full_product_data.get('revised_prompt', '')
                        })
                        
                        generated_products.append(parsed_product)

                    except Exception as e:
                        LOGGER.error(f"Error processing product generation: {e}")

            LOGGER.info(f"Product generation complete")
            
            return generated_products

    def _parse_product_concept(self, concept_text: str) -> Dict:
        """
        Parse the product concept text into a structured dictionary.

        :param concept_text: Raw concept text from product generation
        :return: Structured product dictionary
        """
        # Extract sections using regex
        pattern = r"@@@\s*(.*?)\s*(?=@@@|$)"
        sections = re.findall(pattern, concept_text, re.DOTALL)
        
        # Ensure we have enough sections
        while len(sections) < 4:
            sections.append('')

        # Create a structured product dictionary
        product = {
            'title': sections[0].strip(),
            'summary': sections[1].strip(),
            'description': sections[2].strip(),
        }
        
        return product

