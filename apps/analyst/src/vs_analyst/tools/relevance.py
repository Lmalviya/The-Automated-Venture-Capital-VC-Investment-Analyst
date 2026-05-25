import math
import re
from typing import List, Set
from stop_words import get_stop_words

# Load standard, comprehensive list of English stopwords from stop-words library
STOPWORDS: Set[str] = set(get_stop_words("english"))

def tokenize(text: str) -> List[str]:
    """Tokenizes text into lowercase word tokens, stripping punctuation."""
    if not text:
        return []
    # Strip punctuation and split by whitespace
    words = re.findall(r'\b\w+\b', text.lower())
    return [w for w in words if w not in STOPWORDS]

def bm25_rank(query: str, documents: List[str], top_k: int = 5, k1: float = 1.5, b: float = 0.75) -> List[int]:
    """
    Ranks a list of documents against a query using the Okapi BM25 algorithm.
    Returns a list of integer indices of the documents, sorted in descending order of relevance.

    Args:
        query: The search query string.
        documents: A list of document or text strings to rank.
        top_k: Return up to top_k document indices.
        k1: Term frequency saturation parameter (default: 1.5).
        b: Document length normalization parameter (default: 0.75).
    """
    if not documents:
        return []
        
    query_tokens = tokenize(query)
    if not query_tokens:
        # If query contains no meaningful tokens after stopword removal, return default ordering
        return list(range(len(documents)))[:top_k]

    # Tokenize all documents and compute overall stats
    doc_tokens_list = [tokenize(doc) for doc in documents]
    doc_lengths = [len(tokens) for tokens in doc_tokens_list]
    avg_doc_length = sum(doc_lengths) / len(documents) if documents else 0
    num_docs = len(documents)

    # Compute Document Frequency (DF) for each query token
    df = {}
    for token in query_tokens:
        count = sum(1 for tokens in doc_tokens_list if token in tokens)
        df[token] = count

    scores = []
    for doc_idx, doc_tokens in enumerate(doc_tokens_list):
        score = 0.0
        doc_len = doc_lengths[doc_idx]
        
        # Calculate frequency of each term in the current document
        tf = {}
        for token in doc_tokens:
            tf[token] = tf.get(token, 0) + 1
            
        for token in query_tokens:
            n_q = df.get(token, 0)
            if n_q == 0:
                continue
                
            # Okapi BM25 IDF with natural log and safe addition of 1 to ensure positive values
            idf = math.log((num_docs - n_q + 0.5) / (n_q + 0.5) + 1.0)
            
            f_q = tf.get(token, 0)
            if f_q == 0:
                continue
                
            # BM25 Term scoring formula
            denominator = f_q + k1 * (1.0 - b + b * (doc_len / avg_doc_length if avg_doc_length > 0 else 1.0))
            term_score = idf * (f_q * (k1 + 1.0)) / denominator
            score += term_score
            
        scores.append((doc_idx, score))

    # Sort documents by score descending
    sorted_docs = sorted(scores, key=lambda x: x[1], reverse=True)
    
    # Return top K indices
    return [doc_idx for doc_idx, _ in sorted_docs[:top_k]]
