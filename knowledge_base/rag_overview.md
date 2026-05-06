# RAG overview

Retrieval-Augmented Generation (RAG) combines **retrieval** (finding relevant documents) with **generation** (producing an answer).

## Why use RAG

- Ground answers in a specific knowledge base
- Reduce hallucinations by providing evidence
- Keep domain information up to date without re-training the model

## Typical pipeline

1. Split documents into chunks
2. Build an index (e.g., TF‑IDF, embeddings)
3. Retrieve Top‑K chunks for a query
4. Put retrieved context into the prompt
5. Generate an answer
