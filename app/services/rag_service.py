from app.embedding import generate_embedding, rank_chunks_by_similarity


def get_context_from_question(
    question: str, chunk_embeddings: list[dict]
) -> tuple[str, list[dict]]:
    query_embedding = generate_embedding(question)
    scores = rank_chunks_by_similarity(query_embedding, chunk_embeddings)

    top_items = scores[:3]
    top_chunks = [item["text"] for item in top_items]
    context = "\n\n".join(top_chunks)

    sources = [
        {
            "score": item["score"],
            "text_preview": item["text"][:200]
        }
        for item in top_items
    ]

    return context, sources
