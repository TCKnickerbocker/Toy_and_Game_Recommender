from flask import Flask, request, jsonify
from generator_configs import LOGGER, TESTING_USER_ID, CONNECTION_PARAMS
import generator_funcs
from domain_expander import DomainExpander

app = Flask(__name__)

def call_generate_products(user_id=None, num_products=1, store_image_in_s3=False):
    target_table = "ai_generated_products"
    
    if not user_id:
        user_id = TESTING_USER_ID
        LOGGER.info(f"No user_id provided. Falling back to testing user ID: {user_id}")
    domain_expander = DomainExpander()
    product_generator = generator_funcs.CreativeProductGenerator(CONNECTION_PARAMS, domain_expander, max_workers=5)
    
    generated_products = product_generator.generate_creative_products(
        target_table=target_table, 
        num_products=num_products,
        user_id=user_id,
        # TODO: Set to True once a basic deployment is working ?   
        store_image_in_s3=store_image_in_s3
    )
    return generated_products

@app.route('/generate_fake_product', methods=['POST'])
def generate_products():
    # Get the parameters from the JSON body of the request
    data = request.get_json()
    user_id = data.get('user_id', None)
    num_products = data.get('num_products', 1)
    print(f"Generating {num_products} new products...")
    
    # Call the generate function
    generated_products = call_generate_products(user_id=user_id, num_products=num_products)
    
    # Return the response as JSON
    return jsonify(generated_products), 200

if __name__ == "__main__":
    # app.run(debug=True, host="0.0.0.0", port=5007)
    # call_generate_products(store_image_in_s3=True)
    call_generate_products(store_image_in_s3=False)
    
