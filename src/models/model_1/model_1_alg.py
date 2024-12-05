
def recommend_products(most_similar_products, num_recs_to_give):
    # Calculate weights based on ratings
    print(len(most_similar_products))
    total_ratings = sum([info[0] for info in most_similar_products.values()])
    weights = {pid: info[0] / total_ratings for pid, info in most_similar_products.items()}
    
    recommendations = []
    for pid, weight in weights.items():
        num_recs = round((weight * num_recs_to_give))
        if num_recs == 0:
            num_recs = 1
        print(most_similar_products[pid][2][:num_recs])
        recommendations.extend(most_similar_products[pid][2][:num_recs])
    
    # Ensure unique recommendations and limit to num_recs_to_give
    recommendations = list(dict.fromkeys(recommendations))[:num_recs_to_give]
    print(num_recs_to_give)
    print(len(recommendations))
    return recommendations

