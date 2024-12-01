from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class ProductSimilarityComputer:
    def __init__(self, model='all-MiniLM-L6-v2', 
                 title_weight=0.6, 
                 description_weight=0.3, 
                 store_weight=0.1):
        """
        Initialize similarity computer with configurable weights
        
        :param model: Sentence transformer model to use
        :param title_weight: Weight for product title (recommended highest)
        :param description_weight: Weight for product description
        :param store_weight: Weight for store name
        """
        self.model = SentenceTransformer(model)
        self.weights = {
            'title': title_weight,
            'description': description_weight,
            'store': store_weight
        }
        
        # Validate weights sum to 1
        assert np.isclose(sum(self.weights.values()), 1.0), "Weights must sum to 1"
    
    def compute_product_similarity(self, product1, product2):
        """
        Compute weighted similarity between two products
        
        :param product1: Dict with 'title', 'description', 'store' keys
        :param product2: Dict with 'title', 'description', 'store' keys
        :return: Similarity score between 0 and 1
        """
        # Generate embeddings for each component
        embeddings = {
            'title': self.model.encode([product1['title'], product2['title']]),
            'description': self.model.encode([product1['description'], product2['description']]),
            'store': self.model.encode([product1['store'], product2['store']])
        }
        
        # Compute component-wise similarities
        component_similarities = {
            component: cosine_similarity(
                embeddings[component][0:1], 
                embeddings[component][1:2]
            )[0][0] for component in ['title', 'description', 'store']
        }
        
        # Compute weighted similarity
        weighted_similarity = sum(
            component_similarities[component] * self.weights[component] 
            for component in ['title', 'description', 'store']
        )
        
        return weighted_similarity

# Example usage
similarity_computer = ProductSimilarityComputer(
    title_weight=0.6,  # Strongest weight for title
    description_weight=0.3,
    store_weight=0.1
)

# Example products
product1 = {
    'title': 'Wireless Bluetooth Headphones',
    'description': 'High-quality noise-cancelling headphones with long battery life',
    'store': 'TechGadgets Online'
}

product2 = {
    'title': 'Bluetooth Wireless Headset',
    'description': 'Comfortable noise-reducing headphones with extended battery',
    'store': 'TechGadgets Online'
}

similarity = similarity_computer.compute_product_similarity(product1, product2)
print(f"Product Similarity: {similarity:.4f}")