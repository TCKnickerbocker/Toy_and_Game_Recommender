import sys
sys.path.append("../configs")
import model_config
from generator import CreativeProductGenerator

def main():
    # Configure connection parameters from environment variables
    source_table = "most_popular_products"
    target_table = "ai_generated_products"
    
    # Initialize creative product generator
    product_generator = CreativeProductGenerator(model_config.CONNECTION_PARAMS, max_workers=5)
    product_generator.generate_creative_products(
        source_table=source_table, 
        target_table=target_table, 
        num_products=1,
        # TODO: Replace with userId from front-end
        user_id=model_config.TESTING_USER_ID
    )

if __name__ == "__main__":
    main()