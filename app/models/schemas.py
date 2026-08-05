from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl, model_validator

MediaType = Literal["image", "video"]
ProviderName = Literal["dry_run", "openai", "diffusers_local"]
PromptProviderName = Literal["template", "ollama"]
JobStatus = Literal["queued", "running", "completed", "failed"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class GenerationRequest(BaseModel):
    media_type: MediaType
    prompt: str = Field(min_length=3, max_length=5000)
    style: str | None = Field(default=None, max_length=500)
    negative_prompt: str | None = Field(default=None, max_length=1000)
    aspect_ratio: str | None = Field(default=None, examples=["1:1", "16:9", "9:16"])
    size: str | None = Field(default=None, examples=["1024x1024", "832x480", "720x480"])
    quality: str | None = Field(default=None, examples=["low", "medium", "high"])
    seconds: int | None = Field(default=None, ge=1, le=30)
    reference_image_url: HttpUrl | None = None
    provider: ProviderName | None = None
    enhance_prompt: bool = False
    prompt_provider: PromptProviderName | None = None
    prompt_model: str | None = Field(default=None, max_length=200)
    wait: bool = False

    @model_validator(mode="after")
    def validate_video_fields(self) -> "GenerationRequest":
        if self.media_type == "image" and self.seconds is not None:
            raise ValueError("seconds chi ap dung cho video")
        return self


class PromptRefineRequest(BaseModel):
    media_type: MediaType
    prompt: str = Field(min_length=3, max_length=5000)
    style: str | None = Field(default=None, max_length=500)
    negative_prompt: str | None = Field(default=None, max_length=1000)
    aspect_ratio: str | None = Field(default=None, examples=["1:1", "16:9", "9:16"])
    provider: PromptProviderName | None = None
    model: str | None = Field(default=None, max_length=200)


class PromptRefineResponse(BaseModel):
    original_prompt: str
    refined_prompt: str
    negative_prompt: str | None = None
    provider: str
    model: str | None = None
    notes: list[str] = Field(default_factory=list)


class AgentPlan(BaseModel):
    media_type: MediaType
    provider: str
    prompt: str
    negative_prompt: str | None = None
    size: str
    quality: str | None = None
    seconds: int | None = None
    reference_image_url: str | None = None
    notes: list[str] = Field(default_factory=list)


class Artifact(BaseModel):
    media_type: MediaType
    path: str | None = None
    url: str | None = None
    remote_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    status: JobStatus = "queued"
    request: GenerationRequest
    plan: AgentPlan | None = None
    artifacts: list[Artifact] = Field(default_factory=list)
    remote_status: str | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class GenerationAccepted(BaseModel):
    job_id: str
    status: JobStatus
    job_url: str
    job: Job | None = None


class HealthResponse(BaseModel):
    ok: bool = True
    service: str
    provider: str
    image_model: str | None = None
    video_model: str | None = None
    prompt_provider: str | None = None
    prompt_model: str | None = None