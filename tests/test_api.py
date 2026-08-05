from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")

    payload = response.json()
    assert response.status_code == 200
    assert payload["ok"] is True
    assert payload["image_model"] == "stabilityai/stable-diffusion-xl-base-1.0"
    assert payload["prompt_provider"] == "ollama"
    assert payload["prompt_model"] == "qwen2.5:3b"


def test_template_prompt_refine_endpoint():
    client = TestClient(app)
    response = client.post(
        "/v1/prompts/refine",
        json={
            "media_type": "video",
            "prompt": "lop hoc mo cua buoi sang",
            "style": "cinematic realistic",
            "provider": "template",
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["provider"] == "template"
    assert "Cinematic motion" in payload["refined_prompt"]


def test_waiting_dry_run_generation():
    client = TestClient(app)
    response = client.post(
        "/v1/generations",
        json={
            "media_type": "image",
            "prompt": "A clean product image",
            "provider": "dry_run",
            "wait": True,
        },
    )

    payload = response.json()
    assert response.status_code == 202
    assert payload["status"] == "completed"
    assert payload["job"]["artifacts"]


def test_waiting_dry_run_generation_with_template_prompt_enhancer():
    client = TestClient(app)
    response = client.post(
        "/v1/generations",
        json={
            "media_type": "image",
            "prompt": "A clean product image",
            "provider": "dry_run",
            "enhance_prompt": True,
            "prompt_provider": "template",
            "wait": True,
        },
    )

    payload = response.json()
    assert response.status_code == 202
    assert payload["status"] == "completed"
    assert "Prompt was enhanced before media generation." in payload["job"]["plan"]["notes"]

def test_ollama_prompt_refine_unavailable_returns_503():
    client = TestClient(app)
    response = client.post(
        "/v1/prompts/refine",
        json={
            "media_type": "image",
            "prompt": "A clean product image",
            "provider": "ollama",
            "model": "definitely-not-running-test-model",
        },
    )

    assert response.status_code in {503, 502}
    assert "Ollama" in response.json()["detail"]