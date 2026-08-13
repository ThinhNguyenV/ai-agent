# AI Media Agent

Ứng dụng FastAPI cho agent tạo ảnh và video theo yêu cầu. Hệ thống có giao diện web tại `/`, API tạo tác vụ nền, trình tối ưu prompt, và nhiều provider tạo media.

Mặc định project dùng provider self-hosted `diffusers_local`:

- Model ảnh mặc định, không gated: `stabilityai/stable-diffusion-xl-base-1.0`
- Model video mặc định: `Wan-AI/Wan2.1-T2V-1.3B-Diffusers`
- Model video thay thế: `zai-org/CogVideoX-2b`

Provider `dry_run` dùng để test nhanh mà không cần GPU/model. Provider `openai` vẫn có sẵn nếu muốn dùng API trả phí.

## Chức năng

- Tạo `image` hoặc `video` qua API `POST /v1/generations`.
- Giao diện studio có sẵn tại `http://127.0.0.1:8001/`.
- Prompt enhancer có thể tinh chỉnh prompt bằng Ollama local hoặc template fallback.
- Tác vụ chạy nền, có endpoint xem trạng thái `GET /v1/jobs/{job_id}`.
- Provider được tách lớp: `diffusers_local`, `dry_run`, `openai`.
- Artifact được lưu local trong thư mục `artifacts/` và serve qua `/artifacts`.

## Cài đặt nhanh

Yêu cầu Python 3.11+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
```

Chạy test nhanh không cần GPU:

```powershell
pytest
```

Nếu muốn chạy thử server mà không tạo media thật, sửa `.env`:

```dotenv
MEDIA_PROVIDER=dry_run
PROMPT_PROVIDER=template
```

## Chạy server và UI

```powershell
uvicorn app.main:app --reload --port 8001
```

Mở UI:

```text
http://127.0.0.1:8001/
```

Kiểm tra provider/model đang cấu hình:

```powershell
curl http://127.0.0.1:8001/health
```

## Prompt LLM miễn phí

Mặc định `.env.example` dùng `PROMPT_PROVIDER=ollama` để refine prompt bằng LLM local, không gọi OpenAI.

Cài Ollama trên máy, sau đó tải model prompt nhẹ:

```powershell
ollama pull qwen2.5:3b
```

Các model prompt free nên dùng:

```powershell
ollama pull qwen2.5:3b      # mặc định, cân bằng chất lượng/tài nguyên
ollama pull qwen2.5:7b      # tốt hơn nếu máy khỏe hơn
ollama pull llama3.2:1b     # rất nhẹ
ollama pull llama3.2        # 3B, nhanh và gọn
ollama pull gemma3          # lựa chọn thay thế tốt
```

Cấu hình trong `.env`:

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

Muốn tạo ảnh/video và tự refine prompt trước khi tạo, thêm `"enhance_prompt": true` vào body `/v1/generations`.

Nếu chưa cài Ollama, dùng fallback không cần model:

```json
{"provider":"template"}
```

Hoặc đặt trong `.env`:

```dotenv
PROMPT_PROVIDER=template
```

## Provider local miễn phí

Cài các thư viện local-media:

```powershell
pip install -e ".[local,dev]"
```

Nếu dùng NVIDIA GPU, nên cài bản `torch` có CUDA phù hợp với driver của máy theo hướng dẫn PyTorch. Lần chạy đầu tiên sẽ tải model từ Hugging Face, nên cần kết nối mạng và dung lượng đĩa lớn.

Cấu hình mặc định trong `.env.example`:

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

Muốn dùng FLUX.1-schnell thì cần đăng nhập Hugging Face và accept model trước:

```powershell
huggingface-cli login
```

Sau đó sửa `.env`:

```dotenv
LOCAL_IMAGE_MODEL=black-forest-labs/FLUX.1-schnell
LOCAL_IMAGE_STEPS=4
LOCAL_IMAGE_GUIDANCE_SCALE=0.0
```

Đổi video sang CogVideoX-2b:

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

## Gọi API

Tạo ảnh bằng provider mặc định:

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

Tạo video bằng Wan/CogVideoX:

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

Tạo tác vụ async:

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

Xem tác vụ theo id:

```powershell
curl http://127.0.0.1:8001/v1/jobs/<job_id>
```

## Biến môi trường chính

| Biến | Mặc định | Ghi chú |
| --- | --- | --- |
| `MEDIA_PROVIDER` | `diffusers_local` | `dry_run`, `openai`, hoặc `diffusers_local` |
| `PROMPT_PROVIDER` | `ollama` | `template` hoặc `ollama` |
| `ARTIFACT_DIR` | `artifacts` | Nơi lưu kết quả local |
| `LOCAL_IMAGE_MODEL` | `stabilityai/stable-diffusion-xl-base-1.0` | Model ảnh cho `diffusers_local` |
| `LOCAL_VIDEO_MODEL` | `Wan-AI/Wan2.1-T2V-1.3B-Diffusers` | Model video cho `diffusers_local` |
| `LOCAL_DEVICE` | `auto` | Có thể đặt `cuda`, `mps`, hoặc `cpu` |
| `LOCAL_SEED` | rỗng | Đặt seed nếu cần kết quả tái lập |
| `IMAGE_SIZE` | `1024x1024` | Size ảnh mặc định nếu request không gửi `size` |
| `VIDEO_SECONDS` | `4` | Thời lượng video mặc định |
| `VIDEO_SIZE` | `832x480` | Size video mặc định |
| `OPENAI_API_KEY` | rỗng | Bắt buộc nếu dùng provider `openai` |

## Cấu trúc

```text
app/
  main.py                    API FastAPI và static web mount
  core/config.py             Cấu hình từ biến môi trường
  models/schemas.py          Request/response/job models
  services/agent.py          Chuẩn hóa prompt và điều phối provider
  services/jobs.py           In-memory job store
  services/prompt_enhancer.py Refine prompt bằng template/Ollama
  storage/artifacts.py       Lưu file artifact
  providers/base.py          Interface provider
  providers/diffusers_local.py Provider local SDXL/FLUX/Wan/CogVideoX
  providers/dry_run.py       Provider giả lập
  providers/openai.py        Provider OpenAI Images/Videos
web/
  index.html                 UI studio
  static/css/styles.css
  static/js/app.js
tests/
  test_agent.py
  test_api.py
```

## Ghi chú vận hành

- `diffusers_local` là self-hosted: model free, nhưng GPU/điện/cloud vẫn có chi phí nếu thuê máy.
- `Wan-AI/Wan2.1-T2V-1.3B-Diffusers` phù hợp để bắt đầu hơn; size khuyến nghị `832x480`.
- `zai-org/CogVideoX-2b` nên dùng prompt tiếng Anh dài, mô tả rõ hành động/camera; size phù hợp `720x480`.
- Video local là tác vụ nặng. Nên chạy async/background thay vì `wait=true` nếu video mất nhiều phút.
- Một số video pipeline yêu cầu `num_frames - 1` chia hết cho 4. Provider tự động làm tròn về dạng `4k+1` để tránh warning.
- Nếu máy không có GPU NVIDIA/CUDA, tạo video có thể mất rất lâu. Mặc định hệ thống sẽ chặn video local trên CPU và báo lỗi rõ ràng; chỉ đặt `LOCAL_ALLOW_CPU_VIDEO_GENERATION=true` khi bạn thật sự muốn ép chạy CPU.
- Nên thay in-memory job store bằng Redis/Postgres nếu triển khai production.
