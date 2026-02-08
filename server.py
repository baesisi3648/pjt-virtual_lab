# @TASK P3-R1-T1 - FastAPI Backend Server
# @SPEC TASKS.md#P3-R1-T1
# @TEST tests/test_server.py
"""FastAPI Backend Server

Virtual Lab 연구 워크플로우를 실행하는 REST API 서버입니다.
Streamlit 프론트엔드와 CORS를 통해 연동됩니다.
"""
import asyncio
import json
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from workflow.graph import create_workflow
from workflow.state import AgentState
from celery_app import app as celery_app
from tasks.research_task import run_research as celery_run_research, health_check


app = FastAPI(title="Virtual Lab API")

# CORS 설정 (Streamlit + Next.js 연동)
# 개발 환경: 모든 오리진 허용
# 프로덕션 환경: 특정 오리진만 허용 권장
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:8501",  # Streamlit dev server
        "*",  # 개발 편의를 위해 모든 오리진 허용
    ],
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


class RegenerateRequest(BaseModel):
    """보고서 섹션 재생성 요청 스키마"""
    section: str
    feedback: str
    current_report: str = ""


class RegenerateResponse(BaseModel):
    """보고서 섹션 재생성 응답 스키마"""
    updated_report: str
    section: str
    message: str


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


# P4-T2: SSE 엔드포인트
async def generate_research_events(topic: str, constraints: str) -> AsyncGenerator[str, None]:
    """연구 프로세스 이벤트를 SSE 형식으로 스트리밍합니다.

    Args:
        topic: 연구 주제
        constraints: 제약 조건

    Yields:
        str: SSE 형식의 이벤트 문자열 (data: {...}\n\n)
    """
    def send_event(event_type: str, data: dict):
        """SSE 이벤트 전송 헬퍼"""
        event_data = {
            "type": event_type,
            "timestamp": asyncio.get_event_loop().time(),
            **data
        }
        return f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"

    try:
        # 시작 이벤트
        yield send_event("start", {
            "message": "연구 프로세스를 시작합니다...",
            "topic": topic
        })

        # 워크플로우 생성
        workflow = create_workflow()

        # 초기 상태
        initial_state: AgentState = {
            "topic": topic,
            "constraints": constraints,
            "draft": "",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
        }

        # Phase 1: Drafting 시작
        yield send_event("phase", {
            "phase": "drafting",
            "agent": "scientist",
            "message": "🔬 Scientist: 위험 요소 분석 중..."
        })

        await asyncio.sleep(0.1)  # 이벤트 전송 보장

        # 워크플로우 실행 (스트림 모드)
        # LangGraph의 stream() 메서드는 동기 API이므로 asyncio.to_thread로 실행
        iteration_count = 0
        final_result = None

        # 동기 stream을 비동기 generator로 변환
        for event in workflow.stream(initial_state):
            # 노드별 이벤트 전송
            for node_name, node_state in event.items():
                if node_name == "drafting":
                    yield send_event("agent", {
                        "agent": "scientist",
                        "phase": "drafting",
                        "message": "🔬 Scientist: 초안 작성 완료",
                        "iteration": iteration_count + 1
                    })
                elif node_name == "critique":
                    yield send_event("agent", {
                        "agent": "critic",
                        "phase": "critique",
                        "message": "🔍 Critic: 초안 검토 중...",
                        "iteration": iteration_count + 1
                    })

                    # Critique 결과 확인
                    if node_state.get("critique"):
                        critique = node_state["critique"]
                        decision = critique.decision

                        if decision == "revise":
                            yield send_event("decision", {
                                "agent": "critic",
                                "decision": "revise",
                                "message": "❌ Critic: 수정 필요",
                                "feedback": critique.feedback[:100] + "..."
                            })
                        else:
                            yield send_event("decision", {
                                "agent": "critic",
                                "decision": "approve",
                                "message": "✅ Critic: 승인"
                            })

                elif node_name == "increment":
                    iteration_count += 1
                    yield send_event("iteration", {
                        "iteration": iteration_count,
                        "message": f"🔄 반복 {iteration_count}회차 시작"
                    })

                elif node_name == "finalizing":
                    yield send_event("agent", {
                        "agent": "pi",
                        "phase": "finalizing",
                        "message": "👔 PI: 최종 보고서 작성 중..."
                    })

                # 최종 상태 저장
                final_result = node_state

        # 워크플로우 최종 상태 가져오기
        result = final_result if final_result else workflow.invoke(initial_state)

        # 완료 이벤트
        yield send_event("complete", {
            "message": "✅ 연구 프로세스 완료",
            "report": result["final_report"],
            "iterations": result["iteration"],
            "messages": result["messages"]
        })

    except Exception as e:
        # 에러 이벤트
        yield send_event("error", {
            "message": f"에러 발생: {str(e)}",
            "error": str(e)
        })


@app.post("/api/research/stream")
async def stream_research(request: ResearchRequest):
    """연구 프로세스를 SSE로 스트리밍합니다.

    실시간으로 에이전트 상태를 전송하여 프론트엔드에서 타임라인을 표시할 수 있습니다.

    이벤트 타입:
    - start: 프로세스 시작
    - phase: 단계 변경 (drafting, critique, finalizing)
    - agent: 에이전트 활동 (scientist, critic, pi)
    - decision: Critic 결정 (approve/revise)
    - iteration: 반복 횟수 변경
    - complete: 프로세스 완료
    - error: 에러 발생
    """
    return StreamingResponse(
        generate_research_events(request.topic, request.constraints),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx 버퍼링 방지
        }
    )


@app.post("/api/report/regenerate", response_model=RegenerateResponse)
def regenerate_section(request: RegenerateRequest):
    """보고서 특정 섹션을 재생성합니다.

    사용자 피드백을 받아 해당 섹션만 다시 작성합니다.
    Scientist 에이전트가 원본 보고서와 피드백을 참고하여 재작성합니다.

    Args:
        request: 섹션명, 피드백, 현재 보고서

    Returns:
        업데이트된 보고서 전체
    """
    from agents.scientist import ScientistAgent
    from config import Config

    try:
        # Scientist 에이전트 생성
        scientist = ScientistAgent(Config.OPENAI_MODEL)

        # 재생성 프롬프트 작성
        prompt = f"""다음 보고서의 '{request.section}' 섹션을 사용자 피드백에 따라 개선하세요.

<현재 보고서>
{request.current_report}
</현재 보고서>

<사용자 피드백>
{request.feedback}
</사용자 피드백>

<지침>
1. '{request.section}' 섹션만 재작성하세요
2. 사용자 피드백을 충분히 반영하세요
3. 다른 섹션은 그대로 유지하세요
4. 마크다운 형식을 유지하세요
5. 전체 보고서 구조를 유지하세요

<개선된 전체 보고서를 출력하세요>
"""

        # 에이전트 실행 (간단한 직접 호출)
        # 실제로는 scientist의 LLM을 직접 호출
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage

        llm = ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.3,
        )

        response = llm.invoke([HumanMessage(content=prompt)])
        updated_report = response.content

        return RegenerateResponse(
            updated_report=updated_report,
            section=request.section,
            message=f"'{request.section}' 섹션이 재생성되었습니다."
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to regenerate section: {str(e)}"
        )
