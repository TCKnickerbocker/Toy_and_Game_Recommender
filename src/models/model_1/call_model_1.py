import requests
from flask import Flask, request, jsonify
import snowflake.connector
import model_1_helper_functions
import model_1_alg
from model_1_configs import CONNECTION_PARAMS

app = Flask(__name__)

def call_model_1(user_id, num_recently_rated, num_recs_to_give, by_title=False): 
    """
    Retrieve a list of the most similar product IDs based on description or title 
    and return the corresponding product details.

    :param user_id: str
        The ID of the user for whom recommendations are to be generated.
    :param num_recently_rated: int
        The number of products that the user has recently rated.
    :param num_recs_to_give: int
        The number of similar products to recommend.
    :param by_title: bool, optional (default=False)
        If True, similarity is calculated based on product titles. 
        If False, similarity is calculated based on product descriptions.
    :return: list
        A list of product details corresponding to the most similar product IDs.
    """
    conn = snowflake.connector.connect(**CONNECTION_PARAMS)
    most_similar_products = {}
    recently_rated_products = model_1_helper_functions.get_recently_rated_products_info(conn, user_id, num_recently_rated)  # [(productID, user's rating, if user favorited product)]
    
    # For each recently rated product_id, get similar product ids:    
    for rating_info in recently_rated_products:
        product_id = rating_info[0]
        if by_title:
            similar_product_ids = model_1_helper_functions.get_n_most_similar_product_ids(conn, product_id, n=num_recs_to_give, similarity_tablename='product_title_similarity', user_id=user_id)
        else:
            similar_product_ids = model_1_helper_functions.get_n_most_similar_product_ids(conn, rating_info[0], n=num_recs_to_give, similarity_tablename='product_description_similarity', user_id=user_id)
        most_similar_products[product_id] = [rating_info[1], rating_info[2], similar_product_ids]  # user's rating, whether user favorited, ordered list of similar product ids
        
    # Get products to recommend 
    product_ids_to_rec = model_1_alg.recommend_products(most_similar_products, num_recs_to_give)
    return model_1_helper_functions.get_products_by_product_ids(conn, product_ids_to_rec)

@app.route("/most_similar_products", methods=["GET"])
def most_similar_products():
    """
    API endpoint to retrieve the most similar products based on a given user ID.
    Accepts query parameters for the user ID, number of results, and whether to
    use title-based similarity (else defaults to description-based similarity).

    Query Parameters:
        - user_id: str (required)
        - num_recently_rated: int (optional, default=8)
        - num_recs_to_give: int (optional, default=8)
        - by_title: bool (optional, default=False)

    Returns:
        - JSON response containing the most similar products or an error message.
    """
    try:
        # Extract query parameters
        user_id = request.args.get('user_id', "dummyUser")  # Default user ID if not provided
        num_recently_rated = int(request.args.get('num_recently_rated', 8))  # Default to 8 if not provided
        num_recs_to_give = int(request.args.get('num_recs_to_give', 8))  # Default to 8 if not provided
        by_title = request.args.get('by_title', 'false').lower() == 'true'  # Convert to boolean

        # Call the model function
        products_json = call_model_1(user_id=user_id, num_recently_rated=num_recently_rated, num_recs_to_give=num_recs_to_give, by_title=by_title)
        
        # Return a success response
        return jsonify({"recommended_products": products_json}), 200

    except Exception as e:
        # Log & return the error
        print(f"Error in /api/most_similar_products: {e}")
        return jsonify({"error": "Failed to retrieve most similar products", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5003)  # Expose the service on port 5003
