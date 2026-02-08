#!/usr/bin/env python3
"""
Environment Variable Validation Script for Production Deployment

This script validates that all required environment variables are set
before starting the production deployment.
"""

import os
import sys


def validate_env():
    """Validate required environment variables"""
    required_vars = {
        'OPENAI_API_KEY': 'OpenAI API key for LLM access',
        'POSTGRES_DB': 'PostgreSQL database name',
        'POSTGRES_USER': 'PostgreSQL username',
        'POSTGRES_PASSWORD': 'PostgreSQL password',
    }

    optional_vars = {
        'REDIS_URL': 'Redis connection URL (default: redis://redis:6379/0)',
        'CHROMA_HOST': 'ChromaDB host (default: chromadb)',
        'CHROMA_PORT': 'ChromaDB port (default: 8000)',
        'DATABASE_URL': 'Complete PostgreSQL connection URL',
    }

    errors = []
    warnings = []

    print("=" * 60)
    print("Environment Variable Validation")
    print("=" * 60)

    # Check required variables
    print("\n[Required Variables]")
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if not value:
            errors.append(f"Missing required variable: {var} ({description})")
            print(f"  {var}: MISSING")
        else:
            # Mask sensitive values
            if 'KEY' in var or 'PASSWORD' in var:
                masked_value = value[:8] + '...' if len(value) > 8 else '***'
                print(f"  {var}: {masked_value}")
            else:
                print(f"  {var}: {value}")

    # Check optional variables
    print("\n[Optional Variables]")
    for var, description in optional_vars.items():
        value = os.environ.get(var)
        if not value:
            warnings.append(f"Optional variable not set: {var} ({description})")
            print(f"  {var}: not set (will use default)")
        else:
            if 'URL' in var or 'PASSWORD' in var:
                # Mask URLs and passwords
                masked_value = value[:15] + '...' if len(value) > 15 else value
                print(f"  {var}: {masked_value}")
            else:
                print(f"  {var}: {value}")

    # Additional validation checks
    print("\n[Validation Checks]")

    # Check OPENAI_API_KEY format
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key and not api_key.startswith('sk-'):
        errors.append("OPENAI_API_KEY should start with 'sk-'")
        print("  OPENAI_API_KEY format: INVALID")
    elif api_key:
        print("  OPENAI_API_KEY format: OK")

    # Check password strength
    password = os.environ.get('POSTGRES_PASSWORD')
    if password and len(password) < 8:
        warnings.append("POSTGRES_PASSWORD is less than 8 characters (weak)")
        print("  POSTGRES_PASSWORD strength: WEAK")
    elif password:
        print("  POSTGRES_PASSWORD strength: OK")

    # Print results
    print("\n" + "=" * 60)
    if errors:
        print("VALIDATION FAILED")
        print("=" * 60)
        for error in errors:
            print(f"  ERROR: {error}")
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  WARNING: {warning}")
        sys.exit(1)
    else:
        print("VALIDATION PASSED")
        print("=" * 60)
        if warnings:
            print("\nWarnings:")
            for warning in warnings:
                print(f"  WARNING: {warning}")
        print("\nAll required environment variables are set.")
        print("You can proceed with deployment.")
        sys.exit(0)


if __name__ == '__main__':
    validate_env()
