# @TASK P2-R1 - 에이전트 패키지 초기화
# @SPEC TASKS.md#P2-R1
"""Virtual Lab Agents

Scientist, Critic, PI 에이전트를 제공합니다.
"""
from agents.scientist import run_scientist
from agents.pi import run_pi

__all__ = ["run_scientist", "run_pi"]
