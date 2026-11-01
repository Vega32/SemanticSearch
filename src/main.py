from pathlib import Path

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# 1. Load documents from the text file
file_path = Path(__file__).parent.parent / "data" / "documents.txt"

documents = [
    line.strip()
    for line in file_path.read_text(encoding="utf-8").splitlines()
    if line.strip()
]

if not documents:
    raise ValueError("No documents found in documents.txt")

evaluation_queries = [
    {
        "query": "How can I make my laptop battery last longer?",
        "relevant": [
            "A laptop battery loses capacity over time as it goes through charge cycles.",
            "Reducing screen brightness can help a laptop battery last longer.",
            "Closing unnecessary background applications can reduce power consumption."
        ]
    },
    {
        "query": "How can I improve my physical health?",
        "relevant": [
            "Regular exercise can improve cardiovascular health and overall fitness.",
            "A balanced diet provides the nutrients needed for normal body functions."
        ]
    },
    {
        "query": "How do computers learn from information?",
        "relevant": [
            "Machine learning models learn patterns from data to make predictions.",
            "Neural networks are machine learning models inspired by interconnected neurons."
        ]
    }
]

def search(query, top_k=5):
    query_embedding = model.encode([query])

    scores = cosine_similarity(
        query_embedding,
        document_embeddings
    )[0]

    results = list(zip(documents, scores))
    results.sort(key=lambda result: result[1], reverse=True)

    return results[:top_k]


def precision_at_k(results, relevant_documents):
    retrieved_documents = {document for document, score in results}

    relevant_retrieved = retrieved_documents.intersection(
        relevant_documents
    )

    return len(relevant_retrieved) / len(results)


def recall_at_k(results, relevant_documents):
    retrieved_documents = {document for document, score in results}

    relevant_retrieved = retrieved_documents.intersection(
        relevant_documents
    )

    return len(relevant_retrieved) / len(relevant_documents)

# 2. Load the embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# 3. Convert all documents into embeddings
document_embeddings = model.encode(documents)

# Evaluate the search engine
K = 3

print(f"\nEvaluating search quality (K={K})\n")

precision_scores = []
recall_scores = []

for test_case in evaluation_queries:
    query = test_case["query"]
    relevant_documents = set(test_case["relevant"])

    results = search(query, top_k=K)

    precision = precision_at_k(results, relevant_documents)
    recall = recall_at_k(results, relevant_documents)

    precision_scores.append(precision)
    recall_scores.append(recall)

    print(f"Query: {query}")
    print(f"Precision@{K}: {precision:.2f}")
    print(f"Recall@{K}:    {recall:.2f}")

    print("Retrieved documents:")

    for document, score in results:
        print(f"  {score:.4f} | {document}")

    print()

# Calculate average scores across all test queries
average_precision = sum(precision_scores) / len(precision_scores)
average_recall = sum(recall_scores) / len(recall_scores)

print("Overall evaluation:")
print(f"Average Precision@{K}: {average_precision:.2f}")
print(f"Average Recall@{K}:    {average_recall:.2f}")