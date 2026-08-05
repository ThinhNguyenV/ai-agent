import base64
import json
from pathlib import Path
from typing import Any


class ArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def save_base64(self, job_id: str, payload: str, suffix: str) -> Path:
        job_dir = self._job_dir(job_id)
        data = payload.split(",", 1)[-1]
        output_path = job_dir / f"output.{suffix.lstrip('.')}"
        output_path.write_bytes(base64.b64decode(data))
        return output_path

    def save_json(self, job_id: str, name: str, payload: dict[str, Any]) -> Path:
        job_dir = self._job_dir(job_id)
        output_path = job_dir / f"{name}.json"
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return output_path

    def _job_dir(self, job_id: str) -> Path:
        job_dir = self.root / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir
