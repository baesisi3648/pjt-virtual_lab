# @TASK P2-R1, P3-T2 - 에이전트 패키지 초기화
# @SPEC TASKS.md#P2-R1, TASKS.md#P3-T2
"""Virtual Lab Agents

Specialists, Critic, PI 에이전트와 Dynamic Agent Factory를 제공합니다.
"""
from agents.scientist import run_specialists
from agents.pi import run_pi, run_pi_planning
# factory는 순환 import 방지를 위해 직접 import하지 않음
# 사용 시: from agents.factory import create_specialist

__all__ = ["run_specialists", "run_pi", "run_pi_planning"]
