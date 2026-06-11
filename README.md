# 🛡️ LoanGuard — AI Compliance Agent for Indian Fintech

> **An autonomous AI agent that intercepts loan advisor responses in real time, evaluates them against RBI Digital Lending Guidelines using Gemini, and rewrites or escalates non-compliant responses before a customer sees legally wrong information — fully traced and monitored through Arize Phoenix.**

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google_Cloud-Run-4285F4?style=flat&logo=googlecloud&logoColor=white)
![Vertex AI](https://img.shields.io/badge/Vertex_AI-Gemini_2.5-4285F4?style=flat&logo=googlecloud&logoColor=white)
![Arize Phoenix](https://img.shields.io/badge/Arize-Phoenix-7C3AED?style=flat&logo=data:image/png;base64,iVBORw0KGgo=&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat&logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)
![Hackathon](https://img.shields.io/badge/Google_Cloud-Rapid_Agent_Hackathon_2026-orange?style=flat&logo=googlecloud)

**Built for:** Google Cloud Rapid Agent Hackathon 2026 · **Track:** Arize  
**Live Demo:** https://loanguard-593852498859.us-central1.run.app  
**Video:** https://www.youtube.com/watch?v=nzK-0ezsjDk 
**GitHub:** https://github.com/Gangaparameshwari07/loanguard

---

## The Problem

Every day, AI loan advisors at Indian fintechs give customers:
- Wrong interest rates quoted as monthly instead of annual
- Loan approvals without mandatory Key Fact Statement (KFS)
- Eligibility confirmations without credit score verification
- EMI calculations without reducing balance disclosure

The RBI has already penalized Indian fintechs **hundreds of crores** for non-compliant AI systems. The problem is not that fintechs want to deceive — it is that their AI advisors hallucinate, and nobody catches it before the customer signs.

**LoanGuard catches it.**

---

## How It Works

```
Customer asks a loan question
          ↓
AI Loan Advisor generates a response
          ↓
LoanGuard intercepts — before customer sees it
          ↓
┌─────────────────────────────────────────────────┐
│  Step 1: classify_query                         │
│  Detects the financial claim type               │
│  (interest_rate / eligibility / repayment / kyc)│
│                                                 │
│  Step 2: fetch_rbi_rule                         │
│  Retrieves relevant RBI Digital Lending rule    │
│                                                 │
│  Step 3: evaluate_compliance                    │
│  Scores response 0–100 against 30 RBI rules     │
│                                                 │
│  Step 4: arize_eval (Gemini hallucination check)│
│  Programmatic factual accuracy verification     │
│                                                 │
│  Step 5: generate_safe_response                 │
│  Gemini rewrites — or escalates to human review │
└─────────────────────────────────────────────────┘
          ↓
Every step traced in Arize Phoenix in real time
          ↓
Customer receives safe, compliant response
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Google Cloud Platform                     │
│                                                             │
│  ┌─────────────┐    ┌──────────────────┐                   │
│  │  Cloud Run  │───▶│  Vertex AI       │                   │
│  │  FastAPI    │    │  Gemini 2.5      │                   │
│  │  Backend    │    │  Flash Lite      │                   │
│  └──────┬──────┘    └──────────────────┘                   │
│         │                                                   │
│  ┌──────▼──────┐    ┌──────────────────┐                   │
│  │  Agent      │    │  Agent Builder   │                   │
│  │  Pipeline   │    │  Data Store      │                   │
│  │  (5 steps)  │    │  RBI Guidelines  │                   │
│  └──────┬──────┘    └──────────────────┘                   │
│         │                                                   │
└─────────┼───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Arize Phoenix Cloud                       │
│                                                             │
│  ┌──────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │  Live Traces │  │  Hallucination │  │  Self-Improve  │  │
│  │  74+ spans   │  │  Evaluator     │  │  Loop + RAG    │  │
│  └──────────────┘  └────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Why Arize Phoenix

Most AI compliance tools monitor passively. LoanGuard uses Arize as the **brain of autonomous improvement** — not just a dashboard.

### 1. Real-time Decision Tracing
Every agent step — classify, fetch, evaluate, rewrite — appears as a span in Phoenix. Compliance officers see exactly WHY a response was flagged, not just that it was.

### 2. Programmatic Hallucination Evaluation
LoanGuard runs a Gemini-powered hallucination check on every non-compliant response using Phoenix's evaluation framework. The result (HALLUCINATED / CORRECT) directly drives the escalation decision.

### 3. Closed-Loop Self-Improvement
LoanGuard queries its own Phoenix traces to find violation patterns. When drift is detected — for example, 80% of recent responses failing interest rate checks — it automatically patches the RBI knowledge base with an enhanced guideline. The system gets smarter without human intervention.

### 4. Production Observability
74+ traces captured. Every compliance decision is inspectable, auditable, and improvable. This is not a toy demo — this is production-grade AI governance.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Gemini 2.5 Flash Lite — Vertex AI |
| Observability | Arize Phoenix Cloud |
| Tracing | OpenInference + OpenTelemetry |
| Hallucination Eval | Gemini-powered inline evaluator |
| Self-Improvement | Phoenix MCP trace queries + RAG |
| Knowledge Base | 30 RBI Digital Lending Guidelines |
| Agent Builder | Vertex AI Agent Builder + Data Store |
| Backend | FastAPI on Google Cloud Run |
| Frontend | Google Material Design 3 |

---

## Agent Capabilities

### Beyond Chat ✅
LoanGuard does not answer questions. It intercepts, evaluates, rewrites, escalates, and logs — all autonomously.

### Multi-Step Planning ✅
Five discrete reasoning steps, each traced independently in Arize Phoenix.

### Partner MCP Integration ✅
- Queries Phoenix traces via MCP to detect violation patterns
- Runs programmatic hallucination evaluations
- Feeds evaluation results back into escalation logic
- Self-improvement loop patches knowledge base based on trace data

---

## RBI Compliance Rules

LoanGuard enforces 30 rules across 5 categories from the **RBI Digital Lending Guidelines 2022 + Master Directions 2023** — the current legally binding framework for all Indian fintechs.

| Category | Rules | Example |
|----------|-------|---------|
| Interest Rate | 7 | APR must be stated annually, never monthly |
| Eligibility | 6 | Credit score check mandatory before approval |
| Disclosure | 8 | KFS required before any loan agreement |
| Repayment | 6 | EMI on reducing balance method only |
| KYC | 3 | Aadhaar usage requires explicit consent |

---

## Demo Scenarios

| Scenario | Input | LoanGuard Action |
|----------|-------|-----------------|
| Wrong Interest Rate | "Rate is 0.7% per month" | ESCALATED — APR violation, hallucinated |
| Missing KFS | "Loan approved, sign now" | ESCALATED — KFS not disclosed |
| EMI Violation | "EMI ₹9,500/month, apply now" | REWRITTEN — Gemini adds RBI disclosures |
| Compliant Response | Full APR + KFS + credit check | SAFE — 100/100 score |

---

## Project Structure

```
loanguard/
├── agent/
│   ├── agent.py              # 5-step compliance pipeline
│   ├── evaluator.py          # RBI rule evaluation logic
│   ├── evaluator_arize.py    # Gemini hallucination evaluator
│   ├── mcp_loop.py           # Phoenix MCP self-improvement
│   ├── rag_updater.py        # Knowledge base auto-patcher
│   ├── tracer.py             # Arize Phoenix tracing setup
│   └── rules.json            # 30 RBI guidelines dataset
├── api/
│   └── main.py               # FastAPI backend (5 endpoints)
├── frontend/
│   └── index.html            # Google M3 UI
├── Dockerfile
├── Procfile
└── requirements.txt
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/check` | POST | Run compliance check on advisor response |
| `/improve` | POST | Run self-improvement loop via Phoenix MCP |
| `/rules` | GET | List all 30 RBI guidelines |
| `/stats` | GET | Real-time compliance statistics |
| `/health` | GET | Health check + tracing status |

---

## Setup & Run

### Prerequisites
- Python 3.11+
- Google Cloud account with Vertex AI enabled
- Arize Phoenix Cloud account (free)

### Installation

```bash
git clone https://github.com/Gangaparameshwari07/loanguard.git
cd loanguard
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env_example .env
# Fill in your API keys in .env
```

### Environment Variables

```env
GOOGLE_CLOUD_PROJECT=your_gcp_project_id
GOOGLE_CLOUD_LOCATION=us-central1
PHOENIX_API_KEY=your_phoenix_api_key
PHOENIX_SPACE_NAME=your_space_name
```

### Run Locally

```bash
uvicorn api.main:app --reload --port 8080
```

Open `http://localhost:8080`

### Deploy to Cloud Run

```bash
gcloud run deploy loanguard \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080
```

---

## Google Cloud Infrastructure

| Service | Usage |
|---------|-------|
| Cloud Run | Production hosting |
| Vertex AI | Gemini 2.5 Flash Lite |
| Agent Builder | LoanGuard Compliance Agent app |
| Agent Builder Data Store | RBI guidelines indexed |
| Cloud Build | Container build pipeline |
| Artifact Registry | Container storage |

---

## Real-World Impact

Indian fintech AI compliance is not a hypothetical problem:

- RBI's FREE-AI framework mandates real-time governance for AI financial advisors
- Digital lending volumes exceeded **180 billion transactions** in FY25
- Multiple fintechs have received RBI notices for AI-generated non-compliant advice
- The penalty for non-compliance can reach **₹1 crore per violation**

LoanGuard makes compliance automatic, auditable, and self-improving.

---

## License

MIT License — see [LICENSE](LICENSE)

---

*Built for Google Cloud Rapid Agent Hackathon 2026 · Arize Track*