from transformers import pipeline

def analyze_sentiment(text_list):
    """
    Analyze sentiment for a list of texts using Huggingface's sentiment analysis pipeline.
    Returns a list of sentiment scores.
    """
    sentiment_pipeline = pipeline("sentiment-analysis")
    results = sentiment_pipeline(text_list)
    return [{"text": text, "label": res["label"], "score": res["score"]} for text, res in zip(text_list, results)]

if __name__ == "__main__":
    sample_texts = [
        "This toy is amazing and super fun!",
        "Not worth the money, very disappointing.",
        "Great educational toy for young kids."
    ]
    sentiments = analyze_sentiment(sample_texts)
    for sentiment in sentiments:
        print(sentiment)
