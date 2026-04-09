# Project Roadmap: Danaa

This roadmap follows a "gradual implementation" approach, starting with minimal infrastructure and adding complexity only when necessary.

## Phase 1: Foundation (Minimal Bot) [IN PROGRESS]
**Goal:** Establish a basic Telegram bot that can interact with users.
- [x] Set up a project structure (Python/FastAPI).
- [x] Implement a basic backend to receive and respond to messages.
- [ ] Set up a Telegram bot via BotFather and obtain a token.
- [ ] Configure the webhook and deploy (e.g., local server with ngrok or AWS).
- [ ] **Outcome:** A bot that says "Hello, I'm Danaa!" and echoes back questions.

## Phase 2: AI Integration (General Knowledge) [NEXT]
**Goal:** Connect the bot to an AI model to answer general questions.
- [ ] Research and select a cheap/free AI API (OpenAI, Anthropic, or HuggingFace).
- [ ] Implement the AI service to process user questions.
- [ ] Update the bot to respond using the AI's general knowledge.
- [ ] **Outcome:** A bot that can answer general questions about Canada/Immigration.

## Phase 3: Knowledge Collection (Data Ingestion)
**Goal:** Prepare the community-provided history for processing.
- [ ] Develop a script to ingest Telegram history (JSON/CSV export).
- [ ] Clean and structure the data (remove PII, handle duplicate questions).
- [ ] **Outcome:** A structured "offline" knowledge base.

## Phase 4: Context Aware Intelligence (RAG)
**Goal:** Combine AI with community history for context-aware answers.
- [ ] Implement Retrieval-Augmented Generation (RAG).
- [ ] Ensure answers include citations (links/timestamps to original sources).
- [ ] **Outcome:** A sophisticated bot that synthesizes human-like, referenced answers from history.

## Phase 6: Conversation & Refinement
**Goal:** Allow for multi-turn discussions and feedback loops.
- [ ] Implement session/context management for back-and-forth.
- [ ] Add a user feedback mechanism (upvote/downvote answers).
- [ ] Refine the system based on real-world usage.
