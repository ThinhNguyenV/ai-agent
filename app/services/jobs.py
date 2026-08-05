from threading import RLock

from app.models.schemas import AgentPlan, Artifact, GenerationRequest, Job, utc_now


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = RLock()

    def create(self, request: GenerationRequest) -> Job:
        job = Job(request=request)
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def mark_running(self, job_id: str) -> Job:
        return self._update(job_id, status="running", error=None)

    def set_plan(self, job_id: str, plan: AgentPlan) -> Job:
        return self._update(job_id, plan=plan)

    def mark_completed(self, job_id: str, artifacts: list[Artifact]) -> Job:
        remote_status = None
        if artifacts:
            raw = artifacts[0].metadata.get("raw", {})
            remote_status = raw.get("status")
        return self._update(job_id, status="completed", artifacts=artifacts, remote_status=remote_status)

    def mark_failed(self, job_id: str, error: str) -> Job:
        return self._update(job_id, status="failed", error=error)

    def _update(self, job_id: str, **changes: object) -> Job:
        with self._lock:
            job = self._jobs[job_id]
            updated = job.model_copy(update={**changes, "updated_at": utc_now()})
            self._jobs[job_id] = updated
            return updated
