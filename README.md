# AILF (AI Language Frontend)

**An LLM-powered platform that generates business UIs from natural language.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev/)
[![Qwen3](https://img.shields.io/badge/Model-Qwen3-ff6b6b.svg)](https://github.com/QwenLM/Qwen3)

[English](README.md) · [中文](README_zh.md)

---

## What is AILF?

AILF is an intelligent dynamic UI generation platform powered by large language models. Users express their needs through natural language (voice or text), and the system automatically understands intent, fills slots, and generates the corresponding business interface in real time.

**Core philosophy**: Transform the traditional software paradigm from *"find a feature, then operate"* to *"describe your needs, then execute"*.

**Train ticket is just one example.** AILF is a **general-purpose platform** that works across any business domain. It comes with built-in scenarios like e-commerce, healthcare, hospitality, banking, logistics, education and more — and you can define your own custom scenarios without writing code.

For example, say:
> *"I want to buy a high-speed train ticket from Beijing to Shanghai tomorrow morning"*

The system automatically does: intent recognition → slot filling → form generation → available trains display → user confirmation → ticket purchase submission.

```
+--------------------------------------------------------------------------------+
|  Traditional Flow:  Find Menu -> Click -> Click -> Click -> Submit             |
|                      (5-8 steps, 45-120 seconds)                              |
|                                                                                |
|  AILF Flow:       "I want to..." -> AI generates UI -> Done                   |
|                      (1 step, 2-5 seconds)                                    |
+--------------------------------------------------------------------------------+
```

---

## Architecture

![AILF System Architecture Overview](screenshots/screenshot-architecture.png)

| Diagram | Description |
|---------|-------------|
| **Dataset Flow** | Training data pipeline - scenario definition, data generation, annotation, validation |
| **UI Generation** | Frontend architecture - AMIS Schema generation, dynamic form rendering, voice integration |
| **Server Deployment** | Backend infrastructure - FastAPI + Celery + Redis + MySQL service orchestration |
| **Workflow Execution** | State machine design - workflow persistence, node progression, checkpoint and recovery |

![Dataset Flow](screenshots/arch-dataset-flow.png)
![UI Generation](screenshots/arch-ui-generation.png)
![Server Deployment](screenshots/arch-server-deployment.png)
![Workflow Execution](screenshots/arch-workflow-execution.png)

---

## Screenshots

| Login | Workflow Chat |
|:------:|:------:|
| ![Login](screenshots/screenshot-login.png) | ![Workflow](screenshots/screenshot-workflow.png) |

| Workflow Form | Voice Interaction |
|:------:|:------:|
| ![Form](screenshots/screenshot-workflow-form.png) | ![Voice](screenshots/screenshot-voice-flow.png) |

| Main Interface | Developer Panel |
|:------:|:------:|
| ![Main](screenshots/screenshot-main.png) | ![Developer](screenshots/screenshot-developer-panel.png) |

![Workflow Execution Flow](screenshots/mermaid-workflow-diagram.png)

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Multilingual** | Supports voice and text input in multiple languages |
| **Security-First** | Multi-layer defense: RBAC + JWT + dynamic route validation + audit logging |
| **Real-Time Generation** | LLM inference + schema assembly + UI rendering in seconds |
| **Zero-Code Configuration** | Configure entities, workflows, and permissions via visual panel |
| **Voice Interaction** | Built-in Web Speech API for hands-free operation |
| **Multi-Scenario** | Built-in: train ticket, e-commerce, healthcare, hotel, banking, logistics, education, and more. Define your own scenarios with zero code. |

---

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/mxyooR/AILF.git
cd AILF
docker-compose up -d
```

After startup:
- **User UI**: http://localhost:3000
- **Developer Panel**: http://localhost:3000/config
- **API Docs**: http://localhost:5000/docs

### Manual Installation

Prerequisites: Python 3.10+, Node.js 18+, pnpm 8+, Redis 6+, MySQL 8.0+

```bash
# 1. Create Python environment
conda create -n ailf_env python=3.11
conda activate ailf_env

# 2. Install backend dependencies
cd backend
cp .env.example .env
pip install -r requirements.txt

# 3. Initialize database
python scripts/init_db.py

# 4. Install frontend dependencies
cd ../frontend
pnpm install

# 5. Start services (3 terminals needed)
# Terminal 1 - Backend: cd backend && python main.py
# Terminal 2 - Frontend: cd frontend && pnpm dev
# Terminal 3 - Worker: cd celery_worker && celery -A celery_app worker --loglevel=info
```

See [docs/](docs/) for complete documentation.

---

## Two-Round LLM Architecture

AILF uses an "intent recognition + slot filling" two-round LLM architecture with LoRA fine-tuning for domain adaptation.

```
Round 1: Intent Recognition
+----------------------------------------------------+
|  User: "Buy a high-speed train ticket from Beijing |
|         to Shanghai tomorrow morning"              |
|                                                    |
|  System:                                           |
|    intent: WORKFLOW                                |
|    candidate_workflows: [train_ticket]            |
|    confidence: 0.95                                |
+----------------------------------------------------+

Round 2: Slot Filling
+----------------------------------------------------+
|  Scene: train_ticket                              |
|                                                    |
|  Slots:                                            |
|    date: 2024-XX-XX                               |
|    departure: Beijing                               |
|    destination: Shanghai                            |
|    time_range: morning (06:00-12:00)              |
|    seat_type: second_class                         |
+----------------------------------------------------+
```

```bash
# LoRA Fine-tuning
cd Model
python train_pure_llm_v11.py
```

---

## Security Architecture

| Layer | Mechanism | Description |
|-------|-----------|-------------|
| **1. Candidate Constraint** | Scope restriction | AI only selects from user authorized APIs/workflows |
| **2. Dynamic Route** | Runtime validation | Endpoint and parameter validity checked at runtime |
| **3. Authorization** | RBAC | Role-based access control |
| **4. Authentication** | JWT Dual Token | Access + Refresh token rotation |
| **5. Session Governance** | Concurrency limit | Max sessions, revocation list |
| **6. Audit** | Structured logging | JSON logs, sensitive fields auto-masked |

---

## Configuration Guide

### Entity Configuration

```json
{
  "name": "train_ticket",
  "display_name": "Train Ticket",
  "fields": [
    {"name": "departure", "type": "string", "label": "Departure", "required": true},
    {"name": "destination", "type": "string", "label": "Destination", "required": true},
    {"name": "date", "type": "date", "label": "Travel Date", "required": true},
    {"name": "seat_type", "type": "enum", "label": "Seat Type", "options": ["Second", "First", "Business"]}
  ]
}
```

### Workflow Configuration

```json
{
  "name": "train_ticket_purchase",
  "display_name": "Ticket Purchase Flow",
  "steps": [
    {"step": 1, "name": "query_trains", "action": "Search Trains", "entity": "train_ticket", "api_endpoint": "/api/trains/search"},
    {"step": 2, "name": "select_train", "action": "Select Train", "display": "table"},
    {"step": 3, "name": "confirm_order", "action": "Confirm Order", "form": "passenger_info"},
    {"step": 4, "name": "payment", "action": "Payment", "api_endpoint": "/api/payment/create"}
  ]
}
```

### Permission Configuration

```json
{
  "roles": [
    {"name": "admin", "permissions": ["*"]},
    {"name": "user", "workflows": ["train_ticket_purchase"], "apis": ["/api/trains/*"]},
    {"name": "guest", "workflows": ["query_only"], "apis": ["/api/trains/search"]}
  ]
}
```

---

## Project Structure

```
AILF/
+-- backend/              # FastAPI Backend
|   +-- app/
|   |   +-- api/v1/       # API Routes
|   |   +-- core/         # Core Modules (AI, Auth, Dynamic Router)
|   |   +-- models/       # SQLAlchemy Models
|   |   +-- schemas/      # Pydantic Models
|   |   +-- services/     # Business Logic
|   +-- scripts/          # Operations Scripts
|   +-- tests/            # Test Cases
+-- frontend/             # React + AMIS Frontend
+-- celery_worker/        # Inference Worker
+-- Model/                # Training
+-- docs/                 # Documentation
+-- screenshots/          # Screenshots
+-- docker-compose.yml    # Docker Orchestration
+-- README.md
```

---

## Testing

```bash
cd backend
python -m pytest tests/
python -m pytest tests/ --cov=app --cov-report=html
```

---

## FAQ

**Q: Which LLM models does AILF support?**
A: Any OpenAI API-compatible model, including Qwen, Llama, GPT-4, etc.

**Q: What is the intent recognition accuracy?**
A: 95%+ on domain-specific tasks after LoRA fine-tuning.

**Q: Is voice input required?**
A: No. Both text and voice input are supported.

**Q: How do I add a new business scenario?**
A: Configure entities, workflows, and permissions in the developer panel - no coding needed.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## License

Distributed under the [MIT License](LICENSE).

## Acknowledgments

- [Baidu AMIS](https://aisuda.baidu.com/amis/zh/docs/index) — Low-code frontend framework
- [Qwen3](https://github.com/QwenLM/Qwen3) — LLM
- [BGE](https://github.com/FlagOpen/FlagEmbedding) — Embedding model
- [FastAPI](https://fastapi.tiangolo.com/) — High-performance web framework
- [Celery](https://docs.celeryq.dev/) — Async task queue
- [React](https://react.dev/) — UI library
- [Docker](https://www.docker.com/) — Containerization platform
- [Butterfly](https://github.com/alibaba/butterfly) (MIT) — Node-based visualization framework for workflow designer

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=mxyooR/AILF&type=Timeline)](https://star-history.com/#mxyooR/AILF&Timeline)
