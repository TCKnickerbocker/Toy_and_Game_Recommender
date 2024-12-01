# Not yet working
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity


# Load data
user_item_df = pd.read_sql("SELECT * FROM filtered_user_item_interactions", connection)

# Create user-item sparse matrix
user_item_matrix = user_item_df.pivot_table(
    index='user_id', columns='productID', values='rating', fill_value=0
)
sparse_user_item_matrix = csr_matrix(user_item_matrix.values)

# Compute item-item similarity (optimized for sparse matrix)
item_similarity_sparse = cosine_similarity(sparse_user_item_matrix.T, dense_output=False)

# Convert to dense DataFrame for easier manipulation
item_similarity_df = pd.DataFrame(
    item_similarity_sparse.toarray(), 
    index=user_item_matrix.columns, 
    columns=user_item_matrix.columns
)

# Recommendation function
def recommend_items(user_id, user_item_matrix, item_similarity_df, top_n=5):
    user_ratings = user_item_matrix.loc[user_id]  # Get user's ratings
    already_rated = user_ratings[user_ratings > 0].index  # Products already rated

    # Calculate scores for items not rated by the user
    scores = item_similarity_df.dot(user_ratings).div(item_similarity_df.sum(axis=1))
    scores = scores.drop(already_rated, errors='ignore')  # Filter out rated items

    # Return top N recommendations
    return scores.nlargest(top_n)

# Example usage
user_id = 123
recommendations = recommend_items(user_id, user_item_matrix, item_similarity_df)
print("Recommendations for User:", recommendations)



## TODO: use text similarity between items