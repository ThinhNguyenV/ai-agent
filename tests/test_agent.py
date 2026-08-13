import pytest

from app.core.config import Settings
from app.models.schemas import AgentPlan, GenerationRequest
from app.providers.diffusers_local import DiffusersLocalProvider
from app.services.agent import MediaAgent
from app.services.jobs import JobStore
from app.storage.artifacts import ArtifactStore


def test_agent_builds_image_plan(tmp_path):
    settings = Settings(artifact_dir=tmp_path, media_provider="dry_run")
    agent = MediaAgent(settings, JobStore(), ArtifactStore(tmp_path))
    plan = agent.plan(
        GenerationRequest(
            media_type="image",
            prompt="A tutoring center poster",
            style="clean commercial",
            aspect_ratio="1:1",
        )
    )

    assert plan.media_type == "image"
    assert plan.provider == "dry_run"
    assert "clean commercial" in plan.prompt
    assert plan.size == "1024x1024"


def test_agent_builds_video_plan(tmp_path):
    settings = Settings(artifact_dir=tmp_path, media_provider="dry_run")
    agent = MediaAgent(settings, JobStore(), ArtifactStore(tmp_path))
    plan = agent.plan(
        GenerationRequest(
            media_type="video",
            prompt="A product reveal shot",
            seconds=8,
            size="1280x720",
        )
    )

    assert plan.media_type == "video"
    assert plan.seconds == 8
    assert plan.size == "1280x720"
    assert plan.notes


def test_agent_accepts_diffusers_local_provider(tmp_path):
    settings = Settings(artifact_dir=tmp_path, media_provider="diffusers_local")
    agent = MediaAgent(settings, JobStore(), ArtifactStore(tmp_path))
    plan = agent.plan(GenerationRequest(media_type="image", prompt="A realistic coffee product photo"))

    assert plan.provider == "diffusers_local"
    assert settings.local_image_model == "stabilityai/stable-diffusion-xl-base-1.0"
    assert settings.local_video_model in {
        "Wan-AI/Wan2.1-T2V-1.3B-Diffusers",
        "zai-org/CogVideoX-2b",
    }


def test_diffusers_local_rejects_cpu_video_by_default(tmp_path, monkeypatch):
    settings = Settings(artifact_dir=tmp_path, media_provider="diffusers_local")
    provider = DiffusersLocalProvider(settings, ArtifactStore(tmp_path))

    class FakeCuda:
        @staticmethod
        def is_available():
            return False

    class FakeMps:
        @staticmethod
        def is_available():
            return False

    class FakeBackends:
        mps = FakeMps()

    class FakeTorch:
        cuda = FakeCuda()
        backends = FakeBackends()

    monkeypatch.setattr(provider, "_import_torch", lambda: FakeTorch)
    plan = AgentPlan(
        media_type="video",
        provider="diffusers_local",
        prompt="A short cinematic product reveal",
        size="832x480",
        seconds=4,
    )

    with pytest.raises(RuntimeError, match="LOCAL_ALLOW_CPU_VIDEO_GENERATION=true"):
        provider._generate_video("job-cpu-video", plan)
