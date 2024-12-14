import os
import concurrent.futures

def rank_products_with_llm(
    product_id, 
    similar_products, 
    original_product_title=None, 
    model='gpt-4o-mini', 
    api_provider='openai' 
):
    print(f"Num products being ranked: {len(similar_products)}")
    """
    Rank and prune product recommendations using an LLM.
    
    Args:
    - product_id: The original product ID
    - similar_products: List of tuples (product_id, similarity_score, title, oyt_score, combined_score)
    - original_product_title: Optional title of the original product for context
    - model: The language model to use for ranking (default: 'gpt-4o-mini')
    - api_provider: The API provider ('openai' or 'phi3')
    
    Returns:
    - List of ranked and pruned product IDs
    """
    # Prepare the prompt for the LLM
    prompt = (
        "Rank these products for recommendation based on their similarity, relevance, and potential user interest. "
        f"The original product is: '{original_product_title}'. "
        
        "Provide a comprehensive evaluation and ranked list of product IDs, with the most promising recommendations listed first. "
        "In your ranking, systematically consider the following critical factors:\n"
        "- Semantic similarity to the original product\n"
        "- Potential alignment with user preferences\n"
        "- Nuanced product characteristics and attributes\n"
        "- OYT score (overall review sentiment), which provides insight into product satisfaction\n\n"
        
        "Methodology for ranking:\n"
        "1. Calculate a composite score that integrates:\n"
        "   a) Semantic similarity weight\n"
        "   b) OYT score weight\n"
        "   c) Product characteristic compatibility\n"
        "2. Rank products based on this comprehensive composite score\n\n"
        
        "The objective is to generate a curated list of product recommendations that a user who appreciated the original product would find compelling. "
        "Format your response as a precise, comma-separated list of product IDs, ordered from most to least recommended.\n\n"
    )

    # Prepare product information for the prompt
    product_details = "\n".join([
        f"Product ID: {prod[0]}, Title: {prod[2]}, " \
        f"Similarity Score: {prod[1]}, " \
        f"OYT Score: {prod[3]}, " \
        f"Combined Score: {prod[4]}"
        for prod in similar_products
    ])

    # Rank using OpenAI's API (GPT models)
    if api_provider == 'openai':
        from openai import OpenAI
        
        # Ensure OpenAI API key is set
        if not os.getenv('OPENAI_API_KEY'):
            raise ValueError("OpenAI API key must be set in environment variable OPENAI_API_KEY")
        
        # Initialize OpenAI client
        client = OpenAI()
        
        try:
            # Call selected model to rank products
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that ranks product recommendations based on multiple sophisticated criteria."},
                    {"role": "user", "content": prompt + product_details}
                ],
                max_tokens=500,
                temperature=0.4
            )
            
            # Extract and parse the ranked product IDs
            ranked_response = response.choices[0].message.content.strip()
            ranked_product_ids = [pid.strip() for pid in ranked_response.split(',')]
            print(f"post-gpt ranking: {ranked_product_ids}")

            return ranked_product_ids
        
        except Exception as e:
            # Fallback to original method if LLM call fails
            print(f"OpenAI model ranking failed: {e}")
            return [prod[0] for prod in similar_products[:len(similar_products)//2]]
    
    # Rank using Phi3 TODO: Get working
    elif api_provider == 'phi3':
        # Support for Phi3 via Azure AI or local inference
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        
        # Determine Phi3 model path or endpoint
        model_path = os.getenv('PHI3_MODEL_PATH', 'microsoft/Phi-3-mini-4k-instruct')
        
        try:
            # Load Phi3 model and tokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForCausalLM.from_pretrained(
                model_path, 
                torch_dtype=torch.float16, 
                device_map='auto'
            )
            
            # Prepare full prompt for Phi3
            full_prompt = f"System: You are a helpful assistant that ranks product recommendations based on multiple sophisticated criteria.\n\nUser: {prompt + product_details}\n\nAssistant:"
            
            # Tokenize and generate response
            inputs = tokenizer(full_prompt, return_tensors="pt", add_special_tokens=True).to(model.device)
            
            outputs = model.generate(
                inputs.input_ids, 
                max_new_tokens=500, 
                temperature=0.4,
                do_sample=True
            )
            
            # Decode the response
            ranked_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract product IDs (you might need to adjust this parsing logic)
            ranked_product_ids = [
                pid.strip() 
                for pid in ranked_response.split(',') 
                if pid.strip().isdigit()
            ]
            return ranked_product_ids
        
        except Exception as e:
            # Fallback to original method if Phi3 ranking fails
            print(f"Phi3 model ranking failed: {e}")
            return [prod[0] for prod in similar_products[:len(similar_products)//2]]
    
    else:
        raise ValueError(f"Unsupported API provider: {api_provider}")

def get_n_most_similar_product_ids_model_4(
    conn, 
    product_id, 
    similarity_tablename='product_description_similarity', 
    oyt_tablename='oyt_scores_of_most_popular_products', 
    n=8, 
    user_id=None,
    ranking_model='gpt-4o',
    ranking_api_provider='openai'
):
    # Validate inputs
    if not isinstance(n, int) or n <= 0:
        raise ValueError("n must be a positive integer")
    
    # Validate table names (basic check)
    safe_tables = [similarity_tablename, oyt_tablename]
    for table in safe_tables:
        if not table.replace('_', '').isalnum():
            raise ValueError(f"Invalid table name: {table}")
    
    # Fetch more recommendations than needed
    fetch_n = n*2
    
    # Fetch the original product title for context
    with conn.cursor() as cur:
        cur.execute("SELECT title FROM products_for_display WHERE productid = %s", (product_id,))
        original_product_title = cur.fetchone()[0] if cur.rowcount > 0 else None
    
    # Build the query string with the validated n value
    if user_id:
        query = f"""
        WITH similar_products AS (
            (
                SELECT 
                    s.product2_id AS similar_product_id, 
                    s.similarity_score,
                    p.title
                FROM {similarity_tablename} s
                JOIN products_for_display p ON s.product2_id = p.productid
                WHERE s.product1_id = %s
                AND s.product2_id NOT IN (
                    SELECT parent_asin 
                    FROM user_ratings 
                    WHERE user_id = %s
                )
            )
            UNION ALL
            (
                SELECT 
                    s.product1_id AS similar_product_id, 
                    s.similarity_score,
                    p.title
                FROM {similarity_tablename} s
                JOIN products_for_display p ON s.product1_id = p.productid
                WHERE s.product2_id = %s
                AND s.product1_id NOT IN (
                    SELECT parent_asin 
                    FROM user_ratings 
                    WHERE user_id = %s
                )
            )
        )
        SELECT 
            sp.similar_product_id,
            sp.similarity_score,
            sp.title,
            oyt.oyt_score,
            (sp.similarity_score + COALESCE(oyt.oyt_score, 0)) AS combined_score
        FROM 
            similar_products sp
        LEFT JOIN 
            {oyt_tablename} oyt
        ON 
            sp.similar_product_id = oyt.PRODUCT_ID
        ORDER BY 
            combined_score DESC
        LIMIT %s;
        """
    else:
        query = f"""
        WITH similar_products AS (
            (
                SELECT 
                    s.product2_id AS similar_product_id, 
                    s.similarity_score,
                    p.title
                FROM {similarity_tablename} s
                JOIN products_for_display p ON s.product2_id = p.productid
                WHERE s.product1_id = %s
            )
            UNION ALL
            (
                SELECT 
                    s.product1_id AS similar_product_id, 
                    s.similarity_score,
                    p.title
                FROM {similarity_tablename} s
                JOIN products_for_display p ON s.product1_id = p.productid
                WHERE s.product2_id = %s
            )
        )
        SELECT 
            sp.similar_product_id,
            sp.similarity_score,
            sp.title,
            oyt.oyt_score,
            (sp.similarity_score + COALESCE(oyt.oyt_score, 0)) AS combined_score
        FROM 
            similar_products sp
        LEFT JOIN 
            {oyt_tablename} oyt
        ON 
            sp.similar_product_id = oyt.PRODUCT_ID
        ORDER BY 
            combined_score DESC
        LIMIT %s;
        """

    # Execute the query with parameterized values
    with conn.cursor() as cur:
        if user_id:
            cur.execute(query, (product_id, user_id, product_id, user_id, fetch_n))
        else:
            cur.execute(query, (product_id, product_id, fetch_n))
        top_similar_products = cur.fetchall()
    
    # Prepare data for LLM ranking
    res = [(row[0], row[1], row[2], row[3], row[4]) for row in top_similar_products]  # id simscore title oytscore avg(oyt+sim)
    
    # Rank and prune recommendations using selected LLM
    ranked_product_ids = rank_products_with_llm(
        product_id, 
        res, 
        original_product_title,
        model=ranking_model,
        api_provider=ranking_api_provider
    )
    
    # Truncate to original requested number of recommendations
    return ranked_product_ids[:fetch_n//2]


def get_products_by_product_ids(conn, product_ids, product_table='products_for_display'):
    """
    Retrieve product details for multiple product IDs from Snowflake.
    The results are returned as a list of products, where each product is a dictionary.
    """
    # Function to fetch product data for a single product_id
    def fetch_product_data(product_id):
        with conn.cursor() as cur:
            cur.execute(f"""
            SELECT productid, title, image, summary
            FROM {product_table}
            WHERE productid = %s
            """, (product_id,))
            row = cur.fetchone()
            if row:
                return {
                    "productid": row[0],
                    "title": row[1],
                    "image": row[2],
                    "summary": row[3]
                }
            return None  # Return None if no data is found for the product_id

    # Use ThreadPoolExecutor to fetch data concurrently for all product_ids
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Map the product_ids to the fetch_product_data function
        results = list(executor.map(fetch_product_data, product_ids))

    # Filter out None results (in case some product_ids did not have data)
    products = [result for result in results if result is not None]
    return products

def get_recently_rated_products_info(conn, user_id, num_recently_rated):
    """
    Returns [(productID, user's rating, if user favorited product)]
    """
    query = """
    SELECT parent_asin, rating, favorite FROM user_ratings 
    WHERE user_id = %s
    ORDER BY review_id DESC
    LIMIT %s
    """
    try:
        with conn.cursor() as cur:
            cur.execute(query, (user_id, num_recently_rated))
            top_similar_products = cur.fetchall()
            recently_rated_products = [(row[0], row[1], row[2]) for row in top_similar_products]
            return recently_rated_products
    except Exception as e:
        print(f"Error getting recently_rated_products e: {e}")
        return None
