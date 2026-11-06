"""Fail-closed error types for the deliberation pipeline.

The revision protocol (reference/revision/revision_plan.md, C3, C12-C15) requires
that technical failures stop a run instead of silently substituting fallback
content (error strings, previous outputs, default teams, default scores).
A run that raises one of these errors is recorded as a technical failure and
retried under the pre-registered retry policy.
"""


class PipelineError(RuntimeError):
    """Base class for technical failures that must abort a run."""


class LLMIncompleteError(PipelineError):
    """The model returned an empty or truncated response."""


class SearchError(PipelineError):
    """A retrieval call (RAG, web, EFSA) failed."""


class AgentFailureError(PipelineError):
    """An agent step could not produce a valid output."""


class CritiqueValidationError(PipelineError):
    """Critic scores are missing, malformed, or out of range."""
