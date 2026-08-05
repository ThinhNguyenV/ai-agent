from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Media Agent"
    media_provider: str = Field(default="diffusers_local", pattern="^(dry_run|openai|diffusers_local)$")
    prompt_provider: str = Field(default="ollama", pattern="^(template|ollama)$")
    artifact_dir: Path = Path("artifacts")

    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_image_model: str = "gpt-image-1.5"
    openai_video_model: str = "sora-2"

    ollama_base_url: str = "http://localhost:11434/api"
    ollama_prompt_model: str = "qwen2.5:3b"
    ollama_timeout_seconds: float = 120.0
    ollama_num_predict: int = 700
    ollama_temperature: float = 0.45

    local_image_model: str = "stabilityai/stable-diffusion-xl-base-1.0"
    local_video_model: str = "Wan-AI/Wan2.1-T2V-1.3B-Diffusers"
    local_device: str = "auto"
    local_torch_dtype: str = "auto"
    local_enable_cpu_offload: bool = True
    local_seed: int | None = None
    local_image_steps: int = 4
    local_image_guidance_scale: float = 0.0
    local_video_steps: int = 30
    local_video_guidance_scale: float = 5.0
    local_video_num_frames: int = 81
    local_video_fps: int = 15
    local_video_negative_prompt: str = (
        "Bright tones, overexposed, static, blurred details, subtitles, worst quality, "
        "low quality, jpeg artifacts, ugly, incomplete, deformed, disfigured, messy background"
    )

    image_size: str = "1024x1024"
    image_quality: str = "medium"
    video_seconds: int = 4
    video_size: str = "832x480"
    video_poll_interval_seconds: float = 3.0
    video_poll_timeout_seconds: float = 60.0

    dry_run_delay_seconds: float = 0.2


settings = Settings()