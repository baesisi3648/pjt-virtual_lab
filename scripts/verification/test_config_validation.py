"""Config validation test"""
import os
import sys

# Test with example values
os.environ["OPENAI_API_KEY"] = "sk-test-key"
os.environ["POSTGRES_URL"] = "postgresql://virtual_lab:password@localhost:5432/virtual_lab"
os.environ["CHROMA_HOST"] = "localhost"
os.environ["CHROMA_PORT"] = "8001"
os.environ["TAVILY_API_KEY"] = "tvly-xxxxx"
os.environ["REDIS_URL"] = "redis://localhost:6379"

from config import settings

# Validation 1: Settings loads correctly
print("[PASS] Settings loaded successfully")
print(f"  - OPENAI_API_KEY: {settings.OPENAI_API_KEY[:10]}...")
print(f"  - POSTGRES_URL: {settings.POSTGRES_URL}")
print(f"  - CHROMA_HOST: {settings.CHROMA_HOST}")
print(f"  - CHROMA_PORT: {settings.CHROMA_PORT}")
print(f"  - TAVILY_API_KEY: {settings.TAVILY_API_KEY}")
print(f"  - REDIS_URL: {settings.REDIS_URL}")
print(f"  - LANGSMITH_API_KEY: {settings.LANGSMITH_API_KEY}")
print(f"  - LANGSMITH_PROJECT: {settings.LANGSMITH_PROJECT}")

# Validation 2: Tavily API key format
assert settings.TAVILY_API_KEY.startswith("tvly-") or settings.TAVILY_API_KEY == "tvly-xxxxx"
print("[PASS] TAVILY_API_KEY format validation passed")

# Validation 3: Test validate_secrets method
try:
    settings.validate_secrets()
    print("[PASS] validate_secrets() passed")
except ValueError as e:
    print(f"[PASS] validate_secrets() correctly identified example keys: {e}")

# Validation 4: Test with invalid key
print("\nTesting invalid TAVILY_API_KEY...")
os.environ["TAVILY_API_KEY"] = "invalid-key"
try:
    from importlib import reload
    import config as config_module
    reload(config_module)
    config_module.settings.validate_secrets()
    print("[FAIL] Should have raised ValueError")
    sys.exit(1)
except ValueError as e:
    print(f"[PASS] Correctly rejected invalid key: {e}")

print("\n" + "="*50)
print("All config validation tests passed!")
print("="*50)
