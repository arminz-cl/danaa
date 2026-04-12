import os
import json
import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROCESSED_DIR = "data/processed"
KNOWLEDGE_BASE_DIR = "data/knowledge_base"

@app.get("/api/cards")
async def get_cards():
    """Reads both knowledge cards and raw processed chats, grouped by source."""
    grouped_data = {}
    total_kb_cards = 0
    
    # 1. Load Distilled Knowledge Cards (Recursively)
    if os.path.exists(KNOWLEDGE_BASE_DIR):
        for root, dirs, files in os.walk(KNOWLEDGE_BASE_DIR):
            for filename in files:
                if filename.endswith(".json") and "_cards" in filename:
                    # e.g. "pgwp_cards.json" -> "pgwp"
                    prefix = filename.split('_')[0]
                    name = "★ " + prefix.title()
                    path = os.path.join(root, filename)
                    
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            # Handle both list and dict with "cards" key
                            cards = []
                            if isinstance(data, dict):
                                cards = data.get("cards", [])
                            elif isinstance(data, list):
                                cards = data
                                
                            if cards:
                                total_kb_cards += len(cards)
                                if name not in grouped_data:
                                    grouped_data[name] = []
                                grouped_data[name].extend(cards)
                                logger.info(f"Loaded {len(cards)} cards from {path} into {name}")
                    except Exception as e:
                        logger.error(f"Error reading {path}: {e}")

    # 2. Load Raw Processed History (Most recent 100)
    if os.path.exists(PROCESSED_DIR):
        for filename in os.listdir(PROCESSED_DIR):
            if filename.endswith(".json") and "_cleaned" in filename:
                name = "💬 " + filename.replace("_cleaned", "").replace(".json", "").replace("_", " ").title()
                path = os.path.join(PROCESSED_DIR, filename)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Convert raw items to "card" format for UI
                        snippets = []
                        # Take last 100 items
                        for item in reversed(data[-100:]):
                            if item.get("type") == "conversation_chain":
                                fact = " | ".join([f"{m['user_hash']}: {m['text']}" for m in item.get("messages", [])])
                            else:
                                fact = item.get("content", "")
                            
                            snippets.append({
                                "topic": item.get("type", "Info").upper(),
                                "fact": fact,
                                "type": "experience",
                                "confidence": 5,
                                "source_file": filename
                            })
                        grouped_data[name] = snippets
                except: pass
                
    logger.info(f"Dashboard serving {total_kb_cards} cards total across {len(grouped_data)} groups.")
    return {
        "metadata": {"total_cards": total_kb_cards},
        "data": grouped_data
    }

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Serves the main dashboard HTML page with tab support."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dana Knowledge Dashboard</title>
        <style>
            :root {
                --rule-color: #3b82f6;
                --advice-color: #10b981;
                --experience-color: #f59e0b;
                --question-color: #8b5cf6;
                --bg-color: #f1f5f9;
                --card-bg: #ffffff;
                --text-main: #1e293b;
                --text-muted: #64748b;
                --primary: #2563eb;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: var(--bg-color);
                color: var(--text-main);
                margin: 0;
                padding: 20px;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 30px;
                background: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
            }
            .title h1 { margin: 0; font-size: 24px; color: #0f172a; display: flex; align-items: center; gap: 10px; }
            .title p { margin: 5px 0 0; color: var(--text-muted); font-size: 14px; }
            
            .card-counter {
                background: var(--primary);
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 800;
            }

            .tabs {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 10px;
                overflow-x: auto;
                padding-bottom: 10px;
            }
            .tab-btn {
                padding: 10px 20px;
                border: none;
                background: none;
                font-weight: 600;
                color: var(--text-muted);
                cursor: pointer;
                border-radius: 8px;
                transition: all 0.2s;
                white-space: nowrap;
            }
            .tab-btn:hover { background: #e2e8f0; }
            .tab-btn.active {
                background: var(--primary);
                color: white;
            }

            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                gap: 20px;
            }
            .card {
                background: var(--card-bg);
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
                border-left: 5px solid #cbd5e1;
                display: flex;
                flex-direction: column;
                animation: fadeIn 0.3s ease-in-out;
            }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
            
            .card.rule { border-left-color: var(--rule-color); }
            .card.advice { border-left-color: var(--advice-color); }
            .card.experience { border-left-color: var(--experience-color); }
            .card.question { border-left-color: var(--question-color); }

            .card-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 15px;
            }
            .topic { font-weight: 700; font-size: 13px; text-transform: uppercase; color: var(--text-muted); }
            .type-badge {
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 700;
                color: white;
                text-transform: uppercase;
            }
            .rule .type-badge { background-color: var(--rule-color); }
            .advice .type-badge { background-color: var(--advice-color); }
            .experience .type-badge { background-color: var(--experience-color); }
            .question .type-badge { background-color: var(--question-color); }

            .fact {
                font-size: 17px;
                line-height: 1.6;
                direction: rtl;
                text-align: right;
                flex-grow: 1;
                margin-bottom: 15px;
                color: #334155;
            }

            .card-footer {
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 11px;
                color: var(--text-muted);
                border-top: 1px solid #f1f5f9;
                padding-top: 10px;
            }
            .confidence-bar { width: 50px; height: 5px; background: #e2e8f0; border-radius: 3px; margin-left: 5px; display: inline-block; overflow: hidden; }
            .confidence-fill { height: 100%; background: #fbbf24; }

            #status { font-size: 12px; color: var(--advice-color); font-weight: 600; }
            .empty-state { text-align: center; padding: 100px 0; color: var(--text-muted); grid-column: 1 / -1; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="title">
                    <h1>Dana Knowledge Dashboard <span id="card-count" class="card-counter">0</span></h1>
                    <p>Distilled Facts from Iranian Canadian Community</p>
                </div>
                <div id="status">LIVE</div>
            </div>

            <div id="tabs" class="tabs">
                <!-- Tab buttons will be injected here -->
            </div>

            <div id="grid" class="grid">
                <!-- Cards will be injected here -->
            </div>
        </div>

        <script>
            let allData = {};
            let activeTab = "";

            async function fetchData() {
                try {
                    const response = await fetch('/api/cards');
                    const json = await response.json();
                    const newData = json.data;
                    const metadata = json.metadata;

                    document.getElementById('card-count').innerText = metadata.total_cards;
                    
                    if (JSON.stringify(newData) === JSON.stringify(allData)) return;
                    allData = newData;

                    const tabContainer = document.getElementById('tabs');
                    const keys = Object.keys(allData);
                    
                    if (keys.length === 0) {
                        renderEmpty();
                        return;
                    }

                    // Preserve active tab or set to first one
                    if (!activeTab || !allData[activeTab]) {
                        activeTab = keys[0];
                    }

                    renderTabs(keys);
                    renderGrid();
                } catch (error) {
                    console.error('Error:', error);
                    document.getElementById('status').innerText = 'OFFLINE';
                    document.getElementById('status').style.color = '#ef4444';
                }
            }

            function renderTabs(keys) {
                const tabContainer = document.getElementById('tabs');
                tabContainer.innerHTML = '';
                keys.forEach(key => {
                    const btn = document.createElement('button');
                    btn.className = `tab-btn ${key === activeTab ? 'active' : ''}`;
                    btn.innerText = key;
                    btn.onclick = () => {
                        activeTab = key;
                        Array.from(tabContainer.children).forEach(b => b.classList.remove('active'));
                        btn.classList.add('active');
                        renderGrid();
                    };
                    tabContainer.appendChild(btn);
                });
            }

            function renderGrid() {
                const grid = document.getElementById('grid');
                grid.innerHTML = '';
                const cards = allData[activeTab] || [];

                if (cards.length === 0) {
                    grid.innerHTML = '<div class="empty-state">No cards extracted for this source yet.</div>';
                    return;
                }

                cards.forEach(card => {
                    const cardEl = document.createElement('div');
                    cardEl.className = `card ${card.type.toLowerCase()}`;
                    const confidencePct = (card.confidence / 10) * 100;
                    
                    cardEl.innerHTML = `
                        <div class="card-header">
                            <span class="topic">${card.topic}</span>
                            <span class="type-badge">${card.type}</span>
                        </div>
                        <div class="fact">${card.fact}</div>
                        <div class="card-footer">
                            <div>
                                <span>Confidence: ${card.confidence}/10</span>
                                <div class="confidence-bar"><div class="confidence-fill" style="width: ${confidencePct}%"></div></div>
                            </div>
                            <span>Source: ${card.source_file || 'N/A'}</span>
                        </div>
                    `;
                    grid.appendChild(cardEl);
                });
            }

            function renderEmpty() {
                document.getElementById('tabs').innerHTML = '';
                document.getElementById('grid').innerHTML = '<div class="empty-state">Waiting for extraction to begin...</div>';
            }

            fetchData();
            setInterval(fetchData, 3000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
