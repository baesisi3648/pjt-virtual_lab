# @TASK P3-R1-T1 - FastAPI Backend Server
# @SPEC TASKS.md#P3-R1-T1
# @TEST tests/test_server.py
"""FastAPI Backend Server

Virtual Lab 연구 워크플로우를 실행하는 REST API 서버입니다.
Streamlit 프론트엔드와 CORS를 통해 연동됩니다.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from workflow.graph import create_workflow
from workflow.state import AgentState
from celery_app import app as celery_app
from tasks.research_task import run_research as celery_run_research, health_check


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


class AsyncResearchRequest(BaseModel):
    """비동기 연구 요청 스키마"""
    query: str


class AsyncResearchResponse(BaseModel):
    """비동기 연구 응답 스키마"""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """태스크 상태 응답 스키마"""
    task_id: str
    status: str
    result: dict | None = None
    error: str | None = None


@app.get("/health")
def health_check_endpoint():
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


@app.post("/api/research/async", response_model=AsyncResearchResponse)
async def submit_async_research(request: AsyncResearchRequest):
    """비동기 연구 작업 제출

    장시간 소요되는 연구 작업을 Celery를 통해 백그라운드에서 실행합니다.
    task_id를 반환하며, /api/task/{task_id}로 상태를 조회할 수 있습니다.
    """
    try:
        task = celery_run_research.delay(request.query)
        return AsyncResearchResponse(
            task_id=task.id,
            status="processing",
            message="Research task submitted successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit research task: {str(e)}"
        )


@app.get("/api/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """태스크 상태 조회

    Celery 태스크의 현재 상태와 결과를 조회합니다.

    상태 종류:
    - PENDING: 대기 중
    - PROGRESS: 진행 중
    - SUCCESS: 완료
    - FAILURE: 실패
    """
    try:
        task = celery_app.AsyncResult(task_id)

        if task.state == 'PENDING':
            return TaskStatusResponse(
                task_id=task_id,
                status="pending",
                result=None
            )
        elif task.state == 'PROGRESS':
            return TaskStatusResponse(
                task_id=task_id,
                status="progress",
                result=task.info if task.info else None
            )
        elif task.state == 'SUCCESS':
            return TaskStatusResponse(
                task_id=task_id,
                status="success",
                result=task.result
            )
        elif task.state == 'FAILURE':
            return TaskStatusResponse(
                task_id=task_id,
                status="failure",
                result=None,
                error=str(task.info)
            )
        else:
            return TaskStatusResponse(
                task_id=task_id,
                status=task.state.lower(),
                result=task.info if task.info else None
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )


@app.get("/api/celery/health")
async def celery_health_check():
    """Celery 워커 헬스체크

    Celery 워커가 정상 작동하는지 확인합니다.
    """
    try:
        # Simple task to check if worker is alive
        result = health_check.delay()
        # Wait max 5 seconds
        response = result.get(timeout=5)
        return {
            "status": "ok",
            "celery_status": response.get("status"),
            "message": response.get("message")
        }
    except Exception as e:
        return {
            "status": "error",
            "celery_status": "unavailable",
            "message": f"Celery worker not responding: {str(e)}"
        }
