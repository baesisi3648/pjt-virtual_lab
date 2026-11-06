"""Prompt loader — external prompt asset loading.

Loads system prompts and data assets from `prompts/` (private, gitignored).
If the directory is missing, falls back to `prompts.example/` (public placeholders),
allowing the public repository to remain runnable without the proprietary prompts.

Override the prompts directory with the environment variable
`VIRTUAL_LAB_PROMPTS_DIR`.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parent.parent


def _resolve_prompts_dir() -> Path:
    """Pick the active prompts directory.

    Priority:
    1. `VIRTUAL_LAB_PROMPTS_DIR` environment variable.
    2. `<repo>/prompts` if it exists (private, gitignored).
    3. `<repo>/prompts.example` as a public fallback.
    """
    env_path = os.environ.get("VIRTUAL_LAB_PROMPTS_DIR")
    if env_path:
        p = Path(env_path).expanduser().resolve()
        if p.exists():
            return p
        # Revision: an explicitly requested prompt set must exist. Silently falling
        # back to `prompts/` would mix experimental conditions.
        raise FileNotFoundError(f"VIRTUAL_LAB_PROMPTS_DIR does not exist: {p}")

    private = _REPO_ROOT / "prompts"
    if private.exists():
        return private

    fallback = _REPO_ROOT / "prompts.example"
    if fallback.exists():
        return fallback

    raise FileNotFoundError(
        "No prompts directory found. Expected `prompts/` or `prompts.example/` "
        "at the repository root, or `VIRTUAL_LAB_PROMPTS_DIR` set to a valid path."
    )


@lru_cache(maxsize=64)
def load_prompt(category: str, name: str) -> str:
    """Load a prompt asset by category and name.

    Args:
        category: subdirectory under the prompts root (e.g. "system", "data").
        name: file stem (without .md extension).

    Returns:
        The full text of the prompt file, stripped of trailing whitespace.
    """
    base = _resolve_prompts_dir()
    path = base / category / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def load_data(name: str) -> str:
    """Shortcut for `load_prompt('data', name)`."""
    return load_prompt("data", name)


def load_system(name: str) -> str:
    """Shortcut for `load_prompt('system', name)`."""
    return load_prompt("system", name)


def render(template: str, **substitutions: str) -> str:
    """Substitute `{KEY}` placeholders in a template string.

    Uses simple `.replace` rather than `.format` to avoid clashes with
    JSON braces (`{ ... }`) in prompt bodies.
    """
    rendered = template
    for key, value in substitutions.items():
        rendered = rendered.replace("{" + key + "}", value)
    return rendered


def active_prompts_dir() -> str:
    """Return the absolute path of the prompts directory currently in use."""
    return str(_resolve_prompts_dir())
