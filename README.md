🥝 Omnitest Agent: KiwiBaby Architecture
A production-grade, fault-tolerant AI QA Agent that transforms business requirements into structured, semantically validated test cases.

Unlike standard wrapper applications, Omnitest utilizes a Hybrid Multi-Tier Routing Engine that intelligently dispatches workloads between a zero-cost local CPU mock and dedicated AMD hardware endpoints via Fireworks AI, ensuring maximum token efficiency and zero-downtime resiliency.

🏆 What Makes This Architecture Bulletproof?
This is not a simple prompt-to-response generator. It is a controlled, defensive AI pipeline engineered for enterprise QA:

🏎️ Hybrid Telemetry Router: Dynamically routes complex logic to DeepSeek V4 Pro on AMD GPUs while routing simple structural requests to local edge compute to save cloud costs.

🗜️ Prompt Compression Pipeline (Tier 2): Actively compresses requirement payloads before transmission, significantly reducing API token footprint and latency.

🧠 Semantic Coverage Engine: Uses local SentenceTransformer vector embeddings (all-MiniLM-L6-v2) to mathematically guarantee 100% requirement coverage and score the LLM's output against dynamic business rules.

🛡️ Defensive Type-Safety Guardrails: Implements a strict normalization gateway to catch and self-heal JSON type mutations and formatting hallucinations before they crash the system.

📊 Real-Time Cost Tracking: Logs execution latency, token usage, and estimated cost savings directly into a serverless Neon Postgres database.

🏗 System Architecture Flow
Plaintext
User Requirement 
       │
       ▼
[ Gateway API ] ───────► (Requires Compression?) ────► [ Payload Compressor ]
       │                                                      │
       ▼                                                      ▼
[ Routing Telemetry ] ◄───────────────────────────────────────┘
       │
       ├──► Tier 1: Local CPU Edge Execution (Zero Cost / Sub 5ms)
       │
       └──► Tier 3: Remote AMD Hardware (Fireworks AI / DeepSeek-V4-Pro)
                   │
                   ▼ (Fallback / Retry Logic)
[ Defensive Normalization Gateway ] ◄── (Catches JSON Mutations)
       │
       ▼
[ Semantic Validation Matrix ] ◄── (Vector Embeddings vs Business Rules)
       │
       ▼
[ Storage & Neon DB Telemetry ]
       │
       ▼
Final Output (Gherkin / JSON / Excel) + QA Coverage Score
🧠 Core Features
🔹 Advanced Semantic Coverage Tracking
Generates comprehensive test suites spanning Positive, Negative, Edge, System, and API Validations.

Evaluates the LLM output locally using cosine similarity to ensure no edge cases were dropped.

Automatically flags suites as AUTO_APPROVED, NEEDS_REVIEW, or REGENERATE based on an aggregated Confidence Matrix (QA Score + Rule Score + Coverage Percent).

🔹 Resilience & Failover Control
Exponential back-off and retry limits built-in using Tenacity.

Zero-crash guarantee: If the cloud API goes down, the system seamlessly cascades to the local fallback generator.

🔹 Multi-Interface Support
🌐 Web UI: React/Vite dashboard with live token telemetry.

🧰 CLI Tool: Node.js integration for pipeline runners.

🧩 VS Code Extension: Generate test cases directly inline.

📦 Project Structure
Plaintext
ai-testcase-agent/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── router.py         # Advanced routing logic
│   │   ├── llm_client.py     # Fireworks API & AMD integration
│   │   ├── coverage.py       # SentenceTransformer validation engine
│   │   └── utils.py          # Defensive JSON parsing
│   ├── requirements.txt
│   └── reset_db.py
├── frontend/                 # React + Vite Dashboard
├── cli/                      # Node.js Command Line Tool
└── vscode-extension/         # IDE Plugin
🖥 Backend Setup & Configuration
📌 Requirements
Python 3.10+

Fireworks AI API Key (Free tier supported)

1️⃣ Install Dependencies
Bash
cd backend
pip install -r requirements.txt
2️⃣ Environment Configuration
Create a .env file inside the backend/ directory. Ensure you use the modern instantiated Fireworks client configuration:

Code snippet
# LLM Routing Configuration
FIREWORKS_API_KEY=your_actual_fireworks_api_key_here
FIREWORKS_MODEL=accounts/fireworks/models/deepseek-v4-pro
MAX_TOKENS=4096

# Database & Telemetry
DATABASE_URL=postgresql://neondb_owner:YOUR_PASSWORD@ep-curly-block.aws.neon.tech/neondb?sslmode=require

# App Settings
HOST=127.0.0.1
PORT=8000
FRONTEND_URL=http://localhost:5173
3️⃣ Run the Core Engine
Bash
uvicorn app.main:app --reload --port 8000
🌐 Frontend Dashboard Setup
Bash
cd frontend
npm install
npm run dev
Ensure your frontend/.env points to your active Uvicorn port (e.g., VITE_API_URL=http://127.0.0.1:8000).

📡 API Usage Example
POST /generate

JSON
{
  "requirement": "The Login button must turn exactly #00FF00 green when hovered, unless the button is disabled due to invalid form data.",
  "output_format": "json"
}
Response Payload Includes:

coverage_percent: 100.0

execution_latency_ms: 1245

routing_destination: "REMOTE_AMD"

test_cases: [...]

📄 License
MIT License