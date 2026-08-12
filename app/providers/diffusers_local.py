import asyncio
import threading
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.models.schemas import AgentPlan, Artifact
from app.providers.base import MediaProvider
from app.storage.artifacts import ArtifactStore

_PIPELINE_CACHE: dict[tuple[str, str, str, bool], Any] = {}
_PIPELINE_LOCK = threading.RLock()


class DiffusersLocalProvider(MediaProvider):
    name = "diffusers_local"

    def __init__(self, settings: Settings, artifacts: ArtifactStore) -> None:
        self.settings = settings
        self.artifacts = artifacts

    async def generate(self, job_id: str, plan: AgentPlan) -> list[Artifact]:
        return await asyncio.to_thread(self._generate_sync, job_id, plan)

    def _generate_sync(self, job_id: str, plan: AgentPlan) -> list[Artifact]:
        if plan.reference_image_url:
            raise ValueError("diffusers_local currently supports text-to-image and text-to-video only")
        if plan.media_type == "image":
            return [self._generate_image(job_id, plan)]
        return [self._generate_video(job_id, plan)]

    def _generate_image(self, job_id: str, plan: AgentPlan) -> Artifact:
        torch = self._import_torch()
        model_id = self.settings.local_image_model
        pipe, device = self._pipeline("image", model_id, torch)
        width, height = self._parse_size(plan.size)
        generator = self._generator(torch, device)

        kwargs: dict[str, Any] = {
            "prompt": plan.prompt,
            "width": width,
            "height": height,
            "num_inference_steps": self.settings.local_image_steps,
            "guidance_scale": self.settings.local_image_guidance_scale,
        }
        if generator is not None:
            kwargs["generator"] = generator

        image = pipe(**kwargs).images[0]
        output_path = self._output_path(job_id, "output.png")
        image.save(output_path)
        return Artifact(
            media_type="image",
            path=str(output_path),
            metadata={
                "provider": self.name,
                "model": model_id,
                "pipeline": pipe.__class__.__name__,
                "width": width,
                "height": height,
                "steps": self.settings.local_image_steps,
            },
        )

    def _generate_video(self, job_id: str, plan: AgentPlan) -> Artifact:
        torch = self._import_torch()
        model_id = self.settings.local_video_model
        pipe, device = self._pipeline("video", model_id, torch)
        width, height = self._parse_size(plan.size)
        num_frames = self._num_frames(plan)
        generator = self._generator(torch, device)

        kwargs: dict[str, Any] = {
            "prompt": plan.prompt,
            "height": height,
            "width": width,
            "num_frames": num_frames,
            "num_inference_steps": self.settings.local_video_steps,
            "guidance_scale": self.settings.local_video_guidance_scale,
        }
        if generator is not None:
            kwargs["generator"] = generator
        if "wan" in model_id.lower():
            kwargs["negative_prompt"] = plan.negative_prompt or self.settings.local_video_negative_prompt

        frames = pipe(**kwargs).frames[0]
        output_path = self._output_path(job_id, "output.mp4")
        self._export_to_video(frames, output_path, self.settings.local_video_fps)
        return Artifact(
            media_type="video",
            path=str(output_path),
            metadata={
                "provider": self.name,
                "model": model_id,
                "pipeline": pipe.__class__.__name__,
                "width": width,
                "height": height,
                "frames": num_frames,
                "fps": self.settings.local_video_fps,
                "steps": self.settings.local_video_steps,
            },
        )

    def _pipeline(self, media_type: str, model_id: str, torch: Any) -> tuple[Any, str]:
        device = self._device(torch)
        dtype = self._dtype(torch, model_id, device)
        cache_key = (media_type, model_id, str(dtype), self.settings.local_enable_cpu_offload)

        with _PIPELINE_LOCK:
            if cache_key not in _PIPELINE_CACHE:
                pipe = self._load_pipeline(media_type, model_id, torch, dtype)
                if self.settings.local_enable_cpu_offload and device == "cuda":
                    pipe.enable_model_cpu_offload()
                else:
                    pipe.to(device)
                if hasattr(pipe, "enable_vae_slicing"):
                    pipe.enable_vae_slicing()
                if hasattr(pipe, "enable_vae_tiling"):
                    pipe.enable_vae_tiling()
                _PIPELINE_CACHE[cache_key] = pipe
            return _PIPELINE_CACHE[cache_key], device

    def _load_pipeline(self, media_type: str, model_id: str, torch: Any, dtype: Any) -> Any:
        try:
            normalized = model_id.lower()
            if media_type == "image":
                if "flux" in normalized:
                    from diffusers.pipelines.flux.pipeline_flux import FluxPipeline

                    return FluxPipeline.from_pretrained(model_id, torch_dtype=dtype)
                if "stable-diffusion-xl" in normalized or "sdxl" in normalized:
                    from diffusers.pipelines.stable_diffusion_xl.pipeline_stable_diffusion_xl import (
                        StableDiffusionXLPipeline,
                    )

                    return StableDiffusionXLPipeline.from_pretrained(
                        model_id,
                        torch_dtype=dtype,
                        use_safetensors=True,
                    )
                if "stable-diffusion-v1" in normalized or "stable-diffusion-v1-5" in normalized:
                    from diffusers.pipelines.stable_diffusion.pipeline_stable_diffusion import (
                        StableDiffusionPipeline,
                    )

                    return StableDiffusionPipeline.from_pretrained(
                        model_id,
                        torch_dtype=dtype,
                        use_safetensors=True,
                    )
                from diffusers.pipelines.pipeline_utils import DiffusionPipeline

                return DiffusionPipeline.from_pretrained(model_id, torch_dtype=dtype)

            if "wan" in normalized:
                from diffusers.models.autoencoders.autoencoder_kl_wan import AutoencoderKLWan
                from diffusers.pipelines.wan.pipeline_wan import WanPipeline

                vae = AutoencoderKLWan.from_pretrained(model_id, subfolder="vae", torch_dtype=torch.float32)
                return WanPipeline.from_pretrained(model_id, vae=vae, torch_dtype=dtype)

            if "cogvideox" in normalized:
                from diffusers.pipelines.cogvideo.pipeline_cogvideox import CogVideoXPipeline

                return CogVideoXPipeline.from_pretrained(model_id, torch_dtype=dtype)
        except ImportError as exc:
            raise RuntimeError(
                "Install local media dependencies first: pip install -e \".[local]\". "
                "For NVIDIA GPUs, install the CUDA build of torch that matches your driver."
            ) from exc

        raise ValueError(f"Unsupported diffusers_local model: {model_id}")

    def _import_torch(self) -> Any:
        try:
            import torch

            return torch
        except ImportError as exc:
            raise RuntimeError(
                "Install local media dependencies first: pip install -e \".[local]\". "
                "For NVIDIA GPUs, install the CUDA build of torch that matches your driver."
            ) from exc

    def _export_to_video(self, frames: Any, output_path: Path, fps: int) -> None:
        try:
            from diffusers.utils.export_utils import export_to_video
        except ImportError as exc:
            raise RuntimeError("diffusers is required to export generated videos") from exc
        export_to_video(frames, str(output_path), fps=fps)

    def _device(self, torch: Any) -> str:
        if self.settings.local_device != "auto":
            return self.settings.local_device
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def _dtype(self, torch: Any, model_id: str, device: str) -> Any:
        if self.settings.local_torch_dtype != "auto":
            return getattr(torch, self.settings.local_torch_dtype)
        if device == "cpu" or device == "mps":
            return torch.float32
        normalized = model_id.lower()
        if "cogvideox-2b" in normalized or "stable-diffusion" in normalized or "sdxl" in normalized:
            return torch.float16
        return torch.bfloat16

    def _generator(self, torch: Any, device: str) -> Any | None:
        if self.settings.local_seed is None:
            return None
        generator_device = device if device in {"cuda", "cpu"} else "cpu"
        return torch.Generator(device=generator_device).manual_seed(self.settings.local_seed)

    def _num_frames(self, plan: AgentPlan) -> int:
        target = plan.seconds * self.settings.local_video_fps if plan.seconds else self.settings.local_video_num_frames
        target = max(1, target)
        if (target - 1) % 4 == 0:
            return target
        lower = ((target - 1) // 4) * 4 + 1
        upper = lower + 4
        if lower < 1:
            return upper
        return lower if target - lower <= upper - target else upper

    def _parse_size(self, size: str) -> tuple[int, int]:
        try:
            width, height = size.lower().split("x", 1)
            return int(width), int(height)
        except ValueError as exc:
            raise ValueError(f"Invalid size '{size}'. Expected WIDTHxHEIGHT, for example 832x480.") from exc

    def _output_path(self, job_id: str, filename: str) -> Path:
        output_path = self.artifacts.root / job_id / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path
