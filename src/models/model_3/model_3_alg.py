def recommend_products(most_similar_products, num_recs_to_give):
    """
    Generate personalized product recommendations based on user interactions and product similarities.

    Args:
        most_similar_products (dict): A dictionary of products with the following structure:
            {product_id: [user_rating, is_favorited, [similar_product_ids]]}
            - user_rating: Numeric rating given by the user
            - is_favorited: Boolean indicating if the product was favorited
            - similar_product_ids: List of product IDs similar to the current product

        num_recs_to_give (int): The number of product recommendations to generate

    Returns:
        list: A list of unique product IDs recommended for the user, 
              sorted by a calculated recommendation score

    Note:
        - Recommendations are based on a scoring mechanism that considers:
          1. User's original product rating
          2. Whether the product was favorited
          3. Number of similar products
        - Ensures no duplicate recommendations are returned
    """
    # Validate input
    if not most_similar_products:
        return []

    def calculate_score(pid, info):
        """
        Calculate a recommendation score for a product.

        Args:
            pid (str): Product ID
            info (list): Product information [rating, is_favorited, similar_products]

        Returns:
            float: Calculated recommendation score
        """
        # Base rating score (normalized)
        rating_score = info[0]
        
        # Bonus for favorited items
        favorite_multiplier = 1.5 if info[1] else 1.0
        
        # Number of similar products available
        similar_products_count = len(info[2]) if info[2] else 0
        
        return rating_score * favorite_multiplier * (1 + 0.1 * min(similar_products_count, 5))

    # Calculate scores for each product
    product_scores = {}
    for pid, info in most_similar_products.items():
        # Add similar products to the scoring
        similar_pids = info[2]
        for similar_pid in similar_pids:
            if similar_pid not in product_scores:
                product_scores[similar_pid] = calculate_score(pid, info)
            else:
                # Accumulate scores if a product appears in multiple similar lists
                product_scores[similar_pid] += calculate_score(pid, info)

    # Sort products by score in descending order
    sorted_recommendations = sorted(
        product_scores.items(), 
        key=lambda x: x[1], 
        reverse=True
    )

    # Extract top recommendations, ensuring uniqueness
    recommendations = []
    for pid, score in sorted_recommendations:
        # Ensure no duplicates
        if pid not in recommendations:
            recommendations.append(pid)
            
            # Stop when we have enough recommendations
            if len(recommendations) >= num_recs_to_give:
                break

    # Ensure we return exactly num_recs_to_give recommendations
    return recommendations[:num_recs_to_give]
