# Project Rules & Guidelines: Danaa

These rules govern all technical and operational aspects of the Danaa project.

## 1. Privacy & Security
- **No PII:** Personally Identifiable Information (names, phone numbers, addresses) MUST be scrubbed from the Telegram history before storage or AI processing.
- **Anonymization:** User identifiers should be hashed or anonymized where possible.
- **Data Protection:** All storage (S3, RDS, DynamoDB) must use encryption at rest.

## 2. Open Source & Portfolio Integrity
- **Public Visibility:** This project is intended for a public GitHub repository to showcase skills for a resume.
- **Credential Safety:** NEVER commit `.env` files, API keys, or AWS credentials. Use `.gitignore` rigorously.
- **History Hygiene:** If sensitive data is accidentally committed, the git history must be purged immediately.
- **Code Quality:** Maintain high standards for code readability, documentation, and commit messages to ensure it reflects well as a professional portfolio piece.

## 3. Data Ethics & Legal Compliance
- **Publicly Available Content Only:** The bot MUST only ingest data from public channels/groups where the information is already accessible to the community.
- **Citations & Provenance:** Every answer provided by the bot must include a citation of the source message/group and a timestamp.
- **Information, Not Advice:** The bot must include a mandatory disclaimer that it provides *information based on community history*, not legal, financial, or immigration advice.
- **Accuracy Warning:** Every response must explicitly state: "Information may be outdated or inaccurate; verify with official sources."

## 4. Cost Efficiency
- **AWS Free Tier:** Maximize use of AWS Free Tier services (Lambda, DynamoDB Free Tier, etc.).
- **Minimalist Approach:** Do not add a database until the "Simple Search" phase requires persistence beyond a static file.
- **AI Selection:** Prefer "Free Tier" or "Pay-as-you-go" AI APIs with the lowest possible cost-per-token.

## 5. Implementation Workflow
- **Plan Before Act:** For every major task, a short written plan must be reviewed and approved.
- **Read-Only Actions:** For read-only tools (such as checking running processes, reading git info, reading files) that don't modify or impact anything, permission is not needed.
- **Git Protocol:** NEVER suggest, `git commit`, or `git push` changes unless explicitly requested by the user. I will only perform or propose git operations when you ask for them.
- **Gradual Complexity:** Each phase must be functional and testable before moving to the next.
- **Testing:** Every new feature should include automated tests to verify its core logic.

## 6. Architectural Standards
- **Modular Design:** Keep the data ingestion, search, and Telegram bot layers decoupled.
- **Asynchronous Processing:** Prefer event-driven architectures (e.g., SQS + Lambda) for long-running tasks.
- **Documentation:** Every major architectural change must be documented in the `doc/` directory.

## 7. Data Persistence & Integrity
- **Persistence Mandate:** Do NOT drop, overwrite with empty data, or delete "hard processed" files (e.g., cleaned data, knowledge cards, vector stores) without explicit user permission.
- **Versioning Strategy:** Unless explicitly requested otherwise, always implement a versioning or backup strategy when updating processed data files (e.g., timestamped files or `.bak` backups) to ensure data safety.
- **Safe Writes:** Implement validation checks (e.g., non-empty check) before saving or updating persistent data files to prevent accidental data loss during failures.
