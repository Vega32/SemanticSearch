def chunk_text(
    text: str,
    source: str,
    chunk_size: int = 200,
    overlap: int = 40
) -> list[dict]:

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "Overlap must be non-negative and smaller than chunk size."
        )

    words = text.split()

    if not words:
        return []

    chunks = []

    step = chunk_size - overlap

    for start in range(0, len(words), step):

        end = start + chunk_size

        chunk_words = words[start:end]

        if not chunk_words:
            break

        chunks.append({
            "source": source,
            "chunk_index": len(chunks),
            "text": " ".join(chunk_words),
            "word_count": len(chunk_words)
        })

    return chunks
