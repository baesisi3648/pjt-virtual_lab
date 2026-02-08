"""
Tests for Production Deployment (P4-T5)

Requirements:
1. docker-compose.prod.yml exists
2. Nginx configuration exists
3. Environment variable validation script exists
4. Health checks work for all services
5. Frontend is accessible via nginx
6. Backend API is accessible via nginx
"""

import os
import pytest
import subprocess
import time
import httpx


WORKTREE_ROOT = "C:/Users/배성우/Desktop/pjt-virtual_lab/worktree/phase-4-nextjs"


def test_docker_compose_prod_exists():
    """Test that docker-compose.prod.yml file exists"""
    compose_file = os.path.join(WORKTREE_ROOT, "docker-compose.prod.yml")
    assert os.path.exists(compose_file), "docker-compose.prod.yml should exist"


def test_nginx_config_exists():
    """Test that nginx configuration file exists"""
    nginx_config = os.path.join(WORKTREE_ROOT, "nginx", "nginx.conf")
    assert os.path.exists(nginx_config), "nginx/nginx.conf should exist"


def test_env_validation_script_exists():
    """Test that environment validation script exists"""
    validation_script = os.path.join(WORKTREE_ROOT, "scripts", "validate_env.py")
    assert os.path.exists(validation_script), "scripts/validate_env.py should exist"


def test_docker_compose_prod_structure():
    """Test that docker-compose.prod.yml has required services"""
    compose_file = os.path.join(WORKTREE_ROOT, "docker-compose.prod.yml")

    with open(compose_file, 'r') as f:
        content = f.read()

    # Check for required services
    assert "frontend:" in content, "Should have frontend service"
    assert "backend:" in content, "Should have backend service"
    assert "postgres:" in content, "Should have postgres service"
    assert "chromadb:" in content, "Should have chromadb service"
    assert "redis:" in content, "Should have redis service"
    assert "nginx:" in content, "Should have nginx service"

    # Check for health checks
    assert "healthcheck:" in content, "Should have health checks"

    # Check for networks
    assert "networks:" in content, "Should have network configuration"


def test_nginx_config_structure():
    """Test that nginx.conf has required configuration"""
    nginx_config = os.path.join(WORKTREE_ROOT, "nginx", "nginx.conf")

    with open(nginx_config, 'r') as f:
        content = f.read()

    # Check for upstream configurations
    assert "upstream frontend" in content or "proxy_pass" in content, "Should proxy to frontend"
    assert "upstream backend" in content or "location /api" in content, "Should proxy to backend API"

    # Check for basic nginx configuration
    assert "server {" in content, "Should have server block"
    assert "listen" in content, "Should have listen directive"


def test_env_validation_script_structure():
    """Test that validate_env.py has required validation logic"""
    validation_script = os.path.join(WORKTREE_ROOT, "scripts", "validate_env.py")

    with open(validation_script, 'r') as f:
        content = f.read()

    # Check for required environment variables
    assert "OPENAI_API_KEY" in content, "Should validate OPENAI_API_KEY"
    assert "DATABASE_URL" in content or "POSTGRES" in content, "Should validate database configuration"

    # Check for validation logic
    assert "def" in content, "Should have validation functions"
    assert "raise" in content or "assert" in content or "exit" in content, "Should have error handling"


def test_frontend_dockerfile_exists():
    """Test that frontend Dockerfile exists for production build"""
    frontend_dockerfile = os.path.join(WORKTREE_ROOT, "frontend", "Dockerfile")
    assert os.path.exists(frontend_dockerfile), "frontend/Dockerfile should exist"


def test_backend_dockerfile_exists():
    """Test that backend Dockerfile exists"""
    backend_dockerfile = os.path.join(WORKTREE_ROOT, "Dockerfile")
    assert os.path.exists(backend_dockerfile), "Backend Dockerfile should exist"


def test_frontend_dockerfile_multistage():
    """Test that frontend Dockerfile uses multi-stage build"""
    frontend_dockerfile = os.path.join(WORKTREE_ROOT, "frontend", "Dockerfile")

    with open(frontend_dockerfile, 'r') as f:
        content = f.read()

    # Check for multi-stage build
    assert "FROM" in content, "Should have FROM directive"
    assert "AS" in content or content.count("FROM") > 1, "Should use multi-stage build"
    assert "npm run build" in content or "next build" in content, "Should build Next.js app"


def test_production_env_example_exists():
    """Test that .env.production.example exists"""
    env_example = os.path.join(WORKTREE_ROOT, ".env.production.example")
    assert os.path.exists(env_example), ".env.production.example should exist"


def test_production_env_example_structure():
    """Test that .env.production.example has required variables"""
    env_example = os.path.join(WORKTREE_ROOT, ".env.production.example")

    with open(env_example, 'r') as f:
        content = f.read()

    # Check for required environment variables
    assert "OPENAI_API_KEY" in content, "Should have OPENAI_API_KEY"
    assert "DATABASE_URL" in content or "POSTGRES" in content, "Should have database configuration"
    assert "REDIS_URL" in content or "REDIS" in content, "Should have Redis configuration"
    assert "CHROMA" in content, "Should have ChromaDB configuration"
