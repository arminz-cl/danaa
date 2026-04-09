# Project Roadmap: Danaa

This roadmap follows a "gradual implementation" approach, starting with minimal infrastructure and adding complexity only when necessary.

## Phase 1: Foundation (Minimal Bot) [IN PROGRESS]
**Goal:** Establish a basic Telegram bot that can interact with users.
- [x] Set up a project structure (Python/FastAPI).
- [x] Implement a basic backend to receive and respond to messages.
- [ ] Set up a Telegram bot via BotFather and obtain a token.
- [ ] Configure the webhook and deploy (e.g., local server with ngrok or AWS).
- [ ] **Outcome:** A bot that says "Hello, I'm Danaa!" and echoes back questions.

## Phase 2: Knowledge Collection (Data Ingestion)
**Goal:** Prepare the community-provided history for processing.
- [ ] Develop a script to ingest Telegram history (JSON/CSV export).
- [ ] Clean and structure the data (remove PII, handle duplicate questions).
- [ ] **Outcome:** A structured "offline" knowledge base (e.g., a large JSON file or simple local database).

## Phase 3: Simple Search (No AI)
**Goal:** Implement basic search functionality.
- [ ] Create a simple keyword or fuzzy-search mechanism.
- [ ] Respond with the most relevant historical question/answer found in Phase 2.
- [ ] **Outcome:** A bot that can provide "exact match" answers from history.

## Phase 4: Database Integration
**Goal:** Store knowledge and user interactions.
- [ ] Set up a cheap database (e.g., AWS DynamoDB or RDS).
- [ ] Store processed history and conversation logs.
- [ ] **Outcome:** A persistent knowledge base that is easy to query and scale.

## Phase 5: AI-Powered Intelligence (RAG)
**Goal:** Use AI to synthesize answers from multiple historical sources.
- [ ] Integrate a cheap/free AI API (e.g., OpenAI, Anthropic, or HuggingFace).
- [ ] Implement Retrieval-Augmented Generation (RAG).
- [ ] Ensure answers include citations (links/timestamps to original sources).
- [ ] **Outcome:** A sophisticated bot that generates human-like, referenced answers.

## Phase 6: Conversation & Refinement
**Goal:** Allow for multi-turn discussions and feedback loops.
- [ ] Implement session/context management for back-and-forth.
- [ ] Add a user feedback mechanism (upvote/downvote answers).
- [ ] Refine the system based on real-world usage.
