import sys
import json
sys.path.append("../")
sys.path.append("../configs")
from configs import model_config
import generator_funcs
from domain_expander import DomainExpander

def call_generate_products(user_id=None, num_products=1):
    # Table to insert items into
    target_table = "ai_generated_products"
    
    # Fall back to testing user ID if no user_id found
    if not user_id:
        user_id = model_config.TESTING_USER_ID
        model_config.LOGGER.info(f"No user_id provided. Falling back to testing user ID: {user_id}")
    
    # Initialize creative product generator
    domain_expander = DomainExpander()
    product_generator = generator_funcs.CreativeProductGenerator(model_config.CONNECTION_PARAMS, domain_expander, max_workers=5)
    
    # Generate products
    generated_products = product_generator.generate_creative_products(
        target_table=target_table, 
        num_products=num_products,
        user_id=user_id
    )
    
    # Convert to JSON for API response
    json_products = generated_products
    print(json.dumps(json_products, indent=2))
    
    return generated_products

if __name__ == "__main__":
    call_generate_products()
