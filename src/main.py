from sentence_transformers import SentenceTransformer

# Load a pretrained embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

sentences = [
    "How can I improve my laptop battery life?",
    "Ways to make a notebook last longer without charging.",
    "What are the best restaurants in Montreal?",
    "How do I extend the battery runtime of my computer?",
]

# Convert sentences into embeddings
embeddings = model.encode(sentences)

print("Embedding shape:", embeddings.shape)

for sentence, embedding in zip(sentences, embeddings):
    print(f"\nSentence: {sentence}")
    print(f"Vector dimensions: {len(embedding)}")
    print(f"First five values: {embedding[:5]}")