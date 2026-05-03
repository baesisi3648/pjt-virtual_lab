"""
Research Task - Long-running background job
"""
from celery import Task
from celery_app import app
from typing import Dict, Any


@app.task(bind=True, name='tasks.run_research')
def run_research(self: Task, user_query: str) -> Dict[str, Any]:
    """
    Execute research workflow in background

    Args:
        user_query: User's research question

    Returns:
        Dict with status, report, and session_id

    Raises:
        Exception: On workflow execution failure
    """
    try:
        # Update task state to PROGRESS
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 3, 'status': 'Initializing workflow...'}
        )

        # Import here to avoid circular dependency
        from workflow.graph import create_graph

        # Create and execute workflow
        self.update_state(
            state='PROGRESS',
            meta={'current': 1, 'total': 3, 'status': 'Creating graph...'}
        )
        graph = create_graph()

        self.update_state(
            state='PROGRESS',
            meta={'current': 2, 'total': 3, 'status': 'Running research...'}
        )
        result = graph.invoke({"query": user_query})

        # Extract results
        self.update_state(
            state='PROGRESS',
            meta={'current': 3, 'total': 3, 'status': 'Finalizing results...'}
        )

        return {
            "status": "completed",
            "report": result.get("final_report"),
            "session_id": result.get("session_id"),
            "query": user_query
        }

    except Exception as e:
        # Update state to FAILURE with error details
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(e),
                'error_type': type(e).__name__,
                'query': user_query
            }
        )
        raise


@app.task(name='tasks.health_check')
def health_check() -> Dict[str, str]:
    """
    Simple task to verify Celery worker is alive

    Returns:
        Dict with status message
    """
    return {"status": "ok", "message": "Celery worker is running"}
