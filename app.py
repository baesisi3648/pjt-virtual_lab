# @TASK P3-S1-T1 - Streamlit Chat UI 구현
# @SPEC TASKS.md#P3-S1-T1
"""Streamlit Frontend App

Virtual Lab 연구 워크플로우를 위한 대화형 UI입니다.
FastAPI 백엔드와 통신하여 AI 에이전트들의 논의 과정을 실시간으로 표시합니다.
"""
import streamlit as st
import httpx
from typing import Dict, List


# 페이지 설정
st.set_page_config(
    page_title="Virtual Lab - NGT Safety Framework",
    page_icon="🧬",
    layout="wide",
)

# 제목
st.title("🧬 Virtual Lab for NGT Safety Framework")
st.markdown("유전자편집식품(NGT) 표준 안전성 평가 프레임워크 도출 시스템")

# 2-Column 레이아웃
col_chat, col_report = st.columns([1, 1])

# 왼쪽: 입력 폼 + 회의 로그
with col_chat:
    st.header("📝 연구 설정")

    with st.form("research_form"):
        topic = st.text_area(
            "연구 주제",
            value="유전자편집식품(NGT) 표준 안전성 평가 가이드라인 초안",
            height=100,
        )
        constraints = st.text_area(
            "제약 조건 (선택)",
            value="기존 GMO처럼 무조건 엄격하게 하지 말고, 과학적 근거가 있을 때만 자료를 요구하도록 합리적으로 작성",
            height=80,
        )
        submitted = st.form_submit_button("🚀 워크플로우 실행", use_container_width=True)

    # 회의 로그 영역
    st.header("💬 회의 로그")
    log_container = st.container()

# 오른쪽: 보고서 뷰어
with col_report:
    st.header("📄 최종 보고서")
    report_container = st.container()

# 실행 버튼 클릭 시
if submitted:
    with log_container:
        st.info("🔄 워크플로우를 실행 중입니다...")

    try:
        # FastAPI 서버 호출
        with st.spinner("AI 에이전트들이 논의 중입니다..."):
            response = httpx.post(
                "http://localhost:8000/api/research",
                json={"topic": topic, "constraints": constraints},
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()

        # 회의 로그 표시
        with log_container:
            st.success("✅ 워크플로우 완료!")

            # 메시지 표시
            for msg in data.get("messages", []):
                role = msg.get("role", "")
                content = msg.get("content", "")

                if role == "scientist":
                    st.markdown(f"**👨‍🔬 Scientist (위험 식별가):**\n{content}")
                elif role == "critic":
                    st.markdown(f"**🕵️ Critic (과학 비평가):**\n{content}")
                elif role == "pi":
                    st.markdown(f"**🎓 PI (연구 책임자):**\n{content}")
                else:
                    st.markdown(f"**[시스템]:** {content}")

            st.caption(f"반복 횟수: {data.get('iterations', 0)}회")

        # 보고서 표시
        with report_container:
            st.markdown(data.get("report", "보고서가 생성되지 않았습니다."))

            # 다운로드 버튼
            st.download_button(
                label="📥 보고서 다운로드 (.md)",
                data=data.get("report", ""),
                file_name="ngt_safety_framework.md",
                mime="text/markdown",
                use_container_width=True,
            )

    except httpx.HTTPError as e:
        with log_container:
            st.error(f"❌ 서버 오류: {str(e)}")
            st.info("FastAPI 서버가 실행 중인지 확인하세요: `uvicorn server:app --reload`")
    except Exception as e:
        with log_container:
            st.error(f"❌ 예상치 못한 오류: {str(e)}")

# 초기 상태 안내
if not submitted:
    with log_container:
        st.info("👆 위의 입력 폼을 작성하고 '워크플로우 실행' 버튼을 클릭하세요.")

    with report_container:
        st.info("워크플로우가 완료되면 여기에 최종 보고서가 표시됩니다.")
