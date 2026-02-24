import asyncio
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from app.core.logger import logger
from app.services.github.strategies.pull_request import PullRequestStrategy

@shared_task(
    name="app.tasks.review.process_pull_request_review",
    bind=True,
    # Standard exponential backoff parameters on Exception
    autoretry_for=(Exception,),
    max_retries=3,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    # Override time limits defined in CeleryApp if needed
    soft_time_limit=300,
    time_limit=360
)
def process_pull_request_review(self, payload: dict) -> None:
    """
    Synchronous Celery task that processes a GitHub pull request event.
    It encapsulates the existing async PullRequestStrategy using an event loop.
    Enqueued by API endpoints explicitly when needed.
    """
    pr_number = payload.get("pull_request", {}).get("number", "Unknown")
    repo = payload.get("repository", {}).get("full_name", "Unknown Repo")
    action = payload.get("action", "unknown action")
    
    logger.info(f"Celery Task [{self.request.id}] received PR #{pr_number} action '{action}' on {repo}")
    
    try:
        # Re-use the existing architectural approach, just wrap the async execute
        # method in a fresh sync entry point event loop
        strategy = PullRequestStrategy()
        
        logger.info(f"Celery Task [{self.request.id}] starting async execution loop...")
        asyncio.run(strategy.execute(payload))
        logger.info(f"Celery Task [{self.request.id}] successfully finished PR #{pr_number}.")

    except SoftTimeLimitExceeded as timeout_exc:
        # A soft limit indicates the 5-minute threshold has triggered. Log aggressively
        logger.warning(
            f"Celery Task [{self.request.id}] gracefully exiting due to SoftTimeLimitExceeded! "
            f"Review for PR #{pr_number} took longer than 300 seconds."
        )
        raise timeout_exc
        
    except Exception as e:
        logger.error(f"Celery Task [{self.request.id}] failed processing PR #{pr_number}: {str(e)}", exc_info=True)
        # Reraising the exception kicks off the `autoretry_for` logic automatically
        raise e
