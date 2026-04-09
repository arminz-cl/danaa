# Project: Danaa (دانـا)

## Overview
**Danaa** is an AI-powered Telegram bot designed to assist Iranian immigrants in Canada. It leverages the historical knowledge captured in popular Telegram groups to provide accurate, context-aware answers to questions about immigration, legal procedures, insurance, and financial systems.

## Core Problem
Iranian immigrants frequently ask the same questions in large Telegram groups. While the information exists in the group history, it is:
1.  **Hard to Search:** Telegram's native search is limited and doesn't understand context.
2.  **Uncertain & Slow:** Users must wait for a manual response, which may never come or take hours to arrive.
3.  **Group Spam:** Repetitive questions clutter active groups, making it harder to find new, unique discussions.
4.  **Outdated:** Information changes (e.g., immigration rules), and old group messages don't automatically update.

## Vision
To provide a reliable, privacy-conscious, and always-available "knowledge companion" that helps immigrants navigate the complexities of life in Canada by drawing on the collective experience of their community. **Danaa provides information based on community history; it does not provide legal or professional advice.**

## Key Principles
1.  **Community-Driven:** Base answers on real community interactions from publicly available sources.
2.  **Transparency:** Clearly cite sources and provide timestamps to allow users to verify information.
3.  **Accuracy Awareness:** Explicitly warn users that information may be outdated or inaccurate.
4.  **Temporal Awareness:** Prioritize recent information, as rules and procedures change.
5.  **Privacy First:** Ensure no personally identifiable information (PII) is exposed.
6.  **Lean Development:** Start with minimal, cost-effective infrastructure (Free/Cheap APIs, AWS).

## Technical Strategy
-   **Frontend:** Telegram Bot API.
-   **Backend:** Python (FastAPI) or Node.js (Express) - *To be finalized*.
-   **Knowledge Base:** Processed history from Telegram groups.
-   **Intelligence:** RAG (Retrieval-Augmented Generation) with an emphasis on citations and timestamps.
-   **Infrastructure:** AWS (Lambda, DynamoDB/RDS, S3) for low-cost scalability.
