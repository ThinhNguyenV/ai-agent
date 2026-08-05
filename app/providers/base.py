from abc import ABC, abstractmethod

from app.models.schemas import AgentPlan, Artifact


class MediaProvider(ABC):
    name: str

    @abstractmethod
    async def generate(self, job_id: str, plan: AgentPlan) -> list[Artifact]:
        """Generate media for an agent plan and return produced artifacts."""
