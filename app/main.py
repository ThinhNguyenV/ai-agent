from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.models.schemas import (
    GenerationAccepted,
    GenerationRequest,
    HealthResponse,
    Job,
    PromptRefineRequest,
    PromptRefineResponse,
)
from app.services.agent import MediaAgent
from app.services.jobs import JobStore
from app.services.prompt_enhancer import PromptEnhancer, PromptEnhancerUnavailable
from app.storage.artifacts import ArtifactStore

jobs = JobStore()
artifacts = ArtifactStore(settings.artifact_dir)
agent = MediaAgent(settings, jobs, artifacts)
prompt_enhancer = PromptEnhancer(settings)
PROJECT_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = PROJECT_DIR / "web"


def create_app() -> FastAPI:
    api = FastAPI(title=settings.app_name, version="0.1.0")
    api.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:8002",
            "http://localhost:8002",
            "http://127.0.0.1:8001",
            "http://localhost:8001",
        ],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    api.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
    api.mount("/artifacts", StaticFiles(directory=settings.artifact_dir), name="artifacts")

    @api.get("/", include_in_schema=False)
    async def web_app() -> FileResponse:
        return FileResponse(WEB_DIR / "index.html")

    @api.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        image_model, video_model = _configured_models()
        return HealthResponse(
            service=settings.app_name,
            provider=settings.media_provider,
            image_model=image_model,
            video_model=video_model,
            prompt_provider=settings.prompt_provider,
            prompt_model=settings.ollama_prompt_model if settings.prompt_provider == "ollama" else None,
        )

    @api.post("/v1/prompts/refine", response_model=PromptRefineResponse)
    async def refine_prompt(payload: PromptRefineRequest) -> PromptRefineResponse:
        try:
            return await prompt_enhancer.refine(payload)
        except PromptEnhancerUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @api.post("/v1/generations", response_model=GenerationAccepted, status_code=202)
    async def create_generation(
        payload: GenerationRequest,
        request: Request,
        background_tasks: BackgroundTasks,
    ) -> GenerationAccepted:
        job = jobs.create(payload)
        if payload.wait:
            completed_job = await agent.run_job(job)
            return GenerationAccepted(
                job_id=completed_job.id,
                status=completed_job.status,
                job_url=str(request.url_for("get_job", job_id=completed_job.id)),
                job=completed_job,
            )

        background_tasks.add_task(agent.run_job, job)
        return GenerationAccepted(
            job_id=job.id,
            status=job.status,
            job_url=str(request.url_for("get_job", job_id=job.id)),
        )

    @api.get("/v1/jobs/{job_id}", response_model=Job, name="get_job")
    async def get_job(job_id: str) -> Job:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job

    return api


def _configured_models() -> tuple[str | None, str | None]:
    if settings.media_provider == "openai":
        return settings.openai_image_model, settings.openai_video_model
    if settings.media_provider == "diffusers_local":
        return settings.local_image_model, settings.local_video_model
    return None, None


app = create_app()
