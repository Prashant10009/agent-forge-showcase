import { buildSyntheticTrace, chooseDemoRoute, DEMO_NOTICE } from "../demo/engine.mjs";

const $ = (selector, scope = document) => scope.querySelector(selector);
const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];

const missionState = {
  running: false,
  approved: false,
  taskType: "audit"
};

function setStatus(message, tone = "neutral") {
  const status = $("#mission-status");
  status.textContent = message;
  status.dataset.tone = tone;
}

function renderTrace(activeIndex = -1) {
  const trace = buildSyntheticTrace(missionState.taskType);
  const list = $("#trace-list");
  list.innerHTML = trace.map((stage, index) => {
    const state = index < activeIndex ? "complete" : index === activeIndex ? "active" : "queued";
    return `
      <li class="trace-row" data-state="${state}">
        <span class="trace-node" aria-hidden="true"></span>
        <span class="trace-copy">
          <strong>${stage.label}</strong>
          <small>${stage.detail}</small>
        </span>
        <code>${stage.duration ? `${stage.duration} ms` : "gate"}</code>
      </li>`;
  }).join("");
}

function renderRoute() {
  const route = chooseDemoRoute(missionState.taskType);
  $("#route-model").textContent = route.selected;
  $("#route-confidence").textContent = `${Math.round(route.confidence * 100)}% fit`;
  $("#route-reason").textContent = route.reason;
}

function wait(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

async function runMission() {
  if (missionState.running) return;
  missionState.running = true;
  missionState.approved = false;
  $("#run-mission").disabled = true;
  $("#approval-panel").dataset.state = "locked";
  $("#approval-result").textContent = "Awaiting scoped action review.";
  setStatus("Mission running", "active");

  const trace = buildSyntheticTrace(missionState.taskType);
  for (let index = 0; index < trace.length - 1; index += 1) {
    renderTrace(index);
    await wait(index === 3 ? 620 : 420);
    if (index === 4) {
      $("#approval-panel").dataset.state = "ready";
      setStatus("Approval required", "warning");
      missionState.running = false;
      $("#run-mission").disabled = false;
      return;
    }
  }
}

async function approveMission() {
  if ($("#approval-panel").dataset.state !== "ready") return;
  missionState.approved = true;
  $("#approval-panel").dataset.state = "approved";
  $("#approval-result").textContent = "Approved demo manifest. Verification completed with no external writes.";
  renderTrace(5);
  setStatus("Verified result", "success");
  await wait(480);
  $$("#trace-list .trace-row").forEach((row) => row.dataset.state = "complete");
}

function rejectMission() {
  if ($("#approval-panel").dataset.state !== "ready") return;
  missionState.approved = false;
  $("#approval-panel").dataset.state = "rejected";
  $("#approval-result").textContent = "Rejected safely. No action executed.";
  setStatus("Stopped at policy boundary", "neutral");
}

function selectTab(button) {
  const tabName = button.dataset.tab;
  $$("[role='tab']").forEach((tab) => {
    const selected = tab === button;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
  });
  $$("[role='tabpanel']").forEach((panel) => {
    panel.hidden = panel.dataset.panel !== tabName;
  });
}

function initRevealObserver() {
  if (!("IntersectionObserver" in window) || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    $$("[data-reveal]").forEach((item) => item.dataset.revealed = "true");
    return;
  }
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.dataset.revealed = "true";
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.14 });
  $$("[data-reveal]").forEach((item) => observer.observe(item));
}

function init() {
  $("#demo-notice").textContent = DEMO_NOTICE;
  renderRoute();
  renderTrace();

  $("#run-mission").addEventListener("click", runMission);
  $("#approve-mission").addEventListener("click", approveMission);
  $("#reject-mission").addEventListener("click", rejectMission);

  $$("[role='tab']").forEach((tab) => {
    tab.addEventListener("click", () => selectTab(tab));
    tab.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
      const tabs = $$("[role='tab']");
      const index = tabs.indexOf(tab);
      const next = event.key === "ArrowRight" ? (index + 1) % tabs.length : (index - 1 + tabs.length) % tabs.length;
      tabs[next].focus();
      selectTab(tabs[next]);
    });
  });

  $("#year").textContent = String(new Date().getFullYear());
  initRevealObserver();
}

document.addEventListener("DOMContentLoaded", init);
