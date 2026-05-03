"""Virtual Lab Agents

Specialists, Critic, PI 에이전트와 Dynamic Agent Factory를 제공합니다.
3라운드 팀 회의 워크플로우.
"""
from agents.scientist import run_specialists, run_round_revision
from agents.pi import run_pi_planning, run_pi_summary, run_final_synthesis
# factory는 순환 import 방지를 위해 직접 import하지 않음
# 사용 시: from agents.factory import create_specialist

__all__ = ["run_specialists", "run_round_revision", "run_pi_planning", "run_pi_summary", "run_final_synthesis"]
