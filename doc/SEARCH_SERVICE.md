# Danaa Search & Retrieval Service (RAG)

This document explains the architecture of the search layer that connects Danaa's AI to the community knowledge base.

## 1. Overview
The Search Service is the "Retriever" in our **Retrieval-Augmented Generation (RAG)** pipeline. Its job is to find the most relevant historical discussions from Telegram and provide them as context to the LLM (Groq/Llama).

## 2. The Search Algorithm (Keyword-Based)
Currently, Danaa uses a weighted keyword-matching algorithm designed for speed and transparency.

### A. Relevance Scoring
*   **Base Match**: Each keyword match in a message or discussion chain adds **+10 points** to the score.
*   **Chain Context**: When searching a "Conversation Chain," the algorithm looks at the combined text of the question and all replies to ensure context is captured.

### B. The "Smart" Ranking Factors
To ensure users get the *best* and *most accurate* advice, two additional factors are used:
1.  **Recency (Temporal Awareness)**:
    *   Later timestamps (higher Unix time) receive a boost.
    *   This ensures that 2026 information is prioritized over 2024 information, which is critical for changing immigration rules.
2.  **Popularity (Community Validation)**:
    *   The `sentiment_score` (Positive Reactions - Negative Reactions) is added to the total score.
    *   Discussions with many 👍 or ❤️ are ranked higher than those with no reactions or 👎.

## 3. Context Augmentation
Once the top 4-5 results are found, they are formatted into a structured "Context Block":
*   **Type Label**: Indicates if it's a "Discussion" or "Standalone Information."
*   **Timestamp**: Clearly states when the information was recorded.
*   **Anonymized Threads**: Presents the conversation flow while preserving user privacy (using hashes).

## 4. Integration with AI Service
The `SearchService` is called inside `get_ai_answer`. The resulting context is injected into the prompt as follows:
```text
User Question: [User's Input]
Community Context for Guidance:
[Search Results with Timestamps and User Hashes]
```

## 5. Future Enhancements
*   **Semantic Search (Vector Embeddings)**: Transition from keyword matching to "Meaning Matching" using ChromaDB or Pinecone.
*   **Multi-Group Filtering**: Allow users to specify if they want to search "PGWP" specifically or all groups.
*   **Expert Weighting**: Give higher scores to messages from users with a history of high-reaction answers.
