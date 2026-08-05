import asyncio

from app.core.config import Settings
from app.models.schemas import AgentPlan, Artifact
from app.providers.base import MediaProvider
from app.storage.artifacts import ArtifactStore


class DryRunProvider(MediaProvider):
    name = "dry_run"

    def __init__(self, settings: Settings, artifacts: ArtifactStore) -> None:
        self.settings = settings
        self.artifacts = artifacts

    async def generate(self, job_id: str, plan: AgentPlan) -> list[Artifact]:
        await asyncio.sleep(self.settings.dry_run_delay_seconds)
        path = self.artifacts.save_json(job_id, "dry_run_plan", plan.model_dump())
        return [
            Artifact(
                media_type=plan.media_type,
                path=str(path),
                metadata={"provider": self.name, "message": "dry_run only; no real media was generated"},
            )
        ]
