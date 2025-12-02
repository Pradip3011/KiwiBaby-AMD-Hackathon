# 🧪 AI Testcase Agent

AI-powered test case generator with a **FastAPI backend**, **React frontend**, **Node.js CLI**, and a **VS Code extension**.  
Automatically generate high-quality test cases using LLMs like OpenAI, Anthropic, Gemini, or any model supported by your backend.

---

## 🚀 Features

### 🧠 AI-Driven Testcase Generation
- Generate test cases for functions, methods, API endpoints, or full modules  
- Supports multiple LLM providers (configurable via `.env`)

### 🛠 Multi-Interface Access
- **Backend API** (FastAPI)  
- **Web UI** (React + Vite)  
- **Command Line Interface** (Node.js)  
- **VS Code Extension**

### 🐳 Full Docker Support
- One-command startup with `docker-compose`

---

## 📦 Project Structure


ai-testcase-agent/
├── backend/                     # FastAPI backend service
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # Entry point for FastAPI app
│   │   ├── schemas.py           # Pydantic models
│   │   ├── llm_client.py        # LLM integration logic
│   │   ├── utils.py             # Helper functions
│   │   └── config.py            # Configuration & environment handling
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile               # Backend container setup
│   └── docker-compose.yml       # Multi-service orchestration
│
├── frontend/                    # React (Vite) frontend
│   ├── package.json             # Frontend dependencies
│   ├── index.html               # Root HTML file
│   ├── src/
│   │   ├── main.jsx             # React entry point
│   │   ├── App.jsx              # Main App component
│   │   ├── api.js               # API calls to backend
│   │   └── styles.css           # Global styles
│   └── vite.config.js           # Vite configuration
│
├── cli/                         # Node.js CLI tool
│   ├── package.json             # CLI dependencies
│   └── bin/
│       └── tcgen.js             # CLI entry script
│
├── vscode-extension/            # VS Code extension
│   ├── package.json             # Extension manifest
│   └── src/
│       └── extension.ts         # Extension activation logic
│
└── README.md                    # Project documentation
---

## 🖥 Backend (FastAPI)

### 📌 Requirements
- Python 3.10+  
- Install dependencies:
  ```bash
  pip install -r backend/requirements.txt

🔧 Configuration

Create a .env file in backend/:

LLM_PROVIDER=gemini
LLM_API_KEY=your_gemini_api_key
LLM_MODEL=gemini-pro
MAX_TOKENS=4096

▶️ Run Backend

cd backend
uvicorn app.main:app --reload --port 8000

📘 API Endpoint

POST /generateGenerate test cases from a requirement or code snippet.

Request:

{
  "requirement": "Login page should validate email and password",
  "output_format": "json"
}

Response:

{
  "output": {
    "testcases": [
      { "input": ["user@example.com", "123456"], "expected": "success" },
      { "input": ["", ""], "expected": "error" }
    ]
  }
}

📚 Auto-generated OpenAPI docs:👉 http://localhost:8000/docs

🌐 Frontend (React + Vite)

📦 Install

cd frontend
npm install

▶️ Run

npm run dev

Create a .env file in frontend/:

VITE_API_URL=http://localhost:8000

Access the UI:👉 http://localhost:5173

🧰 CLI (Node.js)

📦 Install Globally

cd cli
npm install
npm link

▶️ Usage

tcgen generate ./src/add.js
tcgen generate ./src/add.py --lang python
tcgen generate ./foo.js --server http://localhost:8000

🧩 VS Code Extension

🛠 Command

AI Testcase Agent: Generate Test Cases

▶️ Usage

Select code in your editor

Press Ctrl+Shift+P

Run the command

Test cases appear in a side panel or are inserted directly into the file

⚙️ Configuration

Set backend URL in VS Code settings:

"aiTestcaseAgent.serverUrl": "http://localhost:8000"

🐳 Docker Setup

▶️ Build & Run

cd backend
docker-compose up --build

This starts:

FastAPI backend → http://localhost:8000

React frontend → http://localhost:5173

🔌 End-to-End Workflow

1️⃣ Developer writes code2️⃣ Requests test cases via:

Web UI

CLI tool

VS Code extension

Direct API call

3️⃣ Backend sends prompt to LLM4️⃣ Response is parsed into executable test cases5️⃣ Results are displayed in UI/CLI/editor

🧪 Testing

Backend

pytest

Frontend

npm test

CLI

npm test

📄 License

MIT License — free for personal and commercial use.

To run backend:
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

To run frontend
npm install
npm run dev
