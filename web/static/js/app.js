const API_BASE_URL = (window.AI_MEDIA_API_BASE_URL || window.location.origin).replace(/\/$/, "");

function apiUrl(path) {
  return `${API_BASE_URL}${path}`;
}
const state = {
  mediaType: "image",
  currentJobId: null,
  pollTimer: null,
};

const statusLabels = {
  idle: "Chưa chạy",
  queued: "Đang chờ",
  running: "Đang tạo",
  completed: "Hoàn tất",
  failed: "Thất bại",
};

const mediaLabels = {
  image: "Ảnh",
  video: "Video",
};

const presets = {
  product: {
    mediaType: "image",
    prompt:
      "Ly cà phê sữa đá Việt Nam cao cấp trên mặt bàn studio sạch, có hơi nước đọng trên ly, phong cách ảnh thương mại",
    style: "ảnh thương mại, chân thực, chỉn chu",
    aspectRatio: "1:1",
    size: "1024x1024",
  },
  campaign: {
    mediaType: "image",
    prompt:
      "Ảnh chủ đạo cho chiến dịch tuyển sinh của một trung tâm học tập hiện đại, lớp học sáng, học viên tự tin, hình ảnh thương hiệu giáo dục chỉn chu",
    style: "thương mại chân thực, bố cục sạch, cảm giác tích cực",
    aspectRatio: "16:9",
    size: "1024x1024",
  },
  video: {
    mediaType: "video",
    prompt:
      "Cảnh giới thiệu sản phẩm cà phê sữa đá Việt Nam trên mặt bàn đá, máy quay tiến chậm, thấy rõ đá lạnh và hơi nước trên ly",
    style: "video thương mại điện ảnh, chuyển động máy mượt, chân thực",
    aspectRatio: "16:9",
    size: "832x480",
    seconds: 4,
  },
};

const form = document.querySelector("#generationForm");
const promptInput = document.querySelector("#prompt");
const styleInput = document.querySelector("#style");
const negativePromptInput = document.querySelector("#negativePrompt");
const aspectRatioInput = document.querySelector("#aspectRatio");
const sizeInput = document.querySelector("#size");
const secondsInput = document.querySelector("#seconds");
const providerInput = document.querySelector("#provider");
const enhancePromptInput = document.querySelector("#enhancePrompt");
const submitButton = document.querySelector("#submitButton");
const refineButton = document.querySelector("#refineButton");
const resultFrame = document.querySelector("#resultFrame");
const jobStatus = document.querySelector("#jobStatus");
const jobMeta = document.querySelector("#jobMeta");
const healthStatus = document.querySelector("#healthStatus");
const recentJobs = document.querySelector("#recentJobs");

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => setMediaType(tab.dataset.media));
});

document.querySelectorAll(".preset").forEach((button) => {
  button.addEventListener("click", () => applyPreset(button.dataset.preset));
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  await createGeneration();
});

refineButton.addEventListener("click", async () => {
  await refinePrompt();
});

loadHealth();
renderRecentJobs();
setMediaType("image");

function setMediaType(mediaType) {
  state.mediaType = mediaType;
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.media === mediaType);
  });
  document.querySelectorAll(".video-only").forEach((node) => {
    node.classList.toggle("is-hidden", mediaType !== "video");
  });
  if (mediaType === "image" && !sizeInput.value.includes("1024")) {
    sizeInput.value = "1024x1024";
  }
  if (mediaType === "video" && sizeInput.value === "1024x1024") {
    sizeInput.value = "832x480";
  }
}

function applyPreset(name) {
  const preset = presets[name];
  if (!preset) return;
  setMediaType(preset.mediaType);
  promptInput.value = preset.prompt;
  styleInput.value = preset.style;
  aspectRatioInput.value = preset.aspectRatio;
  sizeInput.value = preset.size;
  if (preset.seconds) secondsInput.value = String(preset.seconds);
}

async function loadHealth() {
  try {
    const response = await fetch(apiUrl("/health"));
    const payload = await response.json();
    healthStatus.textContent = `${payload.provider} / ${payload.prompt_provider || "prompt"}`;
    healthStatus.classList.add("ok");
  } catch (error) {
    healthStatus.textContent = "Mất kết nối";
  }
}

async function refinePrompt() {
  setBusy(true);
  try {
    const response = await fetch(apiUrl("/v1/prompts/refine"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        media_type: state.mediaType,
        prompt: promptInput.value,
        style: styleInput.value || null,
        negative_prompt: negativePromptInput.value || null,
        aspect_ratio: aspectRatioInput.value || null,
        provider: "template",
      }),
    });
    const payload = await parseResponse(response);
    promptInput.value = payload.refined_prompt;
    if (payload.negative_prompt && !negativePromptInput.value) {
      negativePromptInput.value = payload.negative_prompt;
    }
  } catch (error) {
    renderError(error.message);
  } finally {
    setBusy(false);
  }
}

async function createGeneration() {
  setBusy(true);
  clearPolling();
  setJobStatus("queued");
  renderEmpty("Đang chờ", "Studio đã nhận tác vụ tạo nội dung.");

  try {
    const response = await fetch(apiUrl("/v1/generations"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildGenerationPayload()),
    });
    const payload = await parseResponse(response);
    state.currentJobId = payload.job_id;
    rememberJob(payload.job_id, promptInput.value, state.mediaType);
    renderRecentJobs();

    if (payload.job) {
      renderJob(payload.job);
      setBusy(false);
      return;
    }

    await pollJob(payload.job_id);
    state.pollTimer = window.setInterval(() => pollJob(payload.job_id), 1600);
  } catch (error) {
    renderError(error.message);
    setBusy(false);
  }
}

function buildGenerationPayload() {
  const payload = {
    media_type: state.mediaType,
    prompt: promptInput.value,
    style: styleInput.value || null,
    negative_prompt: negativePromptInput.value || null,
    aspect_ratio: aspectRatioInput.value || null,
    size: sizeInput.value || null,
    provider: providerInput.value || null,
    enhance_prompt: enhancePromptInput.checked,
    wait: false,
  };

  if (state.mediaType === "video") {
    payload.seconds = Number(secondsInput.value || 4);
  }

  return payload;
}

async function pollJob(jobId) {
  try {
    const response = await fetch(apiUrl(`/v1/jobs/${jobId}`));
    const job = await parseResponse(response);
    renderJob(job);
    if (job.status === "completed" || job.status === "failed") {
      clearPolling();
      setBusy(false);
    }
  } catch (error) {
    clearPolling();
    setBusy(false);
    renderError(error.message);
  }
}

function renderJob(job) {
  setJobStatus(job.status);
  renderMeta(job);

  if (job.status === "failed") {
    renderError(job.error || "Tác vụ tạo nội dung thất bại.");
    return;
  }

  if (job.status !== "completed") {
    renderEmpty(
      statusLabels[job.status] || job.status,
      job.plan ? "Nhà cung cấp đang tạo nội dung." : "Đang chuẩn bị kế hoạch tạo nội dung.",
    );
    return;
  }

  const artifact = job.artifacts?.[0];
  if (!artifact) {
    renderEmpty("Hoàn tất", "Tác vụ không trả về artifact.");
    return;
  }

  const source = artifactSource(artifact);
  if (artifact.media_type === "image" && source && !source.endsWith(".json")) {
    resultFrame.innerHTML = `<img src="${escapeHtml(source)}" alt="Ảnh đã tạo" />`;
    return;
  }

  if (artifact.media_type === "video" && source && !source.endsWith(".json")) {
    resultFrame.innerHTML = `<video src="${escapeHtml(source)}" controls playsinline></video>`;
    return;
  }

  resultFrame.innerHTML = `<pre class="json-result">${escapeHtml(JSON.stringify(job.plan || artifact, null, 2))}</pre>`;
}

function renderMeta(job) {
  const plan = job.plan || {};
  const rows = [
    ["Tác vụ", job.id],
    ["Loại", mediaLabels[job.request?.media_type] || job.request?.media_type],
    ["Nhà cung cấp", plan.provider || job.request?.provider || "hệ thống"],
    ["Kích thước", plan.size || job.request?.size || "mặc định"],
    ["Cập nhật", new Date(job.updated_at).toLocaleString("vi-VN")],
  ];

  jobMeta.innerHTML = rows
    .filter(([, value]) => value)
    .map(([label, value]) => `<dt>${label}</dt><dd>${escapeHtml(String(value))}</dd>`)
    .join("");
}

function setJobStatus(status) {
  jobStatus.textContent = statusLabels[status] || status;
  jobStatus.className = `job-badge ${status}`;
}

function renderEmpty(title, message) {
  resultFrame.innerHTML = `<div class="empty-state"><strong>${escapeHtml(title)}</strong><span>${escapeHtml(message)}</span></div>`;
}

function renderError(message) {
  setJobStatus("failed");
  resultFrame.innerHTML = `<div class="empty-state"><strong>Lỗi</strong><span>${escapeHtml(message)}</span></div>`;
}

function artifactSource(artifact) {
  if (artifact.url) return artifact.url;
  if (!artifact.path) return "";

  const normalized = artifact.path.replaceAll("\\", "/");
  const marker = "/artifacts/";
  const markerIndex = normalized.lastIndexOf(marker);
  if (markerIndex >= 0) {
    return apiUrl(normalized.slice(markerIndex));
  }
  if (normalized.startsWith("artifacts/")) {
    return apiUrl(`/${normalized}`);
  }
  return normalized;
}

function clearPolling() {
  if (state.pollTimer) {
    window.clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
}

function setBusy(isBusy) {
  submitButton.disabled = isBusy;
  refineButton.disabled = isBusy;
  submitButton.textContent = isBusy ? "Đang xử lý" : "Tạo nội dung";
}

async function parseResponse(response) {
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || `Yêu cầu thất bại với mã ${response.status}`);
  }
  return payload;
}

function rememberJob(jobId, prompt, mediaType) {
  const jobs = getRecentJobs().filter((job) => job.id !== jobId);
  jobs.unshift({
    id: jobId,
    prompt,
    mediaType,
    createdAt: new Date().toISOString(),
  });
  window.localStorage.setItem("ai-media-agent.jobs", JSON.stringify(jobs.slice(0, 8)));
}

function getRecentJobs() {
  try {
    return JSON.parse(window.localStorage.getItem("ai-media-agent.jobs") || "[]");
  } catch (error) {
    return [];
  }
}

function renderRecentJobs() {
  const jobs = getRecentJobs();
  if (!jobs.length) {
    recentJobs.innerHTML = `<div class="empty-state"><strong>Chưa có tác vụ</strong><span>Phiên làm việc này chưa có tác vụ gần đây.</span></div>`;
    return;
  }

  recentJobs.innerHTML = jobs
    .map(
      (job) => `
      <button class="recent-job" type="button" data-job-id="${escapeHtml(job.id)}">
        <span>
          <strong>${escapeHtml(mediaLabels[job.mediaType] || job.mediaType)}</strong>
          <span>${escapeHtml(job.prompt)}</span>
        </span>
        <span>${new Date(job.createdAt).toLocaleTimeString("vi-VN")}</span>
      </button>
    `,
    )
    .join("");

  recentJobs.querySelectorAll(".recent-job").forEach((button) => {
    button.addEventListener("click", async () => {
      state.currentJobId = button.dataset.jobId;
      clearPolling();
      setBusy(true);
      await pollJob(button.dataset.jobId);
      setBusy(false);
    });
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
