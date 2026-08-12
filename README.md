# AI Media Agent

FastAPI app cho agent tao anh va video theo yeu cau. He thong co UI web tai `/`, API tao job nen, prompt enhancer, va nhieu provider media.

Mac dinh project dung provider self-hosted `diffusers_local`:

- Anh mac dinh khong gated: `stabilityai/stable-diffusion-xl-base-1.0`
- Video mac dinh: `Wan-AI/Wan2.1-T2V-1.3B-Diffusers`
- Video thay the: `zai-org/CogVideoX-2b`

Provider `dry_run` dung de test nhanh khong can GPU/model. Provider `openai` van co san neu muon dung API tra phi.

## Chuc nang

- Tao `image` hoac `video` qua API `POST /v1/generations`.
- UI studio co san tai `http://127.0.0.1:8001/`.
- Prompt enhancer co the refine prompt bang Ollama local hoac template fallback.
- Job chay nen, co endpoint xem trang thai `GET /v1/jobs/{job_id}`.
- Provider tach lop: `diffusers_local`, `dry_run`, `openai`.
- Artifact duoc luu local trong thu muc `artifacts/` va serve qua `/artifacts`.

## Cai dat nhanh

Yeu cau Python 3.11+.

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

Neu muon chay thu server khong tao media that, sua `.env`:

```dotenv
MEDIA_PROVIDER=dry_run
PROMPT_PROVIDER=template
```

## Chay server va UI

```powershell
uvicorn app.main:app --reload --port 8001
```

Mo UI:

```text
http://127.0.0.1:8001/
```

Kiem tra provider/model dang cau hinh:

```powershell
curl http://127.0.0.1:8001/health
```

## Prompt LLM mien phi

Mac dinh `.env.example` dung `PROMPT_PROVIDER=ollama` de refine prompt bang LLM local, khong goi OpenAI.

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
Invoke-RestMethod -Uri "http://127.0.0.1:8001/v1/prompts/refine" `
  -Method Post `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{"media_type":"image","prompt":"quang cao ca phe sua da Viet Nam","style":"commercial photography"}'
```

Muon tao anh/video va tu refine prompt truoc khi tao, them `"enhance_prompt": true` vao body `/v1/generations`.

Neu chua cai Ollama, dung fallback khong can model:

```json
{"provider":"template"}
```

Hoac dat trong `.env`:

```dotenv
PROMPT_PROVIDER=template
```

## Provider local mien phi

Cai cac thu vien local-media:

```powershell
pip install -e ".[local,dev]"
```

Neu dung NVIDIA GPU, nen cai ban `torch` co CUDA phu hop driver cua may theo huong dan PyTorch. Lan chay dau tien se tai model tu Hugging Face, nen can ket noi mang va dung luong dia cung lon.

Cau hinh mac dinh trong `.env.example`:

```dotenv
MEDIA_PROVIDER=diffusers_local
LOCAL_IMAGE_MODEL=stabilityai/stable-diffusion-xl-base-1.0
LOCAL_VIDEO_MODEL=Wan-AI/Wan2.1-T2V-1.3B-Diffusers
LOCAL_IMAGE_STEPS=30
LOCAL_IMAGE_GUIDANCE_SCALE=7.5
LOCAL_VIDEO_STEPS=20
LOCAL_VIDEO_FPS=12
LOCAL_VIDEO_NUM_FRAMES=49
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
LOCAL_VIDEO_STEPS=30
```

Provider OpenAI:

```dotenv
MEDIA_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_IMAGE_MODEL=gpt-image-1.5
OPENAI_VIDEO_MODEL=sora-2
```

## Goi API

Tao anh bang provider mac dinh:

```powershell
$body = @{
  media_type = "image"
  prompt = "A premium Vietnamese iced coffee product shot on a marble counter, commercial photography"
  style = "clean commercial photography"
  enhance_prompt = $true
  wait = $true
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8001/v1/generations" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

Tao video bang Wan/CogVideoX:

```powershell
$body = @{
  media_type = "video"
  prompt = "Slow cinematic shot of a modern tutoring center opening in the morning"
  style = "warm realistic commercial"
  seconds = 4
  size = "832x480"
  wait = $true
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8001/v1/generations" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

Tao job async:

```powershell
$body = @{
  media_type = "image"
  prompt = "A clean product image"
  provider = "dry_run"
  wait = $false
} | ConvertTo-Json

$job = Invoke-RestMethod `
  -Uri "http://127.0.0.1:8001/v1/generations" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body

Invoke-RestMethod -Uri $job.job_url
```

Xem job theo id:

```powershell
curl http://127.0.0.1:8001/v1/jobs/<job_id>
```

## Bien moi truong chinh

| Bien | Mac dinh | Ghi chu |
| --- | --- | --- |
| `MEDIA_PROVIDER` | `diffusers_local` | `dry_run`, `openai`, hoac `diffusers_local` |
| `PROMPT_PROVIDER` | `ollama` | `template` hoac `ollama` |
| `ARTIFACT_DIR` | `artifacts` | Noi luu ket qua local |
| `LOCAL_IMAGE_MODEL` | `stabilityai/stable-diffusion-xl-base-1.0` | Model anh cho `diffusers_local` |
| `LOCAL_VIDEO_MODEL` | `Wan-AI/Wan2.1-T2V-1.3B-Diffusers` | Model video cho `diffusers_local` |
| `LOCAL_DEVICE` | `auto` | Co the dat `cuda`, `mps`, hoac `cpu` |
| `LOCAL_SEED` | rong | Dat seed neu can ket qua tai lap |
| `IMAGE_SIZE` | `1024x1024` | Size anh mac dinh neu request khong gui `size` |
| `VIDEO_SECONDS` | `4` | Thoi luong video mac dinh |
| `VIDEO_SIZE` | `832x480` | Size video mac dinh |
| `OPENAI_API_KEY` | rong | Bat buoc neu dung provider `openai` |

## Cau truc

```text
app/
  main.py                    API FastAPI va static web mount
  core/config.py             Cau hinh tu bien moi truong
  models/schemas.py          Request/response/job models
  services/agent.py          Chuan hoa prompt va dieu phoi provider
  services/jobs.py           In-memory job store
  services/prompt_enhancer.py Refine prompt bang template/Ollama
  storage/artifacts.py       Luu file artifact
  providers/base.py          Interface provider
  providers/diffusers_local.py Provider local SDXL/FLUX/Wan/CogVideoX
  providers/dry_run.py       Provider gia lap
  providers/openai.py        Provider OpenAI Images/Videos
web/
  index.html                 UI studio
  static/css/styles.css
  static/js/app.js
tests/
  test_agent.py
  test_api.py
```

## Ghi chu van hanh

- `diffusers_local` la self-hosted: model free, nhung GPU/dien/cloud van co chi phi neu thue may.
- `Wan-AI/Wan2.1-T2V-1.3B-Diffusers` phu hop bat dau hon; size khuyen nghi `832x480`.
- `zai-org/CogVideoX-2b` nen dung prompt tieng Anh dai, mo ta ro hanh dong/camera; size phu hop `720x480`.
- Video local la tac vu nang. Nen chay async/background thay vi `wait=true` neu video mat nhieu phut.
- Mot so video pipeline yeu cau `num_frames - 1` chia het cho 4. Provider tu dong lam tron ve dang `4k+1` de tranh warning.
- Neu may khong co GPU NVIDIA/CUDA, tao video co the mat rat lau.
- Nen thay in-memory job store bang Redis/Postgres neu trien khai production.
