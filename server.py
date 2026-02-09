# @TASK P3-R1-T1 - FastAPI Backend Server
# @SPEC TASKS.md#P3-R1-T1
# @TEST tests/test_server.py
"""FastAPI Backend Server

Virtual Lab 연구 워크플로우를 실행하는 REST API 서버입니다.
Streamlit 프론트엔드와 CORS를 통해 연동됩니다.
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

# __pycache__ 사용 방지 - 캐시된 .pyc가 오래된 코드를 로드하는 것을 방지
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECACHE"] = "1"

# LangChain/LangSmith auto-instrumentation 비활성화
# - LangSmith tracing이 OpenAI SDK를 auto-instrument하여
#   tool_calls 관련 문제를 일으킬 수 있음
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_TRACING"] = "false"

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel

# 보고서 저장 디렉토리
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

from workflow.graph import create_workflow
from workflow.state import AgentState

# Celery는 선택적 (Redis 없이도 서버 시작 가능)
try:
    from celery_app import app as celery_app
    from tasks.research_task import run_research as celery_run_research, health_check
    CELERY_AVAILABLE = True
except Exception:
    CELERY_AVAILABLE = False

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

app = FastAPI(title="Virtual Lab API")

# 서버 시작 시 로드된 모듈 검증
startup_logger = logging.getLogger("startup")
startup_logger.info("=" * 60)
startup_logger.info("Virtual Lab Server Starting - Module Verification")
import agents.scientist as _sci_mod
import agents.critic as _cri_mod
import agents.pi as _pi_mod
import utils.llm as _llm_mod
startup_logger.info(f"  scientist.py: {_sci_mod.__file__}")
startup_logger.info(f"  critic.py:    {_cri_mod.__file__}")
startup_logger.info(f"  pi.py:        {_pi_mod.__file__}")
startup_logger.info(f"  llm.py:       {_llm_mod.__file__}")
# 핵심 체크: bind_tools나 ChatOpenAI가 에이전트에 없는지 확인
import inspect
for mod_name, mod in [("scientist", _sci_mod), ("critic", _cri_mod), ("pi", _pi_mod)]:
    src = inspect.getsource(mod)
    if "bind_tools" in src or "ChatOpenAI" in src:
        startup_logger.error(f"  DANGER: {mod_name} still has bind_tools/ChatOpenAI!")
    else:
        startup_logger.info(f"  OK: {mod_name} - no bind_tools/ChatOpenAI")
# LLM 모듈이 httpx 직접 호출을 사용하는지 확인
llm_src = inspect.getsource(_llm_mod)
if "httpx" in llm_src and "from openai import" not in llm_src:
    startup_logger.info("  OK: llm.py - using raw httpx (no OpenAI SDK)")
else:
    startup_logger.warning("  WARNING: llm.py - may still use OpenAI SDK")
startup_logger.info(f"  LANGCHAIN_TRACING_V2={os.environ.get('LANGCHAIN_TRACING_V2', 'not set')}")
startup_logger.info("=" * 60)

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


class ReportFileInfo(BaseModel):
    """보고서 파일 정보"""
    filename: str
    topic: str
    created_at: str
    size: int


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


def save_report_to_file(report: str, topic: str) -> str:
    """최종 보고서를 텍스트 파일로 저장합니다."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 파일명에서 특수문자 제거
    safe_topic = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in topic)[:50].strip()
    filename = f"report_{timestamp}_{safe_topic}.txt"
    filepath = REPORTS_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"{'='*80}\n")
        f.write(f"  Virtual Lab - 최종 연구 보고서\n")
        f.write(f"  연구 주제: {topic}\n")
        f.write(f"  생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*80}\n\n")
        f.write(report)

    logging.getLogger("report").info(f"Report saved: {filepath}")
    return filename


@app.get("/health")
def health_check_endpoint():
    """헬스체크"""
    return {"status": "ok"}


@app.get("/api/debug/modules")
def debug_modules():
    """서버에 로드된 모듈 상태 진단 (디버깅용)"""
    import inspect
    import time
    import agents.scientist as sci
    import agents.critic as cri
    import agents.pi as pi
    import utils.llm as llm_mod

    results = {"timestamp": time.time(), "modules": {}}

    for name, mod in [("scientist", sci), ("critic", cri), ("pi", pi), ("llm", llm_mod)]:
        src = inspect.getsource(mod)
        results["modules"][name] = {
            "file": mod.__file__,
            "has_bind_tools": "bind_tools" in src,
            "has_ChatOpenAI": "ChatOpenAI" in src,
            "has_call_gpt4o": "call_gpt4o" in src,
            "has_openai_sdk": "from openai import" in src or "OpenAI(" in src,
            "source_length": len(src),
        }

    # LLM 빠른 테스트 (실제 OpenAI 호출)
    try:
        from utils.llm import call_gpt4o_mini
        test_result = call_gpt4o_mini("Say 'OK'", "Test", max_tokens=5)
        results["llm_test"] = {"status": "ok", "response": test_result[:50]}
    except Exception as e:
        results["llm_test"] = {"status": "error", "error": str(e)}

    return results


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
        "team": [],
        "specialist_outputs": [],
        "draft": "",
        "critique": None,
        "iteration": 0,
        "final_report": "",
        "messages": [],
        "parallel_views": [],
    }

    # 실행
    result = workflow.invoke(initial_state)

    # 보고서 파일 저장
    if result["final_report"]:
        try:
            save_report_to_file(result["final_report"], request.topic)
        except Exception as e:
            logging.getLogger("report").warning(f"Failed to save report: {e}")

    return ResearchResponse(
        report=result["final_report"],
        messages=result["messages"],
        iterations=result["iteration"],
    )


@app.post("/api/research/async", response_model=AsyncResearchResponse)
async def submit_async_research(request: AsyncResearchRequest):
    """비동기 연구 작업 제출"""
    if not CELERY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Celery not available (Redis required)")
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
    """태스크 상태 조회"""
    if not CELERY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Celery not available")
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
    """Celery 워커 헬스체크"""
    if not CELERY_AVAILABLE:
        return {"status": "unavailable", "celery_status": "not_configured", "message": "Celery not available"}
    try:
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
import logging
import traceback

sse_logger = logging.getLogger("sse")


async def generate_research_events(topic: str, constraints: str) -> AsyncGenerator[str, None]:
    """연구 프로세스 이벤트를 SSE 형식으로 스트리밍합니다."""
    import time

    def send_event(event_type: str, data: dict):
        """SSE 이벤트 전송 헬퍼"""
        event_data = {
            "type": event_type,
            "timestamp": time.time(),
            **data
        }
        return f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"

    try:
        print(f"\n{'*'*80}")
        print(f"[SSE STREAM] Starting research workflow stream")
        print(f"  Topic: {topic}")
        print(f"  Constraints: {constraints}")
        print(f"{'*'*80}\n")

        # 시작 이벤트
        yield send_event("start", {
            "message": "연구 프로세스를 시작합니다...",
            "topic": topic
        })

        # 워크플로우 생성
        print(f"[SSE STREAM] Creating workflow graph...")
        workflow = create_workflow()
        print(f"[SSE STREAM] Workflow graph created successfully\n")

        # 초기 상태
        initial_state: AgentState = {
            "topic": topic,
            "constraints": constraints,
            "team": [],
            "specialist_outputs": [],
            "draft": "",
            "critique": None,
            "iteration": 0,
            "final_report": "",
            "messages": [],
            "parallel_views": [],
        }

        # Phase 1: Planning 시작
        yield send_event("phase", {
            "phase": "planning",
            "agent": "pi",
            "message": "PI: 연구 주제를 분석하고 전문가 팀을 구성 중..."
        })

        await asyncio.sleep(0.1)

        # 워크플로우 실행 (스트림 모드)
        iteration_count = 0
        final_report = ""
        all_messages: list[dict] = []

        sse_logger.info(f"Starting workflow stream for topic: {topic}")
        print(f"[SSE STREAM] Starting workflow.stream() iteration...\n")

        for event in workflow.stream(initial_state):
            for node_name, node_state in event.items():
                print(f"\n{'*'*80}")
                print(f"[SSE STREAM] Node event received")
                print(f"  Node: {node_name}")
                print(f"  State keys: {list(node_state.keys())}")
                print(f"{'*'*80}\n")

                sse_logger.info(f"Node: {node_name}, keys: {list(node_state.keys())}")

                if node_name == "planning":
                    team = node_state.get("team", [])
                    team_summary = "\n".join(
                        [f"- {m.get('role', '전문가')}: {m.get('focus', '')}" for m in team]
                    )
                    yield send_event("agent", {
                        "agent": "pi",
                        "phase": "planning",
                        "message": f"전문가 팀을 구성했습니다. ({len(team)}명)",
                        "content": team_summary,
                    })
                    # researching phase 시작 알림
                    yield send_event("phase", {
                        "phase": "researching",
                        "agent": "specialist",
                        "message": "전문가 팀이 개별 분석을 수행 중..."
                    })

                elif node_name == "researching":
                    specialist_outputs = node_state.get("specialist_outputs", [])
                    # 각 전문가별 분석 결과를 개별 이벤트로 전송
                    for so in specialist_outputs:
                        yield send_event("agent", {
                            "agent": "specialist",
                            "phase": "researching",
                            "message": f"[{so.get('role', '전문가')}] 분석을 완료했습니다.",
                            "content": so.get("output", ""),
                            "specialist_name": so.get("role", ""),
                            "specialist_focus": so.get("focus", ""),
                            "iteration": iteration_count + 1,
                        })

                elif node_name == "critique":
                    critique = node_state.get("critique")
                    if critique:
                        decision = critique.decision
                        sse_logger.info(f"Critic decision: {decision}, scores: {critique.scores}")

                        if decision == "revise":
                            yield send_event("decision", {
                                "agent": "critic",
                                "decision": "revise",
                                "message": "수정이 필요합니다.",
                                "content": critique.feedback,
                                "scores": critique.scores,
                                "iteration": iteration_count + 1
                            })
                        else:
                            yield send_event("decision", {
                                "agent": "critic",
                                "decision": "approve",
                                "message": "초안을 승인합니다.",
                                "scores": critique.scores,
                                "iteration": iteration_count + 1
                            })

                elif node_name == "increment":
                    iteration_count += 1
                    sse_logger.info(f"Iteration incremented to {iteration_count}")
                    yield send_event("iteration", {
                        "iteration": iteration_count,
                        "message": f"{iteration_count}회차 수정을 시작합니다."
                    })

                elif node_name == "finalizing":
                    final = node_state.get("final_report", "")
                    yield send_event("agent", {
                        "agent": "pi",
                        "phase": "finalizing",
                        "message": "최종 보고서를 작성했습니다.",
                        "content": final,
                    })

                # 각 노드의 결과에서 필요한 값 수집
                if "final_report" in node_state and node_state["final_report"]:
                    final_report = node_state["final_report"]
                if "messages" in node_state:
                    all_messages = node_state["messages"]
                if "team" in node_state:
                    pass  # team은 state에 자동 저장됨

        sse_logger.info(f"Workflow complete. Report length: {len(final_report)}, iterations: {iteration_count}")

        # 보고서 파일 저장
        saved_filename = ""
        if final_report:
            try:
                saved_filename = save_report_to_file(final_report, topic)
                sse_logger.info(f"Report saved to file: {saved_filename}")
            except Exception as e:
                sse_logger.warning(f"Failed to save report file: {e}")

        # 완료 이벤트
        yield send_event("complete", {
            "message": "연구 프로세스 완료",
            "report": final_report,
            "iterations": iteration_count,
            "messages": all_messages,
            "saved_filename": saved_filename,
        })

    except Exception as e:
        error_detail = traceback.format_exc()

        print(f"\n{'!'*80}")
        print(f"[SSE STREAM ERROR] Exception caught in SSE stream!")
        print(f"  Exception type: {type(e).__name__}")
        print(f"  Exception message: {e}")
        print(f"  Traceback:")
        print(error_detail)
        print(f"{'!'*80}\n")

        sse_logger.error(f"SSE Error: {error_detail}")

        # 에러 이벤트 - 상세 정보 포함
        yield send_event("error", {
            "message": f"에러 발생: {str(e)}",
            "error": f"{type(e).__name__}: {str(e)}\n{error_detail}"
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
    from utils.llm import call_gpt4o_mini

    try:
        system_prompt = "당신은 보고서 편집 전문가입니다."
        user_message = f"""다음 보고서의 '{request.section}' 섹션을 사용자 피드백에 따라 개선하세요.

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

개선된 전체 보고서를 출력하세요.
"""

        updated_report = call_gpt4o_mini(system_prompt, user_message, temperature=0.3)

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


@app.get("/api/reports")
def list_reports():
    """저장된 보고서 목록을 반환합니다."""
    reports = []
    for f in sorted(REPORTS_DIR.glob("report_*.txt"), reverse=True):
        # 파일명에서 정보 추출: report_20260208_143000_topic.txt
        parts = f.stem.split("_", 3)
        topic = parts[3] if len(parts) > 3 else "unknown"
        created = f"{parts[1][:4]}-{parts[1][4:6]}-{parts[1][6:8]} {parts[2][:2]}:{parts[2][2:4]}:{parts[2][4:6]}" if len(parts) > 2 else ""
        reports.append(ReportFileInfo(
            filename=f.name,
            topic=topic.replace("_", " "),
            created_at=created,
            size=f.stat().st_size,
        ))
    return {"reports": reports}


@app.get("/api/reports/{filename}")
def download_report(filename: str):
    """저장된 보고서 파일을 다운로드합니다."""
    filepath = REPORTS_DIR / filename
    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(status_code=404, detail="Report not found")
    # 경로 조작 방지
    if filepath.resolve().parent != REPORTS_DIR.resolve():
        raise HTTPException(status_code=403, detail="Access denied")
    return FileResponse(
        path=str(filepath),
        media_type="text/plain; charset=utf-8",
        filename=filename,
    )
