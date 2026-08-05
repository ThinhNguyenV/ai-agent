import re

import httpx

from app.core.config import Settings
from app.models.schemas import PromptRefineRequest, PromptRefineResponse


class PromptEnhancerUnavailable(RuntimeError):
    pass


class PromptEnhancer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def refine(self, request: PromptRefineRequest) -> PromptRefineResponse:
        provider = request.provider or self.settings.prompt_provider
        if provider == "template":
            return self._refine_with_template(request)
        if provider == "ollama":
            return await self._refine_with_ollama(request)
        raise ValueError(f"Unsupported prompt provider: {provider}")

    def refine_with_template(self, request: PromptRefineRequest, note: str | None = None) -> PromptRefineResponse:
        response = self._refine_with_template(request)
        if note:
            response.notes.append(note)
        return response

    def _refine_with_template(self, request: PromptRefineRequest) -> PromptRefineResponse:
        parts = [self._clean(request.prompt)]
        if request.style:
            parts.append(f"Style: {self._clean(request.style)}.")
        if request.aspect_ratio:
            parts.append(f"Aspect ratio: {request.aspect_ratio}.")
        if request.media_type == "image":
            parts.append("High detail, coherent composition, natural lighting, sharp subject, production-ready image.")
        else:
            parts.append(
                "Cinematic motion, clear subject action, stable camera language, temporal consistency, realistic lighting."
            )
        return PromptRefineResponse(
            original_prompt=request.prompt,
            refined_prompt=" ".join(parts),
            negative_prompt=request.negative_prompt,
            provider="template",
            model=None,
            notes=["Template prompt enhancer; no external model was called."],
        )

    async def _refine_with_ollama(self, request: PromptRefineRequest) -> PromptRefineResponse:
        model = request.model or self.settings.ollama_prompt_model
        payload = {
            "model": model,
            "prompt": self._ollama_prompt(request),
            "stream": False,
            "options": {
                "temperature": self.settings.ollama_temperature,
                "num_predict": self.settings.ollama_num_predict,
            },
        }
        try:
            async with httpx.AsyncClient(
                base_url=self.settings.ollama_base_url,
                timeout=self.settings.ollama_timeout_seconds,
            ) as client:
                response = await client.post("/generate", json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.ConnectError as exc:
            raise PromptEnhancerUnavailable(
                f"Ollama is not reachable at {self.settings.ollama_base_url}. "
                f"Install/start Ollama and run: ollama pull {model}. "
                "Or send provider='template' to refine without a local LLM."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"Ollama API error {exc.response.status_code}: {exc.response.text}") from exc

        refined = self._strip_wrapping(data.get("response", ""))
        if not refined:
            raise RuntimeError("Ollama returned an empty prompt refinement")

        return PromptRefineResponse(
            original_prompt=request.prompt,
            refined_prompt=refined,
            negative_prompt=request.negative_prompt,
            provider="ollama",
            model=model,
            notes=["Generated locally via Ollama; no OpenAI API call was used."],
        )

    def _ollama_prompt(self, request: PromptRefineRequest) -> str:
        target = "text-to-image model FLUX.1-schnell" if request.media_type == "image" else "text-to-video model Wan/CogVideoX"
        constraints = [
            "Rewrite the user's idea into one strong English generation prompt.",
            f"Target: {target}.",
            "Keep the output as plain text only. No markdown, no JSON, no labels, no explanation.",
            "Preserve the user's intent. Add concrete visual details, composition, lighting, subject, environment, mood, and quality cues.",
        ]
        if request.media_type == "video":
            constraints.append("Include camera motion, subject action, scene continuity, pacing, and temporal consistency.")
        if request.style:
            constraints.append(f"Requested style: {request.style}.")
        if request.aspect_ratio:
            constraints.append(f"Requested aspect ratio: {request.aspect_ratio}.")
        if request.negative_prompt:
            constraints.append(f"Avoid: {request.negative_prompt}.")
        constraints.append(f"User idea: {request.prompt}")
        return "\n".join(constraints)

    def _clean(self, value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def _strip_wrapping(self, value: str) -> str:
        cleaned = self._clean(value).strip('"')
        for prefix in ("Prompt:", "Refined prompt:", "Image prompt:", "Video prompt:"):
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
        return cleaned