# Virtual Lab MVP - Project Memory

## Project Overview
- **Name**: Virtual Lab for NGT Safety Framework (MVP)
- **Purpose**: AI agent system for deriving standard safety assessment framework for gene-edited foods (NGT)
- **Architecture**: PI + Critic + Scientist agents → LangGraph Critique Loop

## Tech Stack
- Backend: FastAPI + LangGraph + OpenAI API (GPT-4o, GPT-4o-mini)
- Frontend: Streamlit (Chat UI + Report Viewer)
- Data: Context Injection (no DB, no RAG)
- No authentication required

## Key Decisions
- 3 fixed agents (no dynamic agent creation)
- Max 2 critique loop iterations
- SSE streaming for real-time meeting log
- Hardcoded guideline text assets (Codex, FDA, Rubric)

## Agent Roles
| Agent | Model | Role |
|-------|-------|------|
| Risk Identifier (Scientist) | GPT-4o-mini | Draft risk factors |
| Scientific Critic | GPT-4o | Validate drafts for universality |
| PI | GPT-4o | Final report generation |
