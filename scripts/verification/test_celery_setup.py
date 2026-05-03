"""
Celery Setup Validation Script
P0-T5 검증용 스크립트
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Import 검증"""
    print("=" * 60)
    print("1. Import 검증")
    print("=" * 60)

    try:
        from celery_app import app
        print("✓ celery_app import 성공")
        print(f"  - Broker: {app.conf.broker_url}")
        print(f"  - Backend: {app.conf.result_backend}")
        print(f"  - Timezone: {app.conf.timezone}")
    except Exception as e:
        print(f"✗ celery_app import 실패: {e}")
        return False

    try:
        from tasks.research_task import run_research, health_check
        print("✓ tasks.research_task import 성공")
        print(f"  - run_research task: {run_research.name}")
        print(f"  - health_check task: {health_check.name}")
    except Exception as e:
        print(f"✗ tasks.research_task import 실패: {e}")
        return False

    print()
    return True


def test_celery_config():
    """Celery 설정 검증"""
    print("=" * 60)
    print("2. Celery 설정 검증")
    print("=" * 60)

    try:
        from celery_app import app

        # Check required config
        assert app.conf.task_serializer == 'json', "task_serializer should be json"
        assert 'json' in app.conf.accept_content, "accept_content should include json"
        assert app.conf.result_serializer == 'json', "result_serializer should be json"
        assert app.conf.timezone == 'Asia/Seoul', "timezone should be Asia/Seoul"
        assert app.conf.enable_utc == True, "enable_utc should be True"

        print("✓ 모든 Celery 설정이 올바릅니다")
        print(f"  - Task serializer: {app.conf.task_serializer}")
        print(f"  - Accept content: {app.conf.accept_content}")
        print(f"  - Result serializer: {app.conf.result_serializer}")
        print(f"  - Timezone: {app.conf.timezone}")
        print(f"  - Enable UTC: {app.conf.enable_utc}")
        print(f"  - Task track started: {app.conf.task_track_started}")
        print(f"  - Task time limit: {app.conf.task_time_limit}s")
        print()
        return True
    except AssertionError as e:
        print(f"✗ 설정 검증 실패: {e}")
        print()
        return False
    except Exception as e:
        print(f"✗ 예상치 못한 에러: {e}")
        print()
        return False


def test_registered_tasks():
    """등록된 태스크 검증"""
    print("=" * 60)
    print("3. 등록된 태스크 검증")
    print("=" * 60)

    try:
        from celery_app import app

        # Get registered tasks
        registered = list(app.tasks.keys())

        # Check if our tasks are registered
        expected_tasks = [
            'tasks.run_research',
            'tasks.health_check'
        ]

        print(f"✓ 총 {len(registered)}개의 태스크가 등록되어 있습니다")
        print("\n사용자 정의 태스크:")
        for task_name in expected_tasks:
            if task_name in registered:
                print(f"  ✓ {task_name}")
            else:
                print(f"  ✗ {task_name} (누락)")

        print("\n기본 Celery 태스크:")
        builtin_tasks = [t for t in registered if t.startswith('celery.')]
        for task_name in builtin_tasks[:5]:  # Show first 5
            print(f"  - {task_name}")
        if len(builtin_tasks) > 5:
            print(f"  ... 그 외 {len(builtin_tasks) - 5}개")

        print()
        return all(task in registered for task in expected_tasks)
    except Exception as e:
        print(f"✗ 태스크 검증 실패: {e}")
        print()
        return False


def test_server_integration():
    """Server.py 통합 검증"""
    print("=" * 60)
    print("4. Server.py 통합 검증")
    print("=" * 60)

    try:
        from server import (
            app,
            AsyncResearchRequest,
            AsyncResearchResponse,
            TaskStatusResponse
        )

        print("✓ server.py에서 Celery 관련 import 성공")

        # Check routes
        routes = [route.path for route in app.routes]

        expected_routes = [
            '/api/research/async',
            '/api/task/{task_id}',
            '/api/celery/health'
        ]

        print("\n새로 추가된 엔드포인트:")
        for route in expected_routes:
            if route in routes:
                print(f"  ✓ {route}")
            else:
                print(f"  ✗ {route} (누락)")

        print()
        return all(route in routes for route in expected_routes)
    except Exception as e:
        print(f"✗ Server 통합 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


def test_file_structure():
    """파일 구조 검증"""
    print("=" * 60)
    print("5. 파일 구조 검증")
    print("=" * 60)

    required_files = [
        'celery_app.py',
        'tasks/__init__.py',
        'tasks/research_task.py',
        'scripts/start_worker.sh',
        'scripts/start_worker.bat',
    ]

    all_exist = True
    for file_path in required_files:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"✓ {file_path} ({size} bytes)")
        else:
            print(f"✗ {file_path} (누락)")
            all_exist = False

    print()
    return all_exist


def main():
    """메인 실행 함수"""
    print("\n" + "=" * 60)
    print("  Celery 비동기 작업 처리 인프라 검증 (P0-T5)")
    print("=" * 60 + "\n")

    results = []

    # Run all tests
    results.append(("Import 검증", test_imports()))
    results.append(("Celery 설정 검증", test_celery_config()))
    results.append(("등록된 태스크 검증", test_registered_tasks()))
    results.append(("Server.py 통합 검증", test_server_integration()))
    results.append(("파일 구조 검증", test_file_structure()))

    # Summary
    print("=" * 60)
    print("검증 결과 요약")
    print("=" * 60)

    passed = 0
    failed = 0

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
        if result:
            passed += 1
        else:
            failed += 1

    print()
    print(f"총 {len(results)}개 테스트 중 {passed}개 통과, {failed}개 실패")
    print()

    if failed == 0:
        print("🎉 모든 검증을 통과했습니다!")
        print("\n다음 단계:")
        print("1. Redis 실행: docker compose up -d redis")
        print("2. Celery Worker 실행: python scripts/start_worker.bat (Windows)")
        print("   또는: bash scripts/start_worker.sh (Linux/Mac)")
        print("3. FastAPI 서버 실행: uvicorn server:app --reload")
        print("4. 비동기 API 테스트: POST /api/research/async")
        return 0
    else:
        print("⚠️  일부 검증에 실패했습니다. 위의 오류 메시지를 확인하세요.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
