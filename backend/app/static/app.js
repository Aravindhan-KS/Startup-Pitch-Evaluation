// ── DOM refs ──────────────────────────────────────────────────────────────────
const form          = document.getElementById("pitchForm");
const clearBtn      = document.getElementById("clearBtn");
const purgeBtn      = document.getElementById("purgeBtn");
const evaluateBtn   = document.getElementById("evaluateBtn");
const statusText    = document.getElementById("statusText");
const pitchPreview  = document.getElementById("pitchPreview");
const modeBadge     = document.getElementById("modeBadge");

const evaluationPlaceholder = document.getElementById("evaluationPlaceholder");
const evaluationResults     = document.getElementById("evaluationResults");
const summaryCard           = document.getElementById("summaryCard");
const quantScores           = document.getElementById("quantScores");
const modalityWeights       = document.getElementById("modalityWeights");
const riskDistribution      = document.getElementById("riskDistribution");
const guidanceList          = document.getElementById("guidanceList");
const chunkReports          = document.getElementById("chunkReports");
const rawJson               = document.getElementById("rawJson");
const overallKpi            = document.getElementById("overallKpi");
const confidenceKpi         = document.getElementById("confidenceKpi");
const bandKpi               = document.getElementById("bandKpi");
const outputPanel           = document.querySelector(".output-panel");

// Upload + video preview
const uploadZone      = document.getElementById("uploadZone");
const videoUpload     = document.getElementById("videoUpload");
const uploadHint      = document.getElementById("uploadHint");
const uploadProgress  = document.getElementById("uploadProgress");
const progressFill    = document.getElementById("progressFill");
const progressLabel   = document.getElementById("progressLabel");
const videoContainer  = document.getElementById("videoContainer");
const pitchVideo      = document.getElementById("pitchVideo");
const videoTitle      = document.getElementById("videoTitle");
const videoDuration   = document.getElementById("videoDuration");
const videoSize       = document.getElementById("videoSize");
const removeVideoBtn  = document.getElementById("removeVideoBtn");

// Rating panel
const videoRatingPanel = document.getElementById("videoRatingPanel");
const finalScore       = document.getElementById("finalScore");
const videoRatingBand  = document.getElementById("videoRatingBand");
const videoRatingText  = document.getElementById("videoRatingText");

// ── State ─────────────────────────────────────────────────────────────────────
const MAX_FILE_BYTES = 500 * 1024 * 1024; // 500 MB — matches nginx + EBS headroom
let   selectedFile        = null;
let   localObjectUrl      = null;
let   latestRating        = null;
let   currentScoringMode  = "unknown";

const fields = {
  title:       document.getElementById("title"),
  slideText:   document.getElementById("slideText"),
  founderName: document.getElementById("founderName"),
  startupName: document.getElementById("startupName"),
  sector:      document.getElementById("sector"),
  stage:       document.getElementById("stage"),
};

// ── Utilities ─────────────────────────────────────────────────────────────────
function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function listFromTextarea(value) {
  return value.split("\n").map((l) => l.trim()).filter(Boolean);
}

function formatBytes(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDuration(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

// ── Pitch preview ─────────────────────────────────────────────────────────────
function buildPreviewData() {
  const slidePoints = listFromTextarea(fields.slideText.value);
  return {
    title:      fields.title.value.trim() || "Untitled Pitch",
    user_details: {
      founder_name: fields.founderName.value.trim(),
      startup_name: fields.startupName.value.trim() || fields.title.value.trim(),
      sector:       fields.sector.value.trim(),
      stage:        fields.stage.value.trim(),
    },
    slides: slidePoints,
  };
}

function renderPitchPreview(data) {
  pitchPreview.innerHTML = `
    <h3>${escapeHtml(data.title)}</h3>
    <p><strong>Founder:</strong> ${escapeHtml(data.user_details.founder_name || "N/A")}</p>
    <p><strong>Sector:</strong> ${escapeHtml(data.user_details.sector || "N/A")} · <strong>Stage:</strong> ${escapeHtml(data.user_details.stage || "N/A")}</p>
    <p><strong>Slides:</strong> ${data.slides.length} · <strong>Video:</strong> ${selectedFile ? escapeHtml(selectedFile.name) : "none"}</p>
  `;
}

// ── File upload handling ───────────────────────────────────────────────────────
function applyFile(file) {
  if (!file) return;

  if (file.size > MAX_FILE_BYTES) {
    setStatus(`File too large (${formatBytes(file.size)}). Max is 500 MB.`, "error");
    return;
  }

  // Revoke any previous object URL to free memory
  if (localObjectUrl) {
    URL.revokeObjectURL(localObjectUrl);
    localObjectUrl = null;
  }

  selectedFile   = file;
  localObjectUrl = URL.createObjectURL(file);

  pitchVideo.src   = localObjectUrl;
  videoTitle.textContent = file.name;
  videoSize.textContent  = formatBytes(file.size);
  videoContainer.classList.remove("hidden");
  uploadZone.classList.add("has-file");

  // Auto-fill title from filename if blank
  if (!fields.title.value.trim()) {
    fields.title.value = file.name.replace(/\.[^.]+$/, "");
    renderPitchPreview(buildPreviewData());
  }
}

function clearVideo() {
  if (localObjectUrl) {
    URL.revokeObjectURL(localObjectUrl);
    localObjectUrl = null;
  }
  selectedFile = null;
  pitchVideo.src = "";
  pitchVideo.load();
  videoContainer.classList.add("hidden");
  uploadZone.classList.remove("has-file");
  videoUpload.value = "";
  videoDuration.textContent = "";
  videoSize.textContent     = "";
  videoTitle.textContent    = "";
  videoRatingPanel.classList.add("hidden");
}

// ── Drag-and-drop ─────────────────────────────────────────────────────────────
uploadZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadZone.classList.add("drag-over");
});

uploadZone.addEventListener("dragleave", () => {
  uploadZone.classList.remove("drag-over");
});

uploadZone.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadZone.classList.remove("drag-over");
  const file = e.dataTransfer?.files?.[0];
  if (file) applyFile(file);
});

videoUpload.addEventListener("change", () => {
  const file = videoUpload.files?.[0];
  if (file) applyFile(file);
});

removeVideoBtn.addEventListener("click", clearVideo);

pitchVideo.addEventListener("loadedmetadata", () => {
  const dur = pitchVideo.duration;
  if (Number.isFinite(dur)) {
    videoDuration.textContent = `Duration: ${formatDuration(dur)}`;
  }
});

pitchVideo.addEventListener("ended", () => {
  setTimeout(() => { if (latestRating) showRatingPanel(latestRating.score, latestRating.band); }, 2000);
});

// ── Rating panel ──────────────────────────────────────────────────────────────
function showRatingPanel(score, band) {
  finalScore.textContent   = score;
  videoRatingBand.textContent = band || "—";
  videoRatingText.textContent = "Rating based on video analysis";
  videoRatingPanel.classList.remove("hidden");
}

// ── Status helpers ────────────────────────────────────────────────────────────
function setStatus(msg, kind = "info") {
  statusText.textContent = msg;
  statusText.dataset.kind = kind;
}

function setLoading(isLoading) {
  evaluateBtn.disabled = isLoading;
  outputPanel.classList.toggle("is-loading", isLoading);
}

function showError(message) {
  evaluationPlaceholder.classList.remove("hidden");
  evaluationPlaceholder.textContent = message;
  evaluationResults.classList.add("hidden");
}

// ── Progress bar ──────────────────────────────────────────────────────────────
function setProgress(pct, label) {
  uploadProgress.classList.remove("hidden");
  progressFill.style.width = `${Math.min(100, pct).toFixed(1)}%`;
  progressLabel.textContent = label;
}

function hideProgress() {
  uploadProgress.classList.add("hidden");
  progressFill.style.width = "0%";
}

// ── Evaluate (multipart upload + XHR for progress) ───────────────────────────
function evaluateWithFile(file) {
  return new Promise((resolve, reject) => {
    const fd = new FormData();
    fd.append("video",        file, file.name);
    fd.append("title",        fields.title.value.trim() || file.name.replace(/\.[^.]+$/, ""));
    fd.append("transcript",   "");
    fd.append("language_hint","en-ta");
    fd.append("slide_text",   fields.slideText.value.trim());
    fd.append("founder_name", fields.founderName.value.trim());
    fd.append("startup_name", fields.startupName.value.trim() || fields.title.value.trim());
    fd.append("sector",       fields.sector.value.trim());
    fd.append("stage",        fields.stage.value.trim());

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/evaluate");

    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        const pct = (e.loaded / e.total) * 100;
        setProgress(pct, pct < 100
          ? `Uploading… ${formatBytes(e.loaded)} / ${formatBytes(e.total)}`
          : "Processing pipeline…"
        );
      }
    });

    xhr.addEventListener("load", () => {
      hideProgress();
      if (xhr.status >= 200 && xhr.status < 300) {
        try { resolve(JSON.parse(xhr.responseText)); }
        catch { reject(new Error("Invalid JSON response from server")); }
      } else {
        reject(new Error(`Server error ${xhr.status}: ${xhr.responseText.slice(0, 220)}`));
      }
    });

    xhr.addEventListener("error",  () => { hideProgress(); reject(new Error("Network error during upload")); });
    xhr.addEventListener("abort",  () => { hideProgress(); reject(new Error("Upload aborted")); });
    xhr.addEventListener("timeout",() => { hideProgress(); reject(new Error("Upload timed out")); });

    xhr.timeout = 10 * 60 * 1000; // 10 min for large files + inference
    xhr.send(fd);
  });
}

// ── Render results ────────────────────────────────────────────────────────────
function rowHtml(name, value) {
  return `<div class="row-item"><span>${escapeHtml(name)}</span><strong>${escapeHtml(value)}</strong></div>`;
}

function renderBars(container, points, maxValue, kind) {
  container.innerHTML = "";
  if (!points?.length) { container.innerHTML = '<p class="small">No data.</p>'; return; }
  container.innerHTML = points.map((pt) => {
    const val     = Number.isFinite(Number(pt.value)) ? Number(pt.value) : 0;
    const pct     = Math.max(0, Math.min(100, (val / maxValue) * 100));
    const display = kind === "modality" ? `${(val * 100).toFixed(1)}%` : val.toFixed(2);
    return `
      <div class="bar-row">
        <div>
          <div class="bar-label">${escapeHtml(pt.label)}</div>
          <div class="bar-track"><div class="${kind === "modality" ? "bar-fill modality" : "bar-fill"}" style="width:${pct.toFixed(1)}%"></div></div>
        </div>
        <div class="bar-value">${display}</div>
      </div>`;
  }).join("");
}

function renderGuidance(summary) {
  guidanceList.innerHTML = `
    <div class="guidance-block">
      <p><strong>Strengths:</strong> ${escapeHtml((summary.strengths || []).join(", ") || "-")}</p>
      <p><strong>Weaknesses:</strong> ${escapeHtml((summary.weaknesses || []).join(", ") || "-")}</p>
      <p><strong>Suggestions:</strong> ${escapeHtml((summary.suggestions || []).join(", ") || "-")}</p>
    </div>`;
}

function renderSummary(summary) {
  const overall    = Number(summary.overall_score    || 0);
  const confidence = Number(summary.confidence_score || 0);
  summaryCard.innerHTML = `
    <h3>Overall Summary</h3>
    <div class="summary-score">
      <span>Score</span><strong>${overall.toFixed(2)}</strong><span>/ 10</span>
    </div>
    <p><strong>Language Detected:</strong> ${escapeHtml(summary.language_detected)}</p>
    <p><strong>Scoring Mode:</strong> ${escapeHtml(currentScoringMode || "unknown")}</p>
    <p><strong>Processing Option:</strong> ${escapeHtml(summary.processing_option || "unknown")}</p>
    <p><strong>Runtime:</strong> ${escapeHtml((summary.processing_notes || []).join(" | ") || "-")}</p>
    <span class="band-pill band-${escapeHtml(summary.investment_band)}">${escapeHtml(summary.investment_band)}</span>`;
  overallKpi.textContent    = `${overall.toFixed(2)} / 10`;
  confidenceKpi.textContent = `${confidence.toFixed(2)} / 10`;
  bandKpi.textContent       = summary.investment_band || "-";
}

function renderRisks(points) {
  riskDistribution.innerHTML = points?.length
    ? points.map((p) => rowHtml(p.label, String(p.value))).join("")
    : '<p class="small">No explicit risk flags detected.</p>';
}

function renderChunks(chunks) {
  if (!chunks?.length) { chunkReports.innerHTML = '<p class="small">No chunk reports.</p>'; return; }
  chunkReports.innerHTML = chunks.map((chunk) => {
    const risks = chunk.risk_flags?.length
      ? chunk.risk_flags.map((r) => `<span class="chip chip-risk">${escapeHtml(r)}</span>`).join("")
      : `<span class="chip">No risk flags</span>`;
    const textRows = (chunk.text_metrics || []).map((m) => rowHtml(m.name, Number(m.score || 0).toFixed(2))).join("");
    const avRows   = (chunk.av_metrics   || []).map((m) => rowHtml(m.name, Number(m.score || 0).toFixed(2))).join("");
    return `
      <article class="chunk-card">
        <div class="chunk-title">
          <h4>Chunk #${escapeHtml(String(chunk.chunk_id))}</h4>
          <span class="chunk-meta">${escapeHtml(String(chunk.start_sec))}s–${escapeHtml(String(chunk.end_sec))}s</span>
        </div>
        <p><strong>Aggregate:</strong> ${Number(chunk.aggregate_score || 0).toFixed(2)} &nbsp;|&nbsp;
           <strong>Attention:</strong> T ${Number(chunk.attention?.text   || 0).toFixed(2)} /
                                        V ${Number(chunk.attention?.visual || 0).toFixed(2)} /
                                        A ${Number(chunk.attention?.audio  || 0).toFixed(2)}</p>
        <div>${risks}</div>
        <details>
          <summary>Expand chunk metrics</summary>
          <div class="chunk-subgrid">
            <div class="list-card">${textRows || '<p class="small">No text metrics.</p>'}</div>
            <div class="list-card">${avRows   || '<p class="small">No AV metrics.</p>'}</div>
          </div>
        </details>
      </article>`;
  }).join("");
}

// ── Form submit ───────────────────────────────────────────────────────────────
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  if (!selectedFile) {
    setStatus("Please upload a video file first.", "error");
    return;
  }

  setLoading(true);
  setStatus("Uploading and evaluating…");
  renderPitchPreview(buildPreviewData());

  try {
    const result = await evaluateWithFile(selectedFile);

    renderSummary(result.summary || {});
    renderBars(quantScores,     result.dashboard?.quantitative_scores || [], 10, "score");
    renderBars(modalityWeights, result.dashboard?.modality_weights    || [],  1, "modality");
    renderRisks(result.dashboard?.risk_distribution || []);
    renderGuidance(result.summary || {});
    renderChunks(result.chunk_reports || []);
    rawJson.textContent = JSON.stringify(result, null, 2);

    const overall = Number(result.summary?.overall_score || 0);
    latestRating  = { score: overall.toFixed(2), band: result.summary?.investment_band || "-" };
    showRatingPanel(latestRating.score, latestRating.band);

    evaluationPlaceholder.classList.add("hidden");
    evaluationResults.classList.remove("hidden");
    setStatus("Evaluation complete.");
    evaluationResults.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    showError(err.message || "Something went wrong.");
    setStatus("Evaluation failed.", "error");
  } finally {
    setLoading(false);
  }
});

// ── Clear ─────────────────────────────────────────────────────────────────────
clearBtn.addEventListener("click", () => globalThis.location.reload());

// ── Purge data ────────────────────────────────────────────────────────────────
purgeBtn.addEventListener("click", async () => {
  if (!confirm("Delete all uploaded videos and server-side data? This cannot be undone.")) return;
  purgeBtn.disabled = true;
  try {
    const res  = await fetch("/purge", { method: "POST" });
    const data = await res.json();
    if (res.ok) {
      setStatus(`Purged ${data.deleted_files} file(s) (${formatBytes(data.freed_bytes)}).`);
    } else {
      setStatus(`Purge failed: ${data.detail || "unknown error"}`, "error");
    }
  } catch {
    setStatus("Purge request failed.", "error");
  } finally {
    purgeBtn.disabled = false;
  }
});

// ── Scoring mode badge ────────────────────────────────────────────────────────
function normalizeScoringMode(value) {
  return "neural-network";
}

function updateScoringModeBadge(mode) {
  currentScoringMode = "neural-network";
  modeBadge.textContent = `Scoring Mode: ${currentScoringMode}`;
  modeBadge.classList.toggle("is-neural", true);
}

async function loadScoringMode() {
  try {
    const res  = await fetch("/scoring-mode");
    const data = await res.json();
    updateScoringModeBadge(data.scoring_mode);
  } catch {
    updateScoringModeBadge("unknown");
  }
}

// ── Live preview on field input ───────────────────────────────────────────────
Object.values(fields).filter(Boolean).forEach((f) => {
  f.addEventListener("input", () => renderPitchPreview(buildPreviewData()));
});

// ── Init ──────────────────────────────────────────────────────────────────────
await loadScoringMode();
renderPitchPreview(buildPreviewData());
