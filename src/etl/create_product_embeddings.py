import os
import snowflake.connector
from transformers import AutoModel
from tqdm import tqdm  # For progress tracking


# NOTE: ran this on a colab due to download issues
class ProductTitleEmbedder:
    def __init__(self, model_name="jinaai/jina-embeddings-v3"):
        """
        Initialize the embedder with the specified model
        
        Args:
            model_name (str): Hugging Face model name for embeddings
        """
        # Set environment variables for Snowflake connection
        self.connection_params = {
            'user': os.getenv("SNOWFLAKE_USER"),
            'password': os.getenv("SNOWFLAKE_PASSWORD"),
            'account': os.getenv("SNOWFLAKE_ACCOUNT"),
            'warehouse': os.getenv("SNOWFLAKE_WAREHOUSE"),
            'database': os.getenv("SNOWFLAKE_DATABASE"),
            'schema': os.getenv("SNOWFLAKE_SCHEMA"),
        }
        
        # Load embedding model
        self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
    
    def get_titles_from_snowflake(self, query=None):
        """
        Retrieve product titles from Snowflake
        
        Args:
            query (str, optional): Custom SQL query to fetch titles. 
                                   Defaults to fetching all titles with product ID
        
        Returns:
            list: List of tuples (productid, title)
        """
        if query is None:
            query = """
            SELECT PRODUCTID, TITLE 
            FROM most_popular_products 
            """
        
        try:
            # Establish Snowflake connection
            conn = snowflake.connector.connect(**self.connection_params)
            cursor = conn.cursor()
            
            # Execute query
            cursor.execute(query)
            titles = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return titles
        
        except Exception as e:
            print(f"Error retrieving titles: {e}")
            return []
    
    def encode_titles(self, titles, batch_size=100):
        """
        Encode titles into embeddings
        
        Args:
            titles (list): List of titles to encode
            batch_size (int): Number of titles to process in each batch
        
        Returns:
            list: List of embeddings corresponding to input titles
        """
        all_embeddings = []
        
        # Process titles in batches
        for i in tqdm(range(0, len(titles), batch_size), desc="Encoding Titles"):
            batch = titles[i:i+batch_size]
            batch_texts = [title[1] for title in batch]  # Extract title from (product_id, title)
            
            # Generate embeddings
            batch_embeddings = self.model.encode(
                batch_texts, 
                task="text-matching"
            )
            
            all_embeddings.extend(list(zip(
                [title[0] for title in batch],  # product_ids
                batch_texts,                    # original titles 
                batch_embeddings               # embeddings
            )))
        
        return all_embeddings
    
    def insert_embeddings_to_snowflake(self, embeddings):
        """
        Insert product title embeddings into Snowflake table
        
        Args:
            embeddings (list): List of (product_id, title, embedding) tuples
        """
        insert_sql = """
        INSERT INTO PRODUCT_TITLE_EMBEDDINGS 
        (PRODUCTID, TITLE, EMBEDDING) 
        VALUES (%s, %s, %s)
        """
        
        try:
            conn = snowflake.connector.connect(**self.connection_params)
            cursor = conn.cursor()
            
            # Insert embeddings in batches
            for batch_start in tqdm(range(0, len(embeddings), 1000), desc="Inserting Embeddings"):
                batch = embeddings[batch_start:batch_start+1000]
                batch_data = [
                    (str(prod_id), title, list(map(float, embedding))) 
                    for prod_id, title, embedding in batch
                ]
                
                cursor.executemany(insert_sql, batch_data)
                conn.commit()
            
            cursor.close()
            conn.close()
            
            print(f"Successfully inserted {len(embeddings)} embeddings")
        
        except Exception as e:
            print(f"Error inserting embeddings: {e}")
    
    def run_embedding_pipeline(self, custom_query=None):
        """
        Full pipeline: fetch titles, encode, and insert embeddings
        
        Args:
            custom_query (str, optional): Custom SQL query to fetch titles
        """
        # Retrieve titles
        titles = self.get_titles_from_snowflake(custom_query)
        
        if not titles:
            print("No titles found to process.")
            return
        
        # Encode titles
        embeddings = self.encode_titles(titles)
        
        # Insert embeddings
        self.insert_embeddings_to_snowflake(embeddings)

if __name__ == "__main__":
    # Initialize embedder
    embedder = ProductTitleEmbedder()
    
    # Run full pipeline
    embedder.run_embedding_pipeline()