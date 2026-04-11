import json
import asyncio
import os
import sys

# Add project root to path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ai_service import get_ai_answer

DATA_PATH = "data/processed/pgwp_cleaned.json"
JSON_OUTPUT_PATH = "QA/dataset_results.json"
HTML_OUTPUT_PATH = "QA/dashboard_standalone.html"

# HTML Template with Placeholder for Data
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Danaa RAG Quality Dashboard (Standalone)</title>
    <style>
        body {
            font-family: Tahoma, 'Vazir', Arial, sans-serif;
            background-color: #f4f7f6;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            margin-bottom: 30px;
        }
        .sample-card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 40px;
            overflow: hidden;
            border: 1px solid #ddd;
        }
        .card-header {
            background: #2c3e50;
            color: white;
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .grid-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0;
            border-top: 1px solid #eee;
        }
        .column {
            padding: 20px;
        }
        .human-col {
            background-color: #f9f9f9;
            border-left: 1px solid #eee;
        }
        .ai-col {
            background-color: #ffffff;
        }
        h3 {
            margin-top: 0;
            color: #2980b9;
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
            display: inline-block;
        }
        .section {
            margin-bottom: 20px;
        }
        .label {
            font-weight: bold;
            color: #7f8c8d;
            font-size: 0.9em;
            display: block;
            margin-bottom: 5px;
        }
        .content {
            white-space: pre-wrap;
            line-height: 1.6;
        }
        .question-box {
            background: #e8f4fd;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            border-right: 5px solid #3498db;
        }
        .context-toggle {
            background: #95a5a6;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 0.8em;
        }
        .context-box {
            display: none;
            background: #27ae6011;
            padding: 15px;
            margin-top: 10px;
            border-radius: 5px;
            font-size: 0.85em;
            border-right: 5px solid #27ae60;
        }
        .tag {
            font-size: 0.7em;
            padding: 2px 6px;
            border-radius: 10px;
            text-transform: uppercase;
            margin-right: 10px;
        }
        .tag-human { background: #e67e22; color: white; }
        .tag-ai { background: #9b59b6; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 داشبورد کیفیت پاسخ‌های دانا (نسخه آفلاین)</h1>
            <p>مقایسه پاسخ‌های واقعی جامعه با پاسخ‌های هوش مصنوعی</p>
        </header>

        <div id="dashboard-content">
            <!-- Samples will be injected here -->
        </div>
    </div>

    <script>
        // DATA EMBEDDED DIRECTLY
        const dataset = JSON_DATA_PLACEHOLDER;

        function renderDashboard(samples) {
            const container = document.getElementById('dashboard-content');
            container.innerHTML = '';

            samples.forEach((sample, index) => {
                const card = document.createElement('div');
                card.className = 'sample-card';
                
                card.innerHTML = `
                    <div class="card-header">
                        <span>نمونه شماره ${index + 1} | شناسه: ${sample.id}</span>
                        <button class="context-toggle" onclick="toggleContext(${index})">مشاهده محتوای بازیابی شده (Context)</button>
                    </div>
                    
                    <div class="column" style="background:#fff;">
                         <div class="label">سوال پرسیده شده:</div>
                         <div class="question-box content">${sample.question}</div>
                    </div>

                    <div class="grid-container">
                        <div class="column human-col">
                            <h3><span class="tag tag-human">Human</span> پاسخ واقعی جامعه</h3>
                            <div class="section">
                                <div class="content">${sample.human_answer}</div>
                            </div>
                        </div>
                        
                        <div class="column ai-col">
                            <h3><span class="tag tag-ai">AI</span> پاسخ دانا</h3>
                            <div class="section">
                                <div class="label">پاسخ کوتاه:</div>
                                <div class="content"><strong>${sample.ai_short_answer}</strong></div>
                            </div>
                            <div class="section">
                                <div class="label">جزئیات بیشتر:</div>
                                <div class="content">${sample.ai_detailed_info || '---'}</div>
                            </div>
                        </div>
                    </div>

                    <div id="context-${index}" class="context-box">
                        <div class="label">محتوایی که برای هوش مصنوعی ارسال شد (Retrieved Context):</div>
                        <div class="content">${sample.retrieved_context}</div>
                    </div>
                `;
                container.appendChild(card);
            });
        }

        function toggleContext(index) {
            const el = document.getElementById(`context-${index}`);
            el.style.display = el.style.display === 'block' ? 'none' : 'block';
        }

        // Initialize
        renderDashboard(dataset);
    </script>
</body>
</html>
"""

async def generate_dataset(limit=10):
    print(f"Loading knowledge base from {DATA_PATH}...")
    if not os.path.exists(DATA_PATH):
        print(f"Error: {DATA_PATH} not found.")
        return

    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        kb = json.load(f)

    # Filter for conversation chains and sort by timestamp (most recent first)
    chains = [item for item in kb if item.get("type") == "conversation_chain"]
    chains.sort(key=lambda x: x.get("unix_time", 0), reverse=True)
    
    chains = chains[:limit]

    print(f"Processing {len(chains)} questions...")

    results = []
    for i, chain in enumerate(chains):
        messages = chain.get("messages", [])
        if not messages:
            continue
            
        question = messages[0].get("text", "")
        human_answer = messages[1].get("text", "No human answer found.") if len(messages) > 1 else "No reply found."
        
        print(f"[{i+1}/{len(chains)}] Generating answer for: {question[:50]}...")
        ai_response = await get_ai_answer(question)
        
        results.append({
            "id": chain.get("id"),
            "question": question,
            "human_answer": human_answer,
            "ai_short_answer": ai_response.get("short_answer"),
            "ai_detailed_info": ai_response.get("detailed_info"),
            "retrieved_context": ai_response.get("retrieved_context")
        })

    # Save JSON for backup
    print(f"Saving JSON results to {JSON_OUTPUT_PATH}...")
    os.makedirs("QA", exist_ok=True)
    with open(JSON_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Save Standalone HTML
    print(f"Saving Standalone HTML to {HTML_OUTPUT_PATH}...")
    html_content = HTML_TEMPLATE.replace("JSON_DATA_PLACEHOLDER", json.dumps(results, ensure_ascii=False))
    with open(HTML_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print("Generation complete! You can now double-click 'QA/dashboard_standalone.html' to view it.")

if __name__ == "__main__":
    asyncio.run(generate_dataset())
