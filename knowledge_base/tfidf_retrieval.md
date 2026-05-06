# TF‑IDF retrieval (simple baseline retriever)

TF‑IDF is a sparse retrieval method that scores terms by:

- **TF (term frequency)**: how often a term appears in a document
- **IDF (inverse document frequency)**: down-weights terms that appear in many documents

In a simple RAG demo, TF‑IDF can be used to retrieve Top‑K chunks without requiring embeddings or external services.

Pros:

- Fast, offline, easy to implement
- No API key required

Cons:

- Lexical matching only (synonyms can be missed)
- Often weaker than embeddings for semantic retrieval
