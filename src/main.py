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

# 2. Load the embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# 3. Convert all documents into embeddings
document_embeddings = model.encode(documents)

# 4. Get a search query
query = input("What would you like to search for? ")

# 5. Convert the query into an embedding
query_embedding = model.encode([query])

# 6. Calculate similarity between the query and every document
similarity_scores = cosine_similarity(
    query_embedding,
    document_embeddings
)[0]

# 7. Pair each document with its similarity score
results = list(zip(documents, similarity_scores))

# 8. Sort from most similar to least similar
results.sort(key=lambda result: result[1], reverse=True)

# 9. Display the top 5 results
print(f"\nResults for: {query}\n")

for document, score in results[:5]:
    print(f"{score:.4f} | {document}")