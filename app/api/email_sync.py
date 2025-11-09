"""
Email Sync API
Allows users to manually trigger email checking for their account
"""

from fastapi import APIRouter, Depends, HTTPException
from app.api.auth import get_current_user
from app.tasks.email_checker import check_emails_and_schedule

router = APIRouter(prefix="/api/email", tags=["email"])


@router.post("/sync")
async def sync_emails(current_user: dict = Depends(get_current_user)):
    """
    Manually trigger email sync for the current user.
    This queues a background Celery task to check their Gmail.

    Requires authentication (user must be logged in).
    """
    user_id = current_user.get('user_id')

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Queue background task for this specific user
    task = check_emails_and_schedule.delay(str(user_id))

    return {
        "status": "success",
        "message": "Email sync started",
        "task_id": task.id,
        "user_id": user_id
    }


@router.get("/sync/status/{task_id}")
async def get_sync_status(task_id: str, current_user: dict = Depends(get_current_user)):
    """
    Check the status of an email sync task.

    Args:
        task_id: The Celery task ID returned from /sync
    """
    from app.celery_app import app as celery_app

    result = celery_app.AsyncResult(task_id)

    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None
    }
