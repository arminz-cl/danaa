import os
import json
import logging
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI()

# Setup logging
log_dir = "logs/dashboard"
os.makedirs(log_dir, exist_ok=True)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Standard log handler
info_handler = RotatingFileHandler(f"{log_dir}/dashboard.log", maxBytes=10*1024*1024, backupCount=5)
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(formatter)

# Error log handler
error_handler = RotatingFileHandler(f"{log_dir}/dashboard.errors", maxBytes=10*1024*1024, backupCount=5)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(info_handler)
logger.addHandler(error_handler)
logger.addHandler(logging.StreamHandler())

PROCESSED_DIR = "data/processed"
KNOWLEDGE_BASE_DIR = "data/knowledge_base"
EXPERIMENTS_DIR = "experiments"
LOGS_BASE_DIR = "logs"

@app.get("/api/logs")
async def list_logs():
    """Returns a tree of available log files."""
    log_tree = {}
    if not os.path.exists(LOGS_BASE_DIR):
        return log_tree
        
    for service in os.listdir(LOGS_BASE_DIR):
        service_path = os.path.join(LOGS_BASE_DIR, service)
        if os.path.isdir(service_path):
            log_tree[service] = sorted([f for f in os.listdir(service_path) if f.endswith(('.log', '.errors'))])
    return log_tree

@app.get("/api/logs/{service}/{filename}")
async def get_log_content(service: str, filename: str):
    """Returns the last 500 lines of a specific log file."""
    safe_service = "".join(x for x in service if x.isalnum() or x == "_")
    safe_filename = "".join(x for x in filename if x.isalnum() or x in "._")
    
    path = os.path.join(LOGS_BASE_DIR, safe_service, safe_filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Log file not found")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return {"content": "".join(lines[-500:])}
    except Exception as e:
        return {"content": f"Error reading log: {str(e)}"}

@app.get("/api/cards")
async def get_cards():
    """Reads knowledge cards, raw chats, and RAG experiments, grouped by source."""
    grouped_data = {}
    total_kb_cards = 0
    
    # 1. Load Distilled Knowledge Cards (Recursively)
    if os.path.exists(KNOWLEDGE_BASE_DIR):
        for root, dirs, files in os.walk(KNOWLEDGE_BASE_DIR):
            for filename in files:
                if filename.endswith(".json") and "_cards" in filename:
                    prefix = filename.split('_')[0]
                    name = "★ " + prefix.title()
                    path = os.path.join(root, filename)
                    
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            cards = data.get("cards", []) if isinstance(data, dict) else data
                            if cards:
                                total_kb_cards += len(cards)
                                if name not in grouped_data:
                                    grouped_data[name] = []
                                grouped_data[name].extend(cards)
                    except: pass

    # 2. Load Raw Process History
    if os.path.exists(PROCESSED_DIR):
        for filename in os.listdir(PROCESSED_DIR):
            if filename.endswith(".json") and "_cleaned" in filename:
                name = "💬 " + filename.replace("_cleaned", "").replace(".json", "").replace("_", " ").title()
                path = os.path.join(PROCESSED_DIR, filename)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        snippets = []
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

    # 3. Load RAG Questions (Experiments)
    if os.path.exists(EXPERIMENTS_DIR):
        name = "🔍 QUESTIONS"
        questions = []
        files = sorted([f for f in os.listdir(EXPERIMENTS_DIR) if f.startswith("sample_")], reverse=True)[:50]
        for filename in files:
            path = os.path.join(EXPERIMENTS_DIR, filename)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Parsing with broad splitters to capture context
                    parts = content.split("USER QUESTION:", 1)
                    if len(parts) > 1:
                        q_and_rest = parts[1].split("RETRIEVED CONTEXT:", 1)
                        question = q_and_rest[0].strip()
                        
                        ctx_and_ans = q_and_rest[1].split("AI SHORT ANSWER:", 1)
                        context = ctx_and_ans[0].strip()
                        
                        ans_and_detail = ctx_and_ans[1].split("AI DETAILED INFO:", 1)
                        ai_ans = ans_and_detail[0].strip()
                        detailed_info = ans_and_detail[1].strip() if len(ans_and_detail) > 1 else ""
                        
                        questions.append({
                            "topic": "RAG Interaction",
                            "fact": f"❓ {question}\n\n🤖 {ai_ans}",
                            "type": "question",
                            "confidence": 10,
                            "source_file": filename,
                            "rag_context": context,
                            "detailed_info": detailed_info
                        })
            except: pass
        if questions:
            grouped_data[name] = questions
                
    return {
        "metadata": {"total_cards": total_kb_cards},
        "data": grouped_data
    }

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Serves the main dashboard HTML page."""
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
            .container { max-width: 1400px; margin: 0 auto; }
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
            .card-counter { background: var(--primary); color: white; padding: 4px 12px; border-radius: 20px; font-size: 14px; font-weight: 800; }
            
            .tabs {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 10px;
                overflow-x: auto;
            }
            .tab-btn {
                padding: 10px 20px;
                border: none;
                background: none;
                font-weight: 600;
                color: var(--text-muted);
                cursor: pointer;
                border-radius: 8px;
                white-space: nowrap;
            }
            .tab-btn.active { background: var(--primary); color: white; }

            .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; }
            
            .log-view {
                display: none;
                flex-direction: row;
                gap: 20px;
                height: 75vh;
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            }
            .log-sidebar { width: 280px; border-right: 1px solid #e2e8f0; overflow-y: auto; padding-right: 15px; }
            .log-content {
                flex-grow: 1;
                background: #0f172a;
                color: #e2e8f0;
                padding: 20px;
                border-radius: 8px;
                font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
                overflow-y: auto;
                white-space: pre-wrap;
            }
            .log-service-header { font-weight: 800; font-size: 11px; text-transform: uppercase; color: var(--text-muted); margin: 15px 0 5px; letter-spacing: 1px; }
            .log-file-link {
                display: block;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 13px;
                color: #334155;
                cursor: pointer;
                margin-bottom: 2px;
            }
            .log-file-link:hover { background: #f1f5f9; }
            .log-file-link.active { background: var(--primary); color: white; }
            .log-file-link.error-file { color: #ef4444; border-left: 3px solid #ef4444; }
            .log-file-link.active.error-file { color: white; }

            .card {
                background: var(--card-bg);
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
                border-left: 5px solid #cbd5e1;
                display: flex;
                flex-direction: column;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1); }
            .card.rule { border-left-color: var(--rule-color); }
            .card.advice { border-left-color: var(--advice-color); }
            .card.experience { border-left-color: var(--experience-color); }
            .card.question { border-left-color: var(--question-color); }
            
            .fact { font-size: 15px; line-height: 1.6; direction: rtl; text-align: right; margin: 15px 0; color: #334155; white-space: pre-wrap; }
            .type-badge { padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; color: white; text-transform: uppercase; }
            .rule .type-badge { background-color: var(--rule-color); }
            .advice .type-badge { background-color: var(--advice-color); }
            .experience .type-badge { background-color: var(--experience-color); }
            .question .type-badge { background-color: var(--question-color); }

            .card-details { display: none; margin-top: 15px; padding-top: 15px; border-top: 1px solid #e2e8f0; font-size: 13px; color: #475569; }
            .card-details.active { display: block; }
            .detail-section { margin-bottom: 15px; }
            .detail-label { font-weight: 800; text-transform: uppercase; font-size: 11px; color: var(--text-muted); margin-bottom: 5px; display: block; }
            .detail-content { white-space: pre-wrap; direction: rtl; text-align: right; background: #f8fafc; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="title">
                    <h1>Dana Dashboard <span id="card-count" class="card-counter">0</span></h1>
                </div>
                <div id="status" style="color: #10b981; font-weight: 700;">LIVE</div>
            </div>

            <div id="tabs" class="tabs"></div>

            <div id="grid" class="grid"></div>

            <div id="log-view" class="log-view">
                <div id="log-sidebar" class="log-sidebar"></div>
                <div id="log-content" class="log-content">Select a log file...</div>
            </div>
        </div>

        <script>
            let allData = {};
            let activeTab = "";

            async function fetchData() {
                try {
                    const response = await fetch('/api/cards');
                    const json = await response.json();
                    document.getElementById('card-count').innerText = json.metadata.total_cards;
                    
                    if (JSON.stringify(json.data) === JSON.stringify(allData)) return;
                    allData = json.data;

                    const keys = Object.keys(allData);
                    keys.push("📁 LOGS");
                    
                    if (!activeTab || (!allData[activeTab] && activeTab !== "📁 LOGS")) activeTab = keys[0];

                    renderTabs(keys);
                    renderContent();
                } catch (e) { document.getElementById('status').innerText = 'OFFLINE'; }
            }

            function renderTabs(keys) {
                const container = document.getElementById('tabs');
                container.innerHTML = '';
                keys.forEach(k => {
                    const btn = document.createElement('button');
                    btn.className = `tab-btn ${k === activeTab ? 'active' : ''}`;
                    btn.innerText = k;
                    btn.onclick = () => { activeTab = k; renderTabs(keys); renderContent(); };
                    container.appendChild(btn);
                });
            }

            function renderContent() {
                const grid = document.getElementById('grid');
                const logView = document.getElementById('log-view');
                if (activeTab === "📁 LOGS") {
                    grid.style.display = 'none';
                    logView.style.display = 'flex';
                    fetchLogsList();
                } else {
                    grid.style.display = 'grid';
                    logView.style.display = 'none';
                    renderGrid();
                }
            }

            async function fetchLogsList() {
                const res = await fetch('/api/logs');
                const logData = await res.json();
                const sidebar = document.getElementById('log-sidebar');
                sidebar.innerHTML = '';
                Object.keys(logData).forEach(service => {
                    const h = document.createElement('div');
                    h.className = 'log-service-header';
                    h.innerText = service.replace('_', ' ');
                    sidebar.appendChild(h);
                    logData[service].forEach(f => {
                        const link = document.createElement('a');
                        link.className = `log-file-link ${f.endsWith('.errors') ? 'error-file' : ''}`;
                        link.innerText = f;
                        link.onclick = () => loadLogContent(service, f, link);
                        sidebar.appendChild(link);
                    });
                });
            }

            async function loadLogContent(s, f, el) {
                document.querySelectorAll('.log-file-link').forEach(l => l.classList.remove('active'));
                el.classList.add('active');
                const content = document.getElementById('log-content');
                content.innerText = "Loading...";
                const res = await fetch(`/api/logs/${s}/${f}`);
                const data = await res.json();
                content.innerText = data.content || "Empty.";
                content.scrollTop = content.scrollHeight;
            }

            function renderGrid() {
                const grid = document.getElementById('grid');
                grid.innerHTML = '';
                (allData[activeTab] || []).forEach(c => {
                    const el = document.createElement('div');
                    el.className = `card ${c.type.toLowerCase()}`;
                    
                    let detailsHtml = '';
                    if (c.rag_context || c.detailed_info) {
                        detailsHtml = `
                            <div class="card-details">
                                ${c.detailed_info ? `
                                <div class="detail-section">
                                    <span class="detail-label">Detailed AI Response</span>
                                    <div class="detail-content">${c.detailed_info}</div>
                                </div>` : ''}
                                ${c.rag_context ? `
                                <div class="detail-section">
                                    <span class="detail-label">RAG Context (Retrieved Knowledge)</span>
                                    <div class="detail-content">${c.rag_context}</div>
                                </div>` : ''}
                            </div>
                        `;
                    }

                    el.innerHTML = `
                        <div style="display:flex;justify-content:space-between">
                            <span style="font-weight:700;font-size:12px;color:#64748b">${c.topic}</span>
                            <span class="type-badge">${c.type}</span>
                        </div>
                        <div class="fact">${c.fact}</div>
                        <div style="font-size:10px;color:#94a3b8">Source: ${c.source_file}</div>
                        ${detailsHtml}
                    `;
                    
                    el.onclick = () => {
                        const details = el.querySelector('.card-details');
                        if (details) details.classList.toggle('active');
                    };
                    
                    grid.appendChild(el);
                });
            }

            fetchData();
            setInterval(fetchData, 5000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
