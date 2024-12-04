# NOTE: hasn't been tested yet
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import snowflake.connector
import numpy as np
import sys
sys.path.append("./configs")
import etl_configs

class TFIDFProcessor:
    def __init__(self, connection_params):
        self.connection_params = connection_params

    def fetch_product_descriptions(self, product_table: str) -> pd.DataFrame:
        """
        Fetch product IDs and descriptions from Snowflake.
        
        :param product_table: Name of the product table
        :return: DataFrame with productId and description
        """
        with snowflake.connector.connect(**self.connection_params) as conn:
            query = f"""
            SELECT productId, description
            FROM {product_table}
            WHERE description IS NOT NULL;
            limit 1
            """
            return pd.read_sql(query, conn)

    def compute_tfidf(self, descriptions: pd.Series):
        """
        Compute TF-IDF vectors for the given descriptions.
        
        :param descriptions: Series of product descriptions
        :return: Fitted TF-IDF vectorizer and feature matrix
        """
        vectorizer = TfidfVectorizer(max_features=10000)
        tfidf_matrix = vectorizer.fit_transform(descriptions)
        return vectorizer, tfidf_matrix

    def save_tfidf_to_snowflake(self, product_ids: pd.Series, tfidf_matrix, tfidf_table: str):
        """
        Save TF-IDF vectors to Snowflake.
        
        :param product_ids: Series of product IDs
        :param tfidf_matrix: TF-IDF feature matrix
        :param tfidf_table: Name of the target table in Snowflake
        """
        # Convert TF-IDF matrix to dense format and combine with product IDs
        tfidf_df = pd.DataFrame(tfidf_matrix.todense(), index=product_ids)
        tfidf_df.reset_index(inplace=True)
        tfidf_df.rename(columns={"index": "productId"}, inplace=True)

        # Save to Snowflake
        with snowflake.connector.connect(**self.connection_params) as conn:
            conn.cursor().execute(f"CREATE TABLE IF NOT EXISTS {tfidf_table} (productId STRING, vector ARRAY)")
            for _, row in tfidf_df.iterrows():
                conn.cursor().execute(f"INSERT INTO {tfidf_table} VALUES (%s, %s)", row["productId"], row.iloc[1:].tolist())

    def get_similar_products(self, product_id: str, n=8, tfidf_table="tfidf_vectors"):
        """
        Get the top n most similar products for a given product ID based on TF-IDF cosine similarity.
        
        :param product_id: The product ID for which to find similar products
        :param n: The number of similar products to retrieve (default is 8)
        :param tfidf_table: The Snowflake table that stores TF-IDF vectors
        :return: List of product IDs for the top n most similar products
        """
        with snowflake.connector.connect(**self.connection_params) as conn:
            # Fetch the TF-IDF vector of the given product ID
            query = f"""
            SELECT productId, vector
            FROM {tfidf_table}
            WHERE productId = %s
            """
            cur = conn.cursor()
            cur.execute(query, (product_id,))
            target_product = cur.fetchone()

            if target_product is None:
                raise ValueError(f"Product ID {product_id} not found in the TF-IDF table.")

            target_vector = np.array(target_product[1])  # The TF-IDF vector

            # Fetch all other TF-IDF vectors
            query = f"SELECT productId, vector FROM {tfidf_table} WHERE productId != %s"
            cur.execute(query, (product_id,))
            product_vectors = cur.fetchall()

            # Compute cosine similarity between the target product and all others
            similar_products = []
            for product in product_vectors:
                product_id_ = product[0]
                vector = np.array(product[1])
                similarity = cosine_similarity(target_vector.reshape(1, -1), vector.reshape(1, -1))[0][0]
                similar_products.append((product_id_, similarity))

            # Sort by similarity and return the top n most similar products
            similar_products.sort(key=lambda x: x[1], reverse=True)
            top_n_similar_products = [product[0] for product in similar_products[:n]]

            return top_n_similar_products

def main():
    product_table = "most_popular_products"
    tfidf_table = "tfidf_vectors"

    processor = TFIDFProcessor(etl_configs.CONNECTION_PARAMS)
    products = processor.fetch_product_descriptions(product_table)
    vectorizer, tfidf_matrix = processor.compute_tfidf(products["description"])
    processor.save_tfidf_to_snowflake(products["productId"], tfidf_matrix, tfidf_table)

    # Example: Get 8 most similar products to productid 'B0953YFR2M'
    product_id = "B0953YFR2M" 
    similar_products = processor.get_similar_products(product_id, n=8)
    print(f"Top 8 similar products to {product_id}: {similar_products}")

if __name__ == "__main__":
    main()
