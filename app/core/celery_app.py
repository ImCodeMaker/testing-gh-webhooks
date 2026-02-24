from celery import Celery
from app.core.settings import settings

# Initialize the Celery application
# Use Redis as both the broker (message transport) and backend (result storage)
celery = Celery(
    "chief_ai_reviewer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    # Automatically discover tasks in the app.tasks package
    include=['app.tasks.review']
)


# 1. Serialization
celery.conf.task_serializer = "json"
celery.conf.result_serializer = "json"
celery.conf.accept_content = ["json"]

# 2. Concurrency & Ordering
# Ensure workers process ONE review at a time to prevent hammering AI APIs
# worker_prefetch_multiplier=1 guarantees true FIFO ordering because workers
# won't buffer tasks locally—they only take one when they are completely free.
celery.conf.worker_concurrency = 1
celery.conf.worker_prefetch_multiplier = 1

# 3. Reliability & State Tracking
# Only acknowledge a task as 'done' after it has successfully finished returning or raised.
# If the worker crashes mid-review, the task is sent back to Redis and re-assigned.
celery.conf.task_acks_late = True
# Track when tasks start so we can monitor them in the Flower UI
celery.conf.task_track_started = True

# 4. Expirations & Timeouts
# Hard kill tasks after 6 minutes to free up the worker
celery.conf.task_time_limit = 360
# Raise SoftTimeLimitExceeded after 5 minutes so the task can clean up or catch it gracefully
celery.conf.task_soft_time_limit = 300
# Only store results in Redis for 1 hour to prevent memory bloat
celery.conf.result_expires = 3600
