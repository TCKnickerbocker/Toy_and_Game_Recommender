import re
import snowflake.connector
from openai import OpenAI
import concurrent.futures
from typing import List, Dict
import uuid
import os

# Private variables
from generator_configs import LOGGER, OPENAI_API_KEY

# s3
import boto3
import requests
from urllib.parse import urlparse

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

class CreativeProductGenerator:
    def __init__(self, connection_params, domain_expander, max_workers=5):
        """
        Initialize the creative product generator with Snowflake connection parameters.

        :param connection_params: Dictionary of Snowflake connection parameters
        :param max_workers: Maximum number of concurrent worker threads
        """
        self.connection_params = connection_params
        self.domain_expander = domain_expander
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
            domains_to_consider = self.domain_expander.get_random_domains()

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
            Some domains you may want to consider are: {domains_to_consider}. Try to avoid the topic of outer space.
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

                LOGGER.info(f"Product {title} with id {product_id} store successfully")
                return product_id

        except Exception as e:
            LOGGER.error(f"Error storing new products: {e}")
            return None


    def generate_creative_products(self, target_table='generated_products', num_products=1, user_id=None) -> List[Dict]:
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
                print("NUM PRODUCTS: ", num_products)
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
                        # store_product_image_in_s3(parsed_product["productId"], parsed_product["imageUrl"], "amazontoyreviews", conn)
                        
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

# TODO: call async? takes forever to complete.
def store_product_image_in_s3(product_id, original_image_url, s3name, snowflake_conn):
    """
    Download an image from a URL and store it in an S3 bucket.

    :param full_product_data: Dictionary containing product and image details
    :param s3name: Name or identifier for the S3 bucket
    :return: S3 URL of the stored image or None if storage fails
    """
    try:
        # Get the image URL from the product data
        temp_image_url = original_image_url
        if not temp_image_url:
            LOGGER.warning("No image URL found in store_image_in_s3")
            return None

        # Download the image
        response = requests.get(temp_image_url)
        if response.status_code != 200:
            LOGGER.error(f"Failed to download image from {temp_image_url}")
            return None

        # Prepare file details
        file_extension = os.path.splitext(urlparse(temp_image_url).path)[1] or '.png'
        local_filename = f"{product_id}{file_extension}"

        # Save temporary local file
        with open(local_filename, 'wb') as f:
            f.write(response.content)

        # Initialize S3 client, determine path
        s3_client = boto3.client('s3')
        s3_key = f"product_images/{local_filename}"
        
        # Generate S3 URL
        s3_url = f"https://{s3name}.s3.amazonaws.com/{s3_key}"
        
        insert_new_image_into_table(snowflake_conn, product_id, s3_url, table_name="ai_generated_products", image_column_name="imageurl")
        # Upload to S3
        s3_client.upload_file(
            local_filename, 
            s3name, 
            s3_key, 
            ExtraArgs={
                'ContentType': response.headers.get('content-type', 'image/png')
            }
        )

        # Clean up local file
        os.remove(local_filename)

        LOGGER.info(f"Image stored in S3 at {s3_url}")
        return s3_url

    except Exception as e:
        LOGGER.error(f"Error storing image in S3: {e}")
        return None
    

def insert_new_image_into_table(conn, product_id, image_url, table_name="ai_generated_products", image_column_name="imageurl"):
    """
    Insert a new image URL into the specified table for a given product ID.

    :param conn: Connection object for the database.
    :param product_id: The ID of the product to associate with the image.
    :param image_url: The URL of the image to be inserted.
    :param table_name: The name of the target table (default: 'ai_generated_products').
    :param image_column_name: The name of the column to insert the image URL into (default: 'image').
    """
    query = f"""
        UPDATE {table_name}
        SET {image_column_name} = %s
        WHERE productid = %s
    """
    try:
        with conn.cursor() as cur:
            cur.execute(query, (image_url, str(product_id)))
            conn.commit()
            print(f"Image URL successfully updated for product_id: {product_id}")
    except Exception as e:
        print(f"Error inserting image into table: {e}")
