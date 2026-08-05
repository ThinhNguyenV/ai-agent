import asyncio
from typing import Any

import httpx

from app.core.config import Settings
from app.models.schemas import AgentPlan, Artifact
from app.providers.base import MediaProvider
from app.storage.artifacts import ArtifactStore


class OpenAIProvider(MediaProvider):
    name = "openai"
    video_seconds = {4, 8, 12}
    video_sizes = {"720x1280", "1280x720", "1024x1792", "1792x1024"}

    def __init__(self, settings: Settings, artifacts: ArtifactStore) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when MEDIA_PROVIDER=openai")
        self.settings = settings
        self.artifacts = artifacts

    async def generate(self, job_id: str, plan: AgentPlan) -> list[Artifact]:
        if plan.media_type == "image":
            return await self._generate_image(job_id, plan)
        return await self._generate_video(job_id, plan)

    async def _generate_image(self, job_id: str, plan: AgentPlan) -> list[Artifact]:
        payload: dict[str, Any] = {
            "model": self.settings.openai_image_model,
            "prompt": plan.prompt,
            "size": plan.size,
            "n": 1,
        }
        if plan.quality:
            payload["quality"] = plan.quality

        data = await self._request_json("POST", "/images/generations", json=payload)
        first = (data.get("data") or [{}])[0]
        metadata = {"provider": self.name, "model": payload["model"], "raw": data}

        if b64_json := first.get("b64_json"):
            path = self.artifacts.save_base64(job_id, b64_json, "png")
            return [Artifact(media_type="image", path=str(path), metadata=metadata)]

        if url := first.get("url"):
            return [Artifact(media_type="image", url=url, metadata=metadata)]

        path = self.artifacts.save_json(job_id, "openai_image_response", data)
        return [Artifact(media_type="image", path=str(path), metadata=metadata)]

    async def _generate_video(self, job_id: str, plan: AgentPlan) -> list[Artifact]:
        seconds = plan.seconds or self.settings.video_seconds
        if seconds not in self.video_seconds:
            raise ValueError("OpenAI video seconds must be one of: 4, 8, 12")
        if plan.size not in self.video_sizes:
            raise ValueError("OpenAI video size must be one of: 720x1280, 1280x720, 1024x1792, 1792x1024")

        payload: dict[str, Any] = {
            "model": self.settings.openai_video_model,
            "prompt": plan.prompt,
            "seconds": str(seconds),
            "size": plan.size,
        }
        if plan.reference_image_url:
            payload["input_reference"] = {"image_url": plan.reference_image_url}

        video = await self._request_json("POST", "/videos", json=payload)
        video_id = video["id"]
        final_video = await self._wait_for_video(video_id)
        metadata = {"provider": self.name, "model": payload["model"], "raw": final_video}

        if final_video.get("status") == "completed":
            content = await self._request_bytes("GET", f"/videos/{video_id}/content")
            output_path = self.artifacts.root / job_id / "output.mp4"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(content)
            return [
                Artifact(
                    media_type="video",
                    path=str(output_path),
                    remote_id=video_id,
                    metadata=metadata,
                )
            ]

        path = self.artifacts.save_json(job_id, "openai_video_job", final_video)
        return [
            Artifact(
                media_type="video",
                path=str(path),
                remote_id=video_id,
                metadata=metadata,
            )
        ]

    async def _wait_for_video(self, video_id: str) -> dict[str, Any]:
        deadline = asyncio.get_running_loop().time() + self.settings.video_poll_timeout_seconds
        last_payload = await self._request_json("GET", f"/videos/{video_id}")

        while last_payload.get("status") in {"queued", "in_progress"}:
            if asyncio.get_running_loop().time() >= deadline:
                return last_payload
            await asyncio.sleep(self.settings.video_poll_interval_seconds)
            last_payload = await self._request_json("GET", f"/videos/{video_id}")

        return last_payload

    async def _request_json(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        async with self._client() as client:
            response = await client.request(method, path, **kwargs)
            self._raise_for_status(response)
            return response.json()

    async def _request_bytes(self, method: str, path: str, **kwargs: Any) -> bytes:
        async with self._client() as client:
            response = await client.request(method, path, **kwargs)
            self._raise_for_status(response)
            return response.content

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.settings.openai_base_url,
            timeout=httpx.Timeout(120.0),
            headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
        )

    def _raise_for_status(self, response: httpx.Response) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"OpenAI API error {response.status_code}: {response.text}") from exc

