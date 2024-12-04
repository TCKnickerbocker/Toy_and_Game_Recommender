import json
import os
import argparse
import numpy as np 
import snowflake.connector
from tqdm import tqdm
from transformers import AutoModel

import sys
sys.path.append("./configs")
import etl_configs

class ProductTextEmbedder:
    def __init__(self, connection_params, model_name="jinaai/jina-embeddings-v3"):
        """
        Initialize the embedder

        Args:
            model_name (str): Hugging Face model name for embeddings
        """
        self.connection_params = connection_params

        # Load embedding model
        self.model = AutoModel.from_pretrained(model_name, trust_remote_code=True)

    def get_text_in_batches(self, table_name, target_column='title', batch_size=50):
        """
        Retrieve product text from Snowflake in batches

        Args:
            table_name (str): Name of the table to fetch texts from
            target_column (str): Column to retrieve text from
            batch_size (int): Number of texts to retrieve in each batch

        Yields:
            list: Batch of tuples (productid, text)
        """
        count_query = f"""
        SELECT COUNT(*) as total_count
        FROM {table_name}
        """

        batch_query = f"""
        SELECT PRODUCTID, {target_column}
        FROM {table_name}
        ORDER BY PRODUCTID
        LIMIT %s OFFSET %s
        """

        try:
            # Establish Snowflake connection
            conn = snowflake.connector.connect(**self.connection_params)
            cursor = conn.cursor()

            # Get total count of products
            cursor.execute(count_query)
            total_count = cursor.fetchone()[0]

            # Iterate through batches
            for offset in range(0, total_count, batch_size):
                cursor.execute(batch_query, (batch_size, offset))
                texts_batch = cursor.fetchall()

                if not texts_batch:
                    break

                yield texts_batch

            cursor.close()
            conn.close()

        except Exception as e:
            print(f"Error retrieving texts: {e}")
            return []

    def encode_texts(self, texts, batch_size=50):
        """
        Encode texts into embeddings with reduced memory usage

        Args:
            texts (list): List of texts to encode
            batch_size (int): Number of texts to process in each embedding batch

        Returns:
            list: List of embeddings corresponding to input texts
        """
        all_embeddings = []

        # Process texts in embedding batches
        for i in tqdm(range(0, len(texts), batch_size), desc="Encoding Texts"):
            batch = texts[i:i + batch_size]
            batch_texts = [text[1] for text in batch]  # Extract text from (product_id, text)

            # Generate embeddings
            batch_embeddings = self.model.encode(
                batch_texts,
                task="text-matching"
            )

            all_embeddings.extend(list(zip(
                [text[0] for text in batch],  # product_ids
                batch_texts,                    # original texts
                batch_embeddings               # embeddings
            )))

        return all_embeddings

    def save_embeddings_to_json(self, embeddings, file_path):
            """
            Save product text embeddings to a JSON file in a Colab-compatible way.

            Args:
                embeddings (list): List of (product_id, text, embedding) tuples
                file_path (str): Path of the JSON file to save embeddings
            """
            embeddings_dict = {
                str(prod_id): embedding_vector.tolist()  # Convert numpy arrays to lists
                for prod_id, _, embedding_vector in embeddings
            }
            
            # Handle existing data
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    existing_data = json.load(f)
            else:
                print(f"File {file_path} does not exist. Creating a new one.")
                existing_data = {}

            existing_data.update(embeddings_dict)
            
            # Ensure directory exists
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                print(f"Directory {dir_path} does not exist. Creating it.")
                os.makedirs(dir_path, exist_ok=True)
            
            print(f"Writing to file {file_path}")
            # Save the merged embeddings back to the file
            with open(file_path, "w") as f:
                json.dump(existing_data, f, indent=4)

    def run_embedding_pipeline(self, table_name, target_column, file_path):
        """
        Full pipeline: fetch texts in batches, encode, and save embeddings to JSON

        Args:
            table_name (str): Name of the table to fetch texts from
            target_column (str): Column to retrieve text from
            file_path (str): Path to save embeddings JSON file
        """
        # Process texts in batches
        for texts_batch in self.get_text_in_batches(table_name, target_column):
            if not texts_batch:
                print("No titles found to process.")
                break

            # Encode titles
            embeddings = self.encode_texts(texts_batch)

            # Save embeddings to JSON file
            self.save_embeddings_to_json(embeddings, file_path)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Product Text Embedder")
    
    # Define command-line arguments
    parser.add_argument(
        "--table-name", 
        default="most_popular_products", 
        help="Name of the Snowflake table to process"
    )
    parser.add_argument(
        "--target-column", 
        default="description", 
        help="Column to retrieve text from"
    )
    parser.add_argument(
        "--output-file", 
        default="../../data/embeddings/product_description_embeddings.json", 
        help="Path to save embeddings JSON file"
    )
    
    # Parse arguments
    args = parser.parse_args()

    # Initialize embedder
    embedder = ProductTextEmbedder(etl_configs.CONNECTION_PARAMS)

    # Run full job with parsed arguments
    embedder.run_embedding_pipeline(
        table_name=args.table_name,
        target_column=args.target_column,
        file_path=args.output_file
    )

if __name__ == "__main__":
    main()
