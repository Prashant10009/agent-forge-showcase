export const DEMO_NOTICE = "Synthetic portfolio simulation — no production data or provider calls.";

const ROUTES = Object.freeze({
  audit: {
    selected: "reasoning-core",
    confidence: 0.93,
    reason: "Repository-scale reasoning with a review boundary."
  },
  build: {
    selected: "code-specialist",
    confidence: 0.89,
    reason: "Implementation-heavy task with deterministic verification."
  },
  research: {
    selected: "research-core",
    confidence: 0.86,
    reason: "Source synthesis with citation and uncertainty requirements."
  }
});

export function chooseDemoRoute(taskType = "audit") {
  const key = Object.hasOwn(ROUTES, taskType) ? taskType : "audit";
  return { taskType: key, ...ROUTES[key] };
}

export function buildSyntheticTrace(taskType = "audit") {
  const route = chooseDemoRoute(taskType);
  return [
    { id: "intent", label: "Intent classified", detail: taskType, duration: 18 },
    { id: "context", label: "Context assembled", detail: "4 public-safe signals", duration: 41 },
    { id: "route", label: "Model route selected", detail: route.selected, duration: 27 },
    { id: "tools", label: "Read-only tools scoped", detail: "2 approved actions", duration: 122 },
    { id: "approval", label: "Human boundary reached", detail: "review required", duration: 0 },
    { id: "verify", label: "Verification queued", detail: "tests + diff", duration: 0 }
  ];
}

export function publicBoundarySummary() {
  return {
    included: ["Synthetic UX", "System architecture", "Public-safe interfaces", "Verification examples"],
    excluded: ["Production source", "Routing weights", "Private prompts", "Customer or runtime data"]
  };
}
