"""Job Manager — Canonical background execution engine for all long-running operations.

Every long-running operation becomes a Job tracked by this manager.
Provides: create, list, get, cancel, pause, resume, retry.
"""
import threading, uuid, time, json, logging
from datetime import datetime, timezone
from typing import Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class Job:
    """A single background operation tracked by the Job Manager."""

    def __init__(self, title: str, category: str, total_steps: int = 100):
        self.id: str = f"job_{uuid.uuid4().hex[:12]}"
        self.title: str = title
        self.category: str = category  # upload, import, ocr, ai, export, etc.
        self.status: JobStatus = JobStatus.PENDING
        self.created_at: str = datetime.now(timezone.utc).isoformat()
        self.updated_at: str = self.created_at
        self.completed_at: Optional[str] = None
        self.current_stage: str = "Initializing"
        self.percentage: int = 0
        self.estimated_remaining: Optional[int] = None  # seconds
        self.priority: int = 0
        self.result: Optional[dict] = None
        self.failure_reason: Optional[str] = None
        self._cancel_flag: bool = False
        self._pause_flag: bool = False
        self._thread: Optional[threading.Thread] = None
        self._fn: Optional[Callable] = None
        self._fn_args: tuple = ()
        self._fn_kwargs: dict = {}
        self.total_steps: int = total_steps
        self.current_step: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "current_stage": self.current_stage,
            "percentage": self.percentage,
            "estimated_remaining": self.estimated_remaining,
            "priority": self.priority,
            "result": self.result,
            "failure_reason": self.failure_reason,
            "total_steps": self.total_steps,
            "current_step": self.current_step,
        }

    def update(self, stage: str = None, step: int = None, total: int = None,
               status: JobStatus = None, result: dict = None, error: str = None):
        if stage:
            self.current_stage = stage
        if step is not None:
            self.current_step = step
        if total is not None:
            self.total_steps = total
        if self.total_steps > 0:
            self.percentage = min(100, int((self.current_step / self.total_steps) * 100))
        if status:
            self.status = status
            if status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
                self.completed_at = datetime.now(timezone.utc).isoformat()
        if result:
            self.result = result
        if error:
            self.failure_reason = error
        self.updated_at = datetime.now(timezone.utc).isoformat()

    @property
    def is_cancelled(self) -> bool:
        return self._cancel_flag

    @property
    def is_paused(self) -> bool:
        return self._pause_flag

    def cancel(self):
        self._cancel_flag = True
        self.update(status=JobStatus.CANCELLED)

    def pause(self):
        self._pause_flag = True
        self.update(status=JobStatus.PAUSED)

    def resume(self):
        self._pause_flag = False
        self.update(status=JobStatus.RUNNING)

    def run_async(self, fn: Callable, *args, **kwargs):
        """Execute a function in a background thread as this job."""
        self._fn = fn
        self._fn_args = args
        self._fn_kwargs = kwargs
        self._thread = threading.Thread(target=self._run_wrapper, daemon=True)
        self._thread.start()

    def _run_wrapper(self):
        self.update(status=JobStatus.RUNNING)
        try:
            result = self._fn(self, *self._fn_args, **self._fn_kwargs)
            if not self._cancel_flag:
                self.update(status=JobStatus.COMPLETED, result=result)
        except Exception as e:
            logger.exception(f"Job {self.id} failed: {e}")
            self.update(status=JobStatus.FAILED, error=str(e))


# ── In-memory job store (thread-safe) ──
_jobs: dict[str, Job] = {}
_jobs_lock = threading.Lock()


def create_job(title: str, category: str, total_steps: int = 100) -> Job:
    job = Job(title, category, total_steps)
    with _jobs_lock:
        _jobs[job.id] = job
    logger.info(f"Job created: {job.id} — {title}")
    return job


def get_job(job_id: str) -> Optional[Job]:
    with _jobs_lock:
        return _jobs.get(job_id)


def list_jobs(category: str = None, status: str = None, limit: int = 50) -> list[dict]:
    with _jobs_lock:
        result = list(_jobs.values())
    if category:
        result = [j for j in result if j.category == category]
    if status:
        result = [j for j in result if j.status.value == status]
    result.sort(key=lambda j: j.created_at, reverse=True)
    return [j.to_dict() for j in result[:limit]]


def cancel_job(job_id: str) -> bool:
    job = get_job(job_id)
    if not job:
        return False
    job.cancel()
    return True


def pause_job(job_id: str) -> bool:
    job = get_job(job_id)
    if not job:
        return False
    job.pause()
    return True


def resume_job(job_id: str) -> bool:
    job = get_job(job_id)
    if not job:
        return False
    job.resume()
    return True


def retry_job(job_id: str) -> Optional[Job]:
    job = get_job(job_id)
    if not job or not job._fn:
        return None
    new_job = create_job(job.title, job.category, job.total_steps)
    new_job.run_async(job._fn, *job._fn_args, **job._fn_kwargs)
    return new_job


def count_active_jobs() -> int:
    with _jobs_lock:
        return sum(1 for j in _jobs.values() if j.status in (JobStatus.RUNNING, JobStatus.PAUSED, JobStatus.PENDING))