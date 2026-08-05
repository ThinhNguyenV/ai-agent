from app.core.config import Settings
from app.models.schemas import AgentPlan, GenerationRequest, Job, PromptRefineRequest
from app.providers import build_provider
from app.services.jobs import JobStore
from app.services.prompt_enhancer import PromptEnhancer, PromptEnhancerUnavailable
from app.storage.artifacts import ArtifactStore


class MediaAgent:
    def __init__(self, settings: Settings, jobs: JobStore, artifacts: ArtifactStore) -> None:
        self.settings = settings
        self.jobs = jobs
        self.artifacts = artifacts
        self.prompt_enhancer = PromptEnhancer(settings)

    def plan(
        self,
        request: GenerationRequest,
        refined_prompt: str | None = None,
        extra_notes: list[str] | None = None,
    ) -> AgentPlan:
        size = request.size or self._default_size(request)
        prompt_parts = [refined_prompt or request.prompt.strip()]

        if not refined_prompt:
            if request.style:
                prompt_parts.append(f"Style: {request.style.strip()}.")
            if request.aspect_ratio:
                prompt_parts.append(f"Aspect ratio: {request.aspect_ratio.strip()}.")
            prompt_parts.append(
                "Make the result production-ready, coherent, detailed, and faithful to the user's intent."
            )

        notes = extra_notes or []
        if request.media_type == "video":
            notes.append("Video prompts should describe camera motion, subject action, scene continuity, and mood.")
        if refined_prompt:
            notes.append("Prompt was enhanced before media generation.")

        return AgentPlan(
            media_type=request.media_type,
            provider=request.provider or self.settings.media_provider,
            prompt=" ".join(prompt_parts),
            negative_prompt=request.negative_prompt,
            size=size,
            quality=request.quality or (self.settings.image_quality if request.media_type == "image" else None),
            seconds=request.seconds or (self.settings.video_seconds if request.media_type == "video" else None),
            reference_image_url=str(request.reference_image_url) if request.reference_image_url else None,
            notes=notes,
        )

    async def run_job(self, job: Job) -> Job:
        self.jobs.mark_running(job.id)
        try:
            refined_prompt = None
            notes = []
            if job.request.enhance_prompt:
                refine_request = PromptRefineRequest(
                    media_type=job.request.media_type,
                    prompt=job.request.prompt,
                    style=job.request.style,
                    negative_prompt=job.request.negative_prompt,
                    aspect_ratio=job.request.aspect_ratio,
                    provider=job.request.prompt_provider,
                    model=job.request.prompt_model,
                )
                try:
                    refined = await self.prompt_enhancer.refine(refine_request)
                except PromptEnhancerUnavailable as exc:
                    refined = self.prompt_enhancer.refine_with_template(
                        refine_request,
                        note=f"Ollama unavailable; used template fallback. {exc}",
                    )
                refined_prompt = refined.refined_prompt
                notes.extend(refined.notes)

            plan = self.plan(job.request, refined_prompt=refined_prompt, extra_notes=notes)
            self.jobs.set_plan(job.id, plan)
            provider = build_provider(self.settings, self.artifacts, plan.provider)
            artifacts = await provider.generate(job.id, plan)
            completed = self.jobs.mark_completed(job.id, artifacts)
            return completed
        except Exception as exc:
            return self.jobs.mark_failed(job.id, str(exc))

    def _default_size(self, request: GenerationRequest) -> str:
        if request.media_type == "image":
            return self.settings.image_size
        return self.settings.video_size