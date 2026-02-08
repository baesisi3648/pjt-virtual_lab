# @TASK P3-R1-T1 - FastAPI Backend Server
# @SPEC TASKS.md#P3-R1-T1
# @TEST tests/test_server.py
"""FastAPI Backend Server

Virtual Lab 연구 워크플로우를 실행하는 REST API 서버입니다.
Streamlit 프론트엔드와 CORS를 통해 연동됩니다.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from workflow.graph import create_workflow
from workflow.state import AgentState


app = FastAPI(title="Virtual Lab API")

# CORS 설정 (Streamlit 연동)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResearchRequest(BaseModel):
    """연구 요청 스키마"""
    topic: str
    constraints: str = ""


class ResearchResponse(BaseModel):
    """연구 응답 스키마"""
    report: str
    messages: list[dict]
    iterations: int


@app.get("/health")
def health_check():
    """헬스체크"""
    return {"status": "ok"}


@app.post("/api/research", response_model=ResearchResponse)
def run_research(request: ResearchRequest):
    """워크플로우 실행

    LangGraph 워크플로우를 생성하고 초기 상태로 실행합니다.
    Scientist -> Critic -> PI 흐름을 거쳐 최종 보고서를 반환합니다.
    """
    # 워크플로우 생성
    workflow = create_workflow()

    # 초기 상태
    initial_state: AgentState = {
        "topic": request.topic,
        "constraints": request.constraints,
        "draft": "",
        "critique": None,
        "iteration": 0,
        "final_report": "",
        "messages": [],
    }

    # 실행
    result = workflow.invoke(initial_state)

    return ResearchResponse(
        report=result["final_report"],
        messages=result["messages"],
        iterations=result["iteration"],
    )
