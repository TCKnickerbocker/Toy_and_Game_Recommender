# Not yet working 
def recommend_items(user_id, user_item_matrix, item_similarity_df, top_n=5):
    # Get the user's ratings
    user_ratings = user_item_matrix.loc[user_id]

    # Compute weighted scores for all items
    scores = item_similarity_df.dot(user_ratings).div(item_similarity_df.sum(axis=1))

    # Filter out items the user has already rated
    already_rated = user_ratings[user_ratings > 0].index
    scores = scores.drop(already_rated, errors='ignore')

    # Return top N recommendations
    return scores.nlargest(top_n)

# Example: Get recommendations for user 123
user_id = 123
recommendations = recommend_items(user_id, user_item_matrix, item_similarity_df)
print(recommendations)
