from app.core.config import Settings
from app.providers.base import MediaProvider
from app.providers.diffusers_local import DiffusersLocalProvider
from app.providers.dry_run import DryRunProvider
from app.providers.openai import OpenAIProvider
from app.storage.artifacts import ArtifactStore


def build_provider(settings: Settings, artifacts: ArtifactStore, override: str | None = None) -> MediaProvider:
    provider_name = override or settings.media_provider
    if provider_name == "dry_run":
        return DryRunProvider(settings, artifacts)
    if provider_name == "openai":
        return OpenAIProvider(settings, artifacts)
    if provider_name == "diffusers_local":
        return DiffusersLocalProvider(settings, artifacts)
    raise ValueError(f"Unsupported media provider: {provider_name}")
