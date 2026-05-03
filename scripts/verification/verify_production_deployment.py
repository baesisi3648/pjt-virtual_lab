#!/usr/bin/env python3
"""
Production Deployment Verification Script (P4-T5)

This script verifies that all production deployment files are in place
and have the correct structure.
"""

import os
import sys


WORKTREE_ROOT = os.path.dirname(os.path.abspath(__file__))


def check_file_exists(filepath, description):
    """Check if a file exists"""
    full_path = os.path.join(WORKTREE_ROOT, filepath)
    exists = os.path.exists(full_path)
    status = "OK" if exists else "MISSING"
    print(f"  [{status}] {description}: {filepath}")
    return exists


def check_file_content(filepath, required_strings, description):
    """Check if file contains required strings"""
    full_path = os.path.join(WORKTREE_ROOT, filepath)

    if not os.path.exists(full_path):
        print(f"  [SKIP] {description} (file not found)")
        return False

    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()

    all_found = True
    for required in required_strings:
        if required not in content:
            print(f"  [MISSING] {description}: '{required}' not found")
            all_found = False

    if all_found:
        print(f"  [OK] {description}")

    return all_found


def verify_deployment():
    """Verify all deployment files"""
    print("=" * 70)
    print("Production Deployment Verification")
    print("=" * 70)

    errors = []

    # Check Docker Compose files
    print("\n[1] Docker Compose Configuration")
    if not check_file_exists("docker-compose.prod.yml", "Production compose file"):
        errors.append("docker-compose.prod.yml missing")

    if not check_file_content(
        "docker-compose.prod.yml",
        ["frontend:", "backend:", "postgres:", "chromadb:", "redis:", "nginx:"],
        "All required services"
    ):
        errors.append("docker-compose.prod.yml missing services")

    # Check Dockerfiles
    print("\n[2] Docker Images")
    if not check_file_exists("Dockerfile", "Backend Dockerfile"):
        errors.append("Backend Dockerfile missing")

    if not check_file_exists("frontend/Dockerfile", "Frontend Dockerfile"):
        errors.append("Frontend Dockerfile missing")

    if not check_file_content(
        "frontend/Dockerfile",
        ["FROM", "AS", "npm run build"],
        "Frontend multi-stage build"
    ):
        errors.append("Frontend Dockerfile not using multi-stage build")

    # Check Nginx configuration
    print("\n[3] Nginx Configuration")
    if not check_file_exists("nginx/nginx.conf", "Nginx config"):
        errors.append("Nginx configuration missing")

    if not check_file_content(
        "nginx/nginx.conf",
        ["upstream frontend", "upstream backend", "location /api"],
        "Nginx proxy configuration"
    ):
        errors.append("Nginx configuration incomplete")

    # Check environment files
    print("\n[4] Environment Configuration")
    if not check_file_exists(".env.production.example", "Production env example"):
        errors.append(".env.production.example missing")

    if not check_file_content(
        ".env.production.example",
        ["OPENAI_API_KEY", "POSTGRES", "REDIS", "CHROMA"],
        "Required environment variables"
    ):
        errors.append(".env.production.example incomplete")

    # Check scripts
    print("\n[5] Deployment Scripts")
    if not check_file_exists("scripts/validate_env.py", "Environment validation"):
        errors.append("validate_env.py missing")

    if not check_file_exists("scripts/deploy.sh", "Deployment script (Linux)"):
        errors.append("deploy.sh missing")

    if not check_file_exists("scripts/deploy.bat", "Deployment script (Windows)"):
        errors.append("deploy.bat missing")

    # Check .dockerignore
    print("\n[6] Docker Ignore Files")
    check_file_exists(".dockerignore", "Backend .dockerignore")
    check_file_exists("frontend/.dockerignore", "Frontend .dockerignore")

    # Check documentation
    print("\n[7] Documentation")
    if not check_file_exists("PRODUCTION_DEPLOYMENT.md", "Deployment guide"):
        errors.append("PRODUCTION_DEPLOYMENT.md missing")

    # Check Next.js configuration
    print("\n[8] Next.js Configuration")
    if not check_file_content(
        "frontend/next.config.ts",
        ["output: \"standalone\""],
        "Next.js standalone output"
    ):
        errors.append("Next.js not configured for standalone output")

    # Summary
    print("\n" + "=" * 70)
    if errors:
        print("VERIFICATION FAILED")
        print("=" * 70)
        print("\nErrors found:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        print("\nPlease fix the errors and run verification again.")
        return False
    else:
        print("VERIFICATION PASSED")
        print("=" * 70)
        print("\nAll production deployment files are in place.")
        print("\nNext steps:")
        print("  1. Copy .env.production.example to .env.production")
        print("  2. Edit .env.production and set your OPENAI_API_KEY")
        print("  3. Run: python scripts/validate_env.py")
        print("  4. Run: ./scripts/deploy.sh (Linux) or scripts\\deploy.bat (Windows)")
        return True


if __name__ == '__main__':
    success = verify_deployment()
    sys.exit(0 if success else 1)
