# MVP 기획안: 유전자편집식품(NGT) 표준 안전성 평가 프레임워크 가상 연구실

## 1. 프로젝트 개요 (Overview)
- **프로젝트명**: Virtual Lab for NGT Safety Framework (MVP)
- **목표**: 유전자편집식품(NGT)이라는 '카테고리' 전체에 적용 가능한 **표준 안전성 평가 프레임워크(Standard Safety Assessment Framework)**를 도출하는 AI 에이전트 시스템 구축.
- **핵심 가치**: 개별 제품 평가가 아닌, "안전성을 입증하기 위해 최소한 어떤 자료가 필요한가?"에 대한 범용적 기준(Rule) 수립.
- **핵심 아키텍처**: PI(총괄)와 Critic(비평가) 중심의 **검증 루프(Critique Loop)** 구현.

## 2. 기술 스택 (Tech Stack)
- **Language**: Python 3.10+
- **Orchestration**: **LangGraph** (StateGraph, Conditional Edges 활용)
- **LLM Models**:
  - **GPT-4o**: PI 에이전트, Scientific Critic (고지능 추론 및 검증)
  - **GPT-4o-mini**: Scientist 에이전트 (초안 작성, 데이터 정리)
- **Backend**: FastAPI (API Server)
- **Frontend**: Streamlit (Chat UI & Markdown Report Viewer)
- **Env Management**: Poetry or venv

## 3. 시스템 아키텍처 (Architecture)

### 3.1 에이전트 정의 (Agents)
MVP에서는 **3개의 고정된 에이전트**를 운용한다. (동적 생성 없음)

| 에이전트명 | 역할 (Role) | 모델 (Model) | 주요 임무 (Responsibility) |
| :--- | :--- | :--- | :--- |
| **Risk Identifier**<br>(Scientist) | 위험 식별가 | `gpt-4o-mini` | - NGT 기술 자체의 특성(Off-target 등)에 기반한 잠재적 위험 요소 초안 작성.<br>- 기존 GMO 대비 차이점 서술. |
| **Scientific Critic** | 과학 비평가 | `gpt-4o` | - **[중요]** Scientist의 초안이 '특정 제품'이 아닌 '범용 카테고리'에 적용 가능한지 검증.<br>- 규제 가이드라인(Codex 등)과의 정합성 체크.<br>- 과도한 규제(Over-regulation) 여부 채점. |
| **PI** | 연구 책임자 | `gpt-4o` | - 프로젝트 목표(Scope) 주입.<br>- 최종 회의 주재 및 의견 종합.<br>- 최종 산출물(Framework Report) 포맷팅 및 승인. |

### 3.2 워크플로우 (LangGraph Workflow)
단일 순차 루프 구조를 따른다.

1.  **Start**: 사용자가 연구 주제 입력 ("유전자편집식품 표준 평가 틀 마련").
2.  **Node 1 (Drafting)**: **Risk Identifier**가 주어진 Context(가이드라인 텍스트)를 참고하여 위험 요소 및 필요 자료 목록 초안 작성.
3.  **Node 2 (Critique)**: **Scientific Critic**이 초안을 검토.
    - **Checklist**:
        1. 과학적 근거가 있는가?
        2. 특정 제품이 아닌 카테고리 전체에 적용 가능한가? (범용성)
        3. 불필요하게 과도한 자료를 요구하지 않는가?
    - **Output**: 수정 제안(Feedback) 또는 승인(Approve).
4.  **Edge (Condition)**:
    - If `Feedback` exists -> **Node 1**로 회귀 (재작성 요청, 최대 2회).
    - If `Approve` -> **Node 3**로 진행.
5.  **Node 3 (Finalizing)**: **PI**가 최종 내용을 정리하여 Markdown 보고서 생성.
6.  **End**: UI에 결과 출력.

## 4. 데이터 전략 (Data Strategy for MVP)
복잡한 RAG(Vector DB) 대신, **Context Injection(텍스트 주입)** 방식을 사용한다.

- **System Prompt에 포함될 필수 데이터 (Text Assets)**:
    1.  **연구 목표 정의서**: "개별 제품이 아닌 카테고리 평가 틀을 만든다"는 대원칙.
    2.  **국제 표준 요약 (Codex)**: 분자적 특성, 독성, 알레르기, 영양성 평가의 4대 원칙.
    3.  **규제 동향 (FDA/EU)**: Process-based vs Product-based 접근법의 차이 요약.
    4.  **비평 기준표 (Rubric)**: Critic이 사용할 채점 기준.

## 5. 구현 상세 (Implementation Details)

### 5.1 파일 구조 (Directory Structure)

```

virtual-lab-mvp/
├── app.py                # Streamlit Frontend
├── server.py             # FastAPI Backend
├── agents/
│   ├── **init**.py
│   ├── pi.py             # PI Agent Logic (GPT-4o)
│   ├── critic.py         # Critic Agent Logic (GPT-4o)
│   └── scientist.py      # Scientist Agent Logic (GPT-4o-mini)
├── workflow/
│   ├── **init**.py
│   └── graph.py          # LangGraph Construction
├── data/
│   └── guidelines.py     # Hardcoded Text Assets (Context)
├── utils/
│   └── llm.py            # Model Initialization (OpenAI)
├── .env                  # API Keys
└── requirements.txt

```

### 5.2 입출력 데이터 포맷 (IO Spec)

**Input (User -> System):**
```json
{
  "topic": "유전자편집식품(NGT) 표준 안전성 평가 프레임워크 수립",
  "constraints": "기존 GMO 규제 대비 합리적이고 과학적인 완화 기준 제시 필요"
}

```

**Output (System -> User):**

```markdown
# 유전자편집식품 표준 안전성 평가 프레임워크 (Final Report)

## 1. 개요
(PI 작성: 연구 목적 및 범위)

## 2. 공통 위험 식별 (General Risk Profile)
(Scientist 작성 & Critic 검증 완료: 기술적 위험 요소 나열)

## 3. 최소 제출 자료 요건 (Minimum Data Requirements)
- 필수 제출: ...
- 조건부 제출: ...
- 면제 가능: ...

## 4. 결론 및 제언
(PI 작성: 규제 당국을 위한 제언)

```

## 6. 개발 마일스톤 (Milestones)

1. **Setup**: 환경 설정 및 OpenAI API 연동.
2. **Data**: `data/guidelines.py`에 규제 가이드라인 텍스트 탑재.
3. **Graph**: LangGraph로 `Scientist -> Critic -> Loop` 로직 구현.
4. **Prompting**: Critic이 너무 깐깐하거나 느슨하지 않게 프롬프트 튜닝.
5. **UI**: Streamlit으로 채팅창 및 마크다운 뷰어 연동.

