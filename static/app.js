const askForm = document.getElementById("ask-form");
const askButton = document.getElementById("ask-button");
const answerBox = document.getElementById("answer-box");
const intentBadge = document.getElementById("intent-badge");
const confidenceBadge = document.getElementById("confidence-badge");
const routeBadge = document.getElementById("route-badge");
const sourcesList = document.getElementById("sources-list");

function escapeHtml(input) {
  return input
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function setBadgeState(el, label, tone) {
  el.textContent = label;
  el.className = "badge " + tone;
}

function renderSources(sources) {
  if (!sources || sources.length === 0) {
    sourcesList.innerHTML = '<li class="muted">No chunks retrieved.</li>';
    return;
  }

  sourcesList.innerHTML = sources
    .map((item) => {
      const page = item.page !== null && item.page !== undefined ? `page ${item.page}` : "page n/a";
      return `<li>${escapeHtml(item.source)} (${page}) distance=${Number(item.distance).toFixed(4)}</li>`;
    })
    .join("");
}

async function askAssistant(payload) {
  const response = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.detail || "Request failed");
  }

  return response.json();
}

function renderAnswer(data) {
  answerBox.textContent = data.final_response || "No response generated.";

  const confidence = Number(data.confidence || 0);
  const confidenceTone = confidence >= 0.55 ? "ok" : confidence >= 0.25 ? "warn" : "danger";
  setBadgeState(intentBadge, `Intent: ${data.intent || "unknown"}`, "neutral");
  setBadgeState(confidenceBadge, `Confidence: ${confidence.toFixed(2)}`, confidenceTone);

  if (data.escalate) {
    setBadgeState(routeBadge, "Route: Escalated", "danger");
  } else {
    setBadgeState(routeBadge, "Route: Auto Answer", "ok");
  }

  renderSources(data.sources || []);
}

askForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  askButton.disabled = true;
  askButton.textContent = "Running...";

  const formData = new FormData(askForm);
  const payload = {
    user_id: String(formData.get("user_id") || "web-user").trim(),
    query: String(formData.get("query") || "").trim(),
  };

  try {
    const data = await askAssistant(payload);
    renderAnswer(data);
  } catch (error) {
    answerBox.textContent = `Error: ${error.message}`;
    setBadgeState(routeBadge, "Route: Error", "danger");
  } finally {
    askButton.disabled = false;
    askButton.textContent = "Run Workflow";
  }
});
