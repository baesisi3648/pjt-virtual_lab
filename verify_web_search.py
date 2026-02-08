#!/usr/bin/env python3
"""
Verification Script for P2-T3: Agent Search Integration

This script verifies that all agents have web_search tool integration
by checking source files directly (without importing to avoid circular deps).
"""
import os


def verify_agent_file(agent_name):
    """Check agent source file for web_search integration"""
    file_path = os.path.join("agents", f"{agent_name}.py")

    if not os.path.exists(file_path):
        return {"exists": False}

    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    # Check for web_search import
    has_import = "from tools.web_search import web_search" in source

    # Check for bind_tools usage
    has_bind_tools = "bind_tools" in source and "bind_tools([web_search])" in source

    # Check for system prompt guidance
    has_prompt_guidance = "web_search" in source and any(
        keyword in source for keyword in ["최신", "검색", "검증", "인용"]
    )

    return {
        "exists": True,
        "has_import": has_import,
        "has_bind_tools": has_bind_tools,
        "has_prompt_guidance": has_prompt_guidance,
    }


def main():
    print("=" * 60)
    print("VERIFICATION: Agent Web Search Integration (P2-T3)")
    print("=" * 60)
    print()

    agents = ["scientist", "critic", "pi"]
    results = {}

    for agent_name in agents:
        print(f"[{agent_name.upper()}] Checking web_search integration...")

        check = verify_agent_file(agent_name)

        if not check["exists"]:
            print(f"  X File not found: agents/{agent_name}.py")
            results[agent_name] = False
            print()
            continue

        # Check import
        if check["has_import"]:
            print(f"  OK web_search imported successfully")
        else:
            print(f"  X web_search NOT imported")

        # Check bind_tools
        if check["has_bind_tools"]:
            print(f"  OK Uses bind_tools() for tool binding")
        else:
            print(f"  X Does NOT use bind_tools()")

        # Check system prompt
        if check["has_prompt_guidance"]:
            print(f"  OK System prompt includes web_search guidance")
        else:
            print(f"  X System prompt missing web_search guidance")

        passed = all([
            check["has_import"],
            check["has_bind_tools"],
            check["has_prompt_guidance"]
        ])
        results[agent_name] = passed

        print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = all(results.values())

    for agent, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {agent.upper()}: {status}")

    print()
    if all_passed:
        print("SUCCESS: ALL AGENTS HAVE WEB_SEARCH INTEGRATION!")
        print()
        print("Next steps:")
        print("  1. Run tests: pytest tests/test_web_search_integration.py -v")
        print("  2. Test with real query (requires TAVILY_API_KEY)")
        return 0
    else:
        print("FAILURE: SOME AGENTS FAILED INTEGRATION CHECK")
        return 1


if __name__ == "__main__":
    exit(main())
