# AI Model Comparison & Strategy: Danaa (2025)

This document tracks the intelligence, cost, and capacity of various AI models evaluated for the Danaa project.

## 1. Master Model Comparison Table

| Model Name | IQ (1-10) | Farsi Quality (1-10) | Free Tier (Tokens/Day) | Paid Cost (per 1M) | RPM (Free/Paid) | Efficiency (Items/min) | Project Role | Notes |
| :--- | :---: | :---: | :--- | :--- | :---: | :---: | :--- | :--- |
| **1. OpenAI o1** | **10.0** | **9.5** | None | $15.00 | 0 / 1k | 10 | None | High-end logic model. |
| **2. Claude 3.5 Sonnet** | **9.5** | **10.0** | ~20k | $3.00 | 5 / 50 | 50 | None | Best for natural Persian "Persona". |
| **3. GPT-4o** | **9.5** | **9.0** | ~200k | $2.50 | 3 / 500 | 100 | None | Industry standard for extraction. |
| **4. Claude 3 Opus** | **9.5** | **9.5** | None | $15.00 | 0 / 50 | 20 | None | Extremely thorough research model. |
| **5. Gemini 1.5 Pro** | **9.5** | **9.0** | ~32k | $3.50 | 2 / 150 | 100 | None | Best for massive context windows. |
| **6. Llama 3.3 70B** | **9.0** | **8.5** | **100k** | **$0.59** | 15 / 1k | 300 | None | Former extractor (reached free limit). |
| **7. DeepSeek-V3** | **9.0** | **8.0** | Variable | $0.27 | High / Unl. | 500 | None | Cheapest high-IQ model. |
| **8. DeepSeek-R1** | **9.0** | **7.5** | Variable | $0.55 | High / Unl. | 200 | None | Open-source reasoning model. |
| **9. Mistral Large 2** | **9.0** | **8.0** | 50k | $2.00 | 1 / 300 | 80 | None | Excellent European model. |
| **10. Qwen 2.5 72B** | **8.5** | **7.0** | 100k | $0.40 | 30 / 500 | 400 | None | Fast Chinese model. |
| **11. GPT-4o-mini** | **8.0** | **8.5** | ~200k | $0.15 | 3 / 3.5k | 1,000 | None | Best candidate for future chatbot. |
| **12. Claude 3.5 Haiku** | **8.0** | **8.5** | ~10k | $0.25 | 5 / 50 | 200 | None | Fast and concise reasoning. |
| **13. Gemini 2.0 Flash** | **8.0** | **9.0** | **1M** | $0.10 | 15 / 2k | 2,000+ | **Extractor & Bot** | **High-speed 2.0 model.** |
| **14. Llama 3.1 70B** | **8.0** | **8.0** | 100k | $0.59 | 15 / 1k | 300 | None | Solid all-rounder model. |
| **15. Command R+** | **8.0** | **8.0** | ~50k | $2.00 | 20 / 500 | 150 | None | RAG and Tool-use specialist. |
| **16. Mistral Small** | **7.5** | **7.0** | 50k | $0.20 | 1 / 300 | 500 | None | Efficient for simple summaries. |
| **17. Mixtral 8x7B** | **7.0** | **6.5** | 100k | $0.50 | 30 / 1k | 800 | None | Good for basic data tasks. |
| **18. Llama 3.1 8B** | **6.5** | **7.0** | **500k** | **$0.05** | 30 / 2k | 2,500 | **None** | **Instant response speed.** |
| **19. Gemini 1.5 Flash** | **7.5** | **8.5** | **1M** | **$0.07** | 15 / 2k | 1,500 | **None** | **Great "Free Freedom" choice.** |
| **20. Mistral Nemo** | **6.5** | **7.0** | 50k | $0.30 | 1 / 300 | 400 | None | Efficient small model. |

## 2. Current Implementation Strategy

- **Knowledge Extraction:** **Gemini 2.0 Flash (Google AI Studio)**
  - **Role:** Mining and distilling Telegram chat history into Knowledge Cards.
  - **Rationale:** High daily free limit (1M tokens) and superior speed/multimodal reasoning of version 2.0.
  - **Config:** `v1beta` API with `response_mime_type: "application/json"`.

- **User Response (Chatbot):** **Gemini 2.0 Flash (Google AI Studio)**
  - **Role:** Real-time Telegram interaction.
  - **Rationale:** 2.0 Flash offers near-instant latency similar to small models but with much higher reasoning capabilities.
  - **Context:** Augmented with search results from both raw snippets and distilled knowledge cards.

## 3. Cost & Safety Controls

- **Prepaid Models (Groq/OpenAI):** Spending is capped by the account balance. Deposits of $5-$10 ensure no overages.
- **Quota-Based Models (Gemini):** Hard quotas are set in Google Cloud Console to prevent accidental billing on the free tier.
- **Data Integrity:** Per `RULES.md`, hard-processed data is never overwritten or deleted without confirmation.
