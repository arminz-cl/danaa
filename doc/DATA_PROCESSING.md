# Danaa Data Processing Guide

This document outlines the architecture for transforming raw Telegram JSON exports into a structured knowledge base.

## 1. Information Types

### A. Conversational Chains (Threaded Q&A)
*   **Definition**: A sequence of messages linked by `reply_to_message_id`.
*   **Structure**: Root Question -> Multiple Answers -> Clarifications.
*   **Value**: Captures the "how-to" and "why" of community knowledge.
*   **Processing Rule**: If a message has a `reply_to_message_id`, it must be attached to its parent. If a message receives multiple replies, they form a "Discussion Tree."

### B. Individual Informational Messages (News/Alerts)
*   **Definition**: Messages without replies that contain high-density information (e.g., "The new PGWP policy was just released...").
*   **Value**: Captures news, links, and official updates.
*   **Processing Rule**: Filter by length or keyword density. Short "Ok" or "Thanks" messages are discarded.

## 2. Temporal Awareness
*   **Criticality**: Immigration rules change. An answer from 2022 may be dangerous in 2026.
*   **Data Requirement**: Every piece of information MUST retain its `date` and `date_unixtime`.
*   **Validity Logic**: The AI should be instructed to prefer more recent entries in a chain.

## 3. Privacy & Security (PII Scrubbing)
*   **User Anonymization**: Replace `from` and `from_id` with a SHA-256 hash (e.g., `user_a7b2...`). This allows tracking "Expert" users without knowing their identity.
*   **Regex Scrubbing**:
    *   **Phone Numbers**: `(\+?\d{1,3}[- ]?)?\d{10}` (Covers CA/IR).
    *   **Emails**: `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`.
    *   **Addresses**: Keywords like "خیابان", "کوچه", "پلاک" followed by numbers.

## 4. Output Format
Processed data should be saved as a list of "Knowledge Objects":
```json
{
  "id": "chain_123",
  "type": "conversation_chain",
  "timestamp": "2026-03-01T00:16:53",
  "group": "pgwp",
  "messages": [
    {"role": "question", "text": "...", "user_hash": "..."},
    {"role": "answer", "text": "...", "user_hash": "..."}
  ]
}
```
