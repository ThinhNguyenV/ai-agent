# AI Media Agent

He thong FastAPI cho agent tao anh va video theo yeu cau. Mac dinh he thong dung provider `diffusers_local` voi cac model free/self-hosted:

- Anh mac dinh khong gated: `stabilityai/stable-diffusion-xl-base-1.0`
- Video mac dinh: `Wan-AI/Wan2.1-T2V-1.3B-Diffusers`
- Video thay the: `zai-org/CogVideoX-2b`

`dry_run` van co san de test luong xu ly khong can GPU/model. `openai` van giu lai nhu provider tra phi tuy chon.

## Chuc nang

- Nhan yeu cau tao `image` hoac `video` qua API.
- Agent chuan hoa prompt tu mo ta cua nguoi dung, style, ti le khung hinh, negative prompt.
- Job chay nen, co endpoint xem trang thai.
- Provider tach lop: `diffusers_local`, `dry_run`, `openai`.
- Luu artifact local trong thu muc `artifacts/`.

## Cai dat nhanh

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
```

Chay test nhanh khong can GPU:

```powershell
pytest
```

## Prompt LLM mien phi

He thong dung `PROMPT_PROVIDER=ollama` de refine prompt dau vao bang LLM local, khong goi OpenAI.

Cai Ollama tren may, sau do tai model prompt nhe:

```powershell
ollama pull qwen2.5:3b
```

Cac model prompt free nen dung:

```powershell
ollama pull qwen2.5:3b      # mac dinh, can bang chat luong/tai nguyen
ollama pull qwen2.5:7b      # tot hon neu may khoe hon
ollama pull llama3.2:1b     # rat nhe
ollama pull llama3.2        # 3B, nhanh va gon
ollama pull gemma3          # lua chon thay the tot
```

Cau hinh trong `.env`:

```dotenv
PROMPT_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/api
OLLAMA_PROMPT_MODEL=qwen2.5:3b
```

Test endpoint refine prompt:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/prompts/refine" `
  -Method Post `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{"media_type":"image","prompt":"quang cao ca phe sua da Viet Nam","style":"commercial photography"}'
```

Muon tao anh/video va tu refine prompt truoc khi tao, them `"enhance_prompt": true` vao body `/v1/generations`.

Neu chua cai Ollama, co the dung fallback khong can model:

```json
{"provider":"template"}
```
## Cai provider local mien phi

Cai cac thu vien local-media:

```powershell
pip install -e ".[local,dev]"
```

Neu dung NVIDIA GPU, nen cai ban `torch` co CUDA phu hop driver cua may truoc/sau lenh tren theo huong dan PyTorch. Lan chay dau tien se tai model tu Hugging Face, nen can dung luong dia cung lon va co ket noi mang.

`.env` mac dinh da duoc dat nhu sau:

```dotenv
MEDIA_PROVIDER=diffusers_local
LOCAL_IMAGE_MODEL=stabilityai/stable-diffusion-xl-base-1.0
LOCAL_VIDEO_MODEL=Wan-AI/Wan2.1-T2V-1.3B-Diffusers
VIDEO_SIZE=832x480
```

Muon dung FLUX.1-schnell thi can dang nhap Hugging Face va accept model truoc:

```powershell
huggingface-cli login
```

Sau do sua `.env`:

```dotenv
LOCAL_IMAGE_MODEL=black-forest-labs/FLUX.1-schnell
LOCAL_IMAGE_STEPS=4
LOCAL_IMAGE_GUIDANCE_SCALE=0.0
```

Doi video sang CogVideoX-2b:

```dotenv
LOCAL_VIDEO_MODEL=zai-org/CogVideoX-2b
VIDEO_SIZE=720x480
LOCAL_VIDEO_FPS=8
LOCAL_VIDEO_STEPS=50
```

Chay thu khong tao media that:

```dotenv
MEDIA_PROVIDER=dry_run
```

Provider OpenAI van co the dung khi can:

```dotenv
MEDIA_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_IMAGE_MODEL=gpt-image-1.5
OPENAI_VIDEO_MODEL=sora-2
```

## Chay server

```powershell
uvicorn app.main:app --reload --port 8001
```

Kiem tra provider/model dang cau hinh:

```powershell
curl http://127.0.0.1:8000/health
```

Tao anh bang FLUX:

```powershell
$body = @{
  media_type = "image"
  prompt = "A premium Vietnamese iced coffee product shot on a marble counter, commercial photography"
  wait = $true
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8001/v1/generations" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

Tao video bang Wan/CogVideoX:

```powershell
$body = @{
    media_type = "video"
    prompt     = "Slow cinematic shot of a modern tutoring center opening in the morning"
    style      = "warm realistic commercial"
    seconds    = 10
    wait       = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/v1/generations" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

Xem job:

```powershell
curl http://127.0.0.1:8000/v1/jobs/<job_id>
```

## Cau truc

```text
app/
  main.py                    API FastAPI
  core/config.py             Cau hinh tu bien moi truong
  models/schemas.py          Request/response/job models
  services/agent.py          Chuan hoa prompt va dieu phoi provider
  services/jobs.py           In-memory job store
  storage/artifacts.py       Luu file artifact
  providers/base.py          Interface provider
  providers/diffusers_local.py Provider local FLUX/Wan/CogVideoX
  providers/dry_run.py       Provider gia lap
  providers/openai.py        Provider OpenAI Images/Videos
tests/
  test_agent.py
  test_api.py
```

## Ghi chu van hanh

- `diffusers_local` la self-hosted: model free, nhung GPU/dien/cloud van co chi phi neu thue may.
- `Wan-AI/Wan2.1-T2V-1.3B-Diffusers` phu hop bat dau hon; size khuyen nghi `832x480`.
- `zai-org/CogVideoX-2b` nen dung prompt tieng Anh dai, mo ta ro hanh dong/camera; size phu hop `720x480`.
- Video local la tac vu nang. Nen chay async/background thay vi `wait=true` neu video mat nhieu phut.
- Nen thay in-memory job store bang Redis/Postgres neu trien khai production.
