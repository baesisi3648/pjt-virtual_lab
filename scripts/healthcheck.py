#!/usr/bin/env python3
"""
Virtual Lab Container Health Check Script (Python version)
Usage: python scripts/healthcheck.py
"""

import subprocess
import sys
import time
import requests
from typing import Tuple

# ANSI color codes
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color


def check_container(container_name: str, service_name: str) -> int:
    """
    Check if a Docker container is healthy.
    Returns:
        0: Healthy
        1: Starting
        2: Not running
    """
    try:
        # Check if container is healthy
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={container_name}", "--filter", "health=healthy", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True
        )

        if container_name in result.stdout:
            print(f"{service_name}: {GREEN}HEALTHY{NC}")
            return 0

        # Check if container is running but not healthy yet
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True
        )

        if container_name in result.stdout:
            print(f"{service_name}: {YELLOW}STARTING{NC}")
            return 1
        else:
            print(f"{service_name}: {RED}NOT RUNNING{NC}")
            return 2

    except subprocess.CalledProcessError as e:
        print(f"{service_name}: {RED}ERROR - {str(e)}{NC}")
        return 2


def check_postgres() -> bool:
    """Check PostgreSQL connectivity."""
    try:
        result = subprocess.run(
            ["docker", "exec", "virtual-lab-postgres", "pg_isready", "-U", "postgres"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"PostgreSQL Connection: {GREEN}OK{NC}")
        return True
    except subprocess.CalledProcessError:
        print(f"PostgreSQL Connection: {RED}FAILED{NC}")
        return False


def check_chromadb() -> bool:
    """Check ChromaDB API connectivity."""
    try:
        response = requests.get("http://localhost:8001/api/v1/heartbeat", timeout=5)
        if response.status_code == 200:
            print(f"ChromaDB API: {GREEN}OK{NC}")
            return True
        else:
            print(f"ChromaDB API: {RED}FAILED (Status: {response.status_code}){NC}")
            return False
    except Exception as e:
        print(f"ChromaDB API: {RED}FAILED - {str(e)}{NC}")
        return False


def check_redis() -> bool:
    """Check Redis connectivity."""
    try:
        result = subprocess.run(
            ["docker", "exec", "virtual-lab-redis", "redis-cli", "ping"],
            capture_output=True,
            text=True,
            check=True
        )
        if "PONG" in result.stdout:
            print(f"Redis Connection: {GREEN}OK{NC}")
            return True
        else:
            print(f"Redis Connection: {RED}FAILED{NC}")
            return False
    except subprocess.CalledProcessError:
        print(f"Redis Connection: {RED}FAILED{NC}")
        return False


def main():
    """Main health check function."""
    print("=" * 50)
    print("Virtual Lab Health Check")
    print("=" * 50)
    print()

    print("Checking container status...")
    print()

    # Check container health status
    postgres_status = check_container("virtual-lab-postgres", "PostgreSQL")
    chromadb_status = check_container("virtual-lab-chromadb", "ChromaDB")
    redis_status = check_container("virtual-lab-redis", "Redis")

    print()
    print("Checking service connectivity...")
    print()

    # Check service connectivity only if containers are healthy
    all_healthy = True

    if postgres_status == 0:
        if not check_postgres():
            all_healthy = False
    else:
        all_healthy = False

    if chromadb_status == 0:
        if not check_chromadb():
            all_healthy = False
    else:
        all_healthy = False

    if redis_status == 0:
        if not check_redis():
            all_healthy = False
    else:
        all_healthy = False

    print()
    print("=" * 50)

    if all_healthy:
        print(f"{GREEN}All services are healthy!{NC}")
        sys.exit(0)
    else:
        print(f"{RED}Some services are not ready yet.{NC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
