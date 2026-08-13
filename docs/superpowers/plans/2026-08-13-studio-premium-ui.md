# Studio Premium UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing AI Media Agent web UI into a dark, high-contrast professional creative studio while preserving the current API workflow.

**Architecture:** Keep the no-build static frontend architecture: FastAPI serves `web/index.html`, `web/static/css/styles.css`, and `web/static/js/app.js`. Most of the change is CSS and semantic HTML class/copy updates; JavaScript changes are limited to rendering richer state markup without changing API contracts.

**Tech Stack:** FastAPI `TestClient`, plain HTML, plain CSS, plain JavaScript, pytest.

## Global Constraints

- Keep the first screen as the usable generation tool, not a landing page.
- Do not add a frontend framework, build step, or provider.
- Keep `window.AI_MEDIA_API_BASE_URL = "http://127.0.0.1:8001"`.
- Keep API routes and backend contracts unchanged.
- Keep recent jobs in `localStorage` under `ai-media-agent.jobs`.
- Use a dark cinematic visual system with teal for active/success, amber for queued/running, and red for failed.
- Preserve mobile one-column layout and prevent text overflow inside controls/cards.
- Run `pytest` after each implementation task.

---

## File Structure

- `tests/test_api.py`: protects served homepage and required UI anchors/classes so markup changes are deliberate.
- `web/index.html`: semantic structure for studio shell, command strip, composer controls, preview stage, and recent jobs.
- `web/static/css/styles.css`: complete dark premium studio visual system and responsive layout.
- `web/static/js/app.js`: small rendering markup/copy updates for richer state markup; API and localStorage behavior stay unchanged.

---

### Task 1: Protect Premium UI Markup Anchors

**Files:**
- Modify: `tests/test_api.py`
- Modify: `web/index.html`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: FastAPI `app` from `app.main`.
- Produces: A homepage test that requires the future dark studio markup anchors.

- [ ] **Step 1: Write the failing test**

Add these assertions to `test_web_app_homepage` after the existing assertions:

```python
    assert "studio-shell" in response.text
    assert "command-strip" in response.text
    assert "preview-stage" in response.text
    assert "shot-card" in response.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py::test_web_app_homepage -v`

Expected: FAIL because at least `studio-shell` is not present in the current homepage.

- [ ] **Step 3: Implement minimal markup anchors**

Update `web/index.html` only enough to introduce the anchor classes that the test requires:

```html
<div class="app-shell studio-shell">
<section class="topbar command-strip">
<section class="preview-panel preview-stage" aria-labelledby="previewTitle">
<button type="button" class="preset shot-card" data-preset="product">Chụp sản phẩm</button>
```

Apply `shot-card` to all three preset buttons.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py::test_web_app_homepage -v`

Expected: PASS.

- [ ] **Step 5: Run full tests**

Run: `pytest`

Expected: all tests pass.

- [ ] **Step 6: Commit**

```powershell
git add tests/test_api.py web/index.html
git commit -m "test: protect premium studio UI anchors"
```

---

### Task 2: Restructure Homepage Into Studio Control Room

**Files:**
- Modify: `tests/test_api.py`
- Modify: `web/index.html`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: Existing element ids used by `app.js`: `generationForm`, `prompt`, `style`, `negativePrompt`, `aspectRatio`, `size`, `seconds`, `provider`, `enhancePrompt`, `submitButton`, `refineButton`, `resultFrame`, `jobStatus`, `jobMeta`, `healthStatus`, `recentJobs`.
- Produces: Semantic studio layout classes consumed by CSS: `studio-shell`, `studio-header`, `command-strip`, `command-copy`, `signal-cluster`, `control-panel`, `composer-panel`, `preview-stage`, `stage-frame`, `shot-card`, `recent-panel`.

- [ ] **Step 1: Write the failing test**

Add this test to `tests/test_api.py`:

```python
def test_homepage_exposes_studio_control_room_sections():
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert "studio-header" in response.text
    assert "signal-cluster" in response.text
    assert "control-panel" in response.text
    assert "stage-frame" in response.text
    assert "Cinematic Control Room" in response.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py::test_homepage_exposes_studio_control_room_sections -v`

Expected: FAIL because `Cinematic Control Room` and one or more classes are not present.

- [ ] **Step 3: Update `web/index.html` structure**

Make these structural changes while preserving all ids listed in Interfaces:

```html
<header class="brand-header studio-header" aria-label="AI Media Agent">
```

Replace the current topbar internals with:

```html
<section class="topbar command-strip">
  <div class="command-copy">
    <p class="eyebrow">Cinematic Control Room</p>
    <h1>Tạo asset AI như một studio chuyên nghiệp</h1>
    <p class="lede">Điều phối prompt, provider và preview trong một không gian tối tập trung cho ảnh và video.</p>
  </div>
  <div class="signal-cluster" aria-label="Trạng thái hệ thống">
    <span class="signal-label">Provider</span>
    <div class="status-pill" id="healthStatus">Đang kiểm tra</div>
  </div>
</section>
```

Add `control-panel` to composer:

```html
<section class="composer-panel control-panel" aria-labelledby="composerTitle">
```

Replace preset button content with:

```html
<button type="button" class="preset shot-card" data-preset="product">
  <strong>Chụp sản phẩm</strong>
  <span>Ảnh thương mại sắc nét</span>
</button>
<button type="button" class="preset shot-card" data-preset="campaign">
  <strong>Ảnh chiến dịch</strong>
  <span>Key visual cho thương hiệu</span>
</button>
<button type="button" class="preset shot-card" data-preset="video">
  <strong>Video giới thiệu</strong>
  <span>Chuyển động cinematic</span>
</button>
```

Add `stage-frame` to result frame:

```html
<div class="result-frame stage-frame" id="resultFrame">
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py::test_homepage_exposes_studio_control_room_sections tests/test_api.py::test_web_app_homepage -v`

Expected: PASS.

- [ ] **Step 5: Run full tests**

Run: `pytest`

Expected: all tests pass.

- [ ] **Step 6: Commit**

```powershell
git add tests/test_api.py web/index.html
git commit -m "feat: structure studio control room layout"
```

---

### Task 3: Apply Dark Premium Visual System

**Files:**
- Modify: `tests/test_api.py`
- Modify: `web/static/css/styles.css`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: Classes from Task 2.
- Produces: CSS variables and responsive rules for the dark studio UI.

- [ ] **Step 1: Write the failing test**

Add this test to `tests/test_api.py`:

```python
def test_stylesheet_contains_premium_studio_theme_tokens():
    client = TestClient(app)
    response = client.get("/static/css/styles.css")

    assert response.status_code == 200
    css = response.text
    assert "--bg: #080b10" in css
    assert "--stage: #030508" in css
    assert ".preview-stage" in css
    assert ".shot-card" in css
    assert "@media (max-width: 980px)" in css
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py::test_stylesheet_contains_premium_studio_theme_tokens -v`

Expected: FAIL because the current stylesheet uses the light theme and does not define `--stage`.

- [ ] **Step 3: Replace CSS with dark studio theme**

Update `web/static/css/styles.css` with dark tokens and rules. Required tokens:

```css
:root {
  color-scheme: dark;
  --bg: #080b10;
  --bg-elevated: #0d121a;
  --surface: #111822;
  --surface-strong: #182231;
  --stage: #030508;
  --ink: #eef5f7;
  --muted: #94a3ad;
  --subtle: #5f6f7a;
  --line: rgba(205, 231, 236, 0.14);
  --line-strong: rgba(205, 231, 236, 0.24);
  --teal: #22d3c5;
  --teal-dark: #11a99d;
  --amber: #f3b45b;
  --red: #ff6b6b;
  --shadow: 0 24px 70px rgba(0, 0, 0, 0.42);
}
```

Required behavior:

- `body` uses a dark cinematic layered background.
- `.studio-shell` keeps `width: min(1440px, 100%)` and responsive padding.
- `.studio-header` has translucent dark surface, border, and `backdrop-filter: blur(16px)`.
- `.command-strip` is compact and dark, not a landing hero.
- `.workspace` remains two columns on desktop and one column under `980px`.
- `.control-panel`, `.preview-stage`, `.recent-panel` use dark surfaces, 8px radius, border, and shadow.
- `.stage-frame` uses `background: var(--stage)` and a subtle inset border.
- `.shot-card` displays `strong` and `span`, has visible hover/focus, and avoids text overflow.
- Form controls are dark, readable, and have visible focus rings.
- Job badges use amber/teal/red by status.
- `.json-result` is readable on dark background.
- Mobile rules keep result frame at least `240px` high.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py::test_stylesheet_contains_premium_studio_theme_tokens -v`

Expected: PASS.

- [ ] **Step 5: Run full tests**

Run: `pytest`

Expected: all tests pass.

- [ ] **Step 6: Commit**

```powershell
git add tests/test_api.py web/static/css/styles.css
git commit -m "feat: apply premium dark studio theme"
```

---

### Task 4: Improve Runtime State Markup

**Files:**
- Modify: `tests/test_api.py`
- Modify: `web/static/js/app.js`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: Existing DOM ids and API payloads.
- Produces: Richer state markup using classes `state-panel`, `state-kicker`, `state-title`, `state-copy`; no API behavior changes.

- [ ] **Step 1: Write the failing test**

Add this test to `tests/test_api.py`:

```python
def test_frontend_runtime_states_use_studio_markup():
    client = TestClient(app)
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    js = response.text
    assert "state-panel" in js
    assert "state-kicker" in js
    assert "Render queue" in js
    assert "Tín hiệu lỗi" in js
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py::test_frontend_runtime_states_use_studio_markup -v`

Expected: FAIL because current JS renders only `empty-state` markup.

- [ ] **Step 3: Update state rendering in `app.js`**

Replace `renderEmpty` and `renderError` with:

```javascript
function renderEmpty(title, message, kicker = "Render queue") {
  resultFrame.innerHTML = `<div class="empty-state state-panel"><span class="state-kicker">${escapeHtml(kicker)}</span><strong class="state-title">${escapeHtml(title)}</strong><span class="state-copy">${escapeHtml(message)}</span></div>`;
}

function renderError(message) {
  setJobStatus("failed");
  resultFrame.innerHTML = `<div class="empty-state state-panel"><span class="state-kicker">Tín hiệu lỗi</span><strong class="state-title">Lỗi</strong><span class="state-copy">${escapeHtml(message)}</span></div>`;
}
```

Do not change fetch, payload construction, polling interval, or localStorage behavior.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py::test_frontend_runtime_states_use_studio_markup -v`

Expected: PASS.

- [ ] **Step 5: Run full tests**

Run: `pytest`

Expected: all tests pass.

- [ ] **Step 6: Commit**

```powershell
git add tests/test_api.py web/static/js/app.js
git commit -m "feat: polish studio runtime states"
```

---

### Task 5: Final Verification And Manual Preview

**Files:**
- Modify: none unless verification reveals an issue.
- Test: full project and browser/manual checks.

**Interfaces:**
- Consumes: Completed Tasks 1-4.
- Produces: Verified branch ready for user review.

- [ ] **Step 1: Run full tests**

Run: `pytest`

Expected: all tests pass.

- [ ] **Step 2: Start the local server**

Run: `uvicorn app.main:app --reload --port 8001`

Expected: server starts and serves `http://127.0.0.1:8001/`.

- [ ] **Step 3: Browser/manual check**

Open `http://127.0.0.1:8001/` and verify:

- Desktop layout shows composer left and preview stage right.
- Mobile width stacks into one column.
- Header, command strip, composer, preview stage, and recent jobs are readable on dark background.
- Buttons, tabs, inputs, shot cards, and badges have visible hover/focus states.
- No obvious text overlap or button text overflow.
- `dry_run` generation displays JSON readably in the preview stage.

- [ ] **Step 4: Stop server**

Stop the uvicorn process used for preview.

- [ ] **Step 5: Final status**

Run: `git status --short` and `git log --oneline --max-count 5`.

Expected: only intentional committed changes on `feature/studio-premium-ui`; no uncommitted files.