# 🧪 AI QA Agent (Testcase Generation System)

A **production-grade AI QA Agent** that transforms business requirements into **structured, validated test cases** using a **multi-layer LLM pipeline**.

---

## 🚀 Tech Stack

- ⚡ FastAPI (Backend)
- ⚛️ React (Frontend)
- 🧰 Node.js CLI
- 🧩 VS Code Extension
- 🧠 Multi-LLM Support (OpenAI, Gemini, etc.)

---

## 🚀 What Makes This Different?

This is NOT just a prompt-based generator.

👉 It is a **controlled AI pipeline** with:

- 🧠 LLM Generation
- 🔍 Review Layer (QA reasoning)
- 🎯 Control Layer (output discipline)
- 🧱 Structure Validation
- 📊 Coverage Engine (semantic QA validation)
- 🧠 Memory Layer (context reuse)

---

## 🏗 Architecture Overview

User Input
↓
API Layer (FastAPI)
↓
Agent Pipeline
↓
Pre-processing (Enrichment + Memory)
↓
LLM Generation (Prompt Engine)
↓
Review Layer (QA Brain)
↓
Control Layer (Discipline)
↓
Structure Validation
↓
Coverage Engine (Quality Check)
↓
Final Output + Storage

---

## 🧠 Core Features

### 🔹 AI-Driven Test Generation

- Generate **Gherkin, JSON, Excel test cases**
- Covers:
  - Positive / Negative / Edge cases
  - System scenarios (rate limiting, session, concurrency)
  - API + UI validation

---

### 🔹 Multi-Layer QA Intelligence

#### 🧠 Review Layer

- Detect missing scenarios
- Fix structure
- Fill incomplete sections

#### 🎯 Control Layer

- Limit over-generation
- Remove noise
- Enforce maintainability

#### 🧱 Validation Layer

- Fix numbering
- Enforce Scenario / Scenario Outline rules
- Ensure structural consistency

---

### 📊 Coverage Engine (Advanced)

- Semantic similarity using embeddings
- Scenario coverage detection
- QA gap identification
- Quality scoring

---

### 🧠 Memory System

- Stores past requirements
- Retrieves similar cases
- Improves future outputs

---

### 🛠 Multi-Interface Support

- 🌐 Web UI (React)
- 🧰 CLI Tool
- 🧩 VS Code Extension
- 🔌 Direct API

---

## 📦 Project Structure

ai-testcase-agent/
├── backend/
│ ├── app/
│ │ ├── main.py
│ │ ├── routes/
│ │ ├── services/
│ │ ├── llm_client.py # Core AI pipeline
│ │ ├── coverage.py # Semantic QA coverage engine
│ │ ├── memory.py # Retrieval system
│ │ ├── schemas.py
│ │ ├── utils.py
│ │ └── config.py
│ ├── requirements.txt
│ └── Dockerfile
│
├── frontend/
├── cli/
├── vscode-extension/
└── README.md

---

## 🖥 Backend Setup

### 📌 Requirements

- Python 3.10+

```bash
pip install -r backend/requirements.txt
🔧 Configuration

Create .env inside backend/:

LLM_PROVIDER=openai
LLM_API_KEY=your_api_key
LLM_MODEL=gpt-4o-mini
MAX_TOKENS=4096
▶️ Run Backend
cd backend
uvicorn app.main:app --reload --port 8000
📡 API Usage
POST /generate
{
  "requirement": "Login system should validate email and password",
  "output_format": "gherkin"
}
🌐 Frontend Setup
cd frontend
npm install
npm run dev

.env:

VITE_API_URL=http://localhost:8000
🧰 CLI Usage
tcgen generate ./file.js
tcgen generate ./file.py --lang python
🧩 VS Code Extension

Command:

AI Testcase Agent: Generate Test Cases
🐳 Docker
cd backend
docker-compose up --build
🔄 End-to-End Flow
User provides requirement
API triggers agent pipeline
Requirement enrichment + memory injection
LLM generates output
Review + Control + Validation applied
Coverage evaluated
Output stored and returned
🧠 Design Pattern
Generator → Reviewer → Controller → Validator → Evaluator
🎯 Key Strengths
Structured, deterministic outputs
QA-aware reasoning
Controlled AI behavior
Production-ready architecture
📄 License

MIT License
```
