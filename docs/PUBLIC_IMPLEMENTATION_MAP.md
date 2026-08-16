# Public Implementation Map

This map records how the public repository communicates private-system depth without copying private implementation. It was prepared from a read-only architectural review of the production codebase and its tests.

| System responsibility observed | Evidence safe to publish | Deliberately withheld |
|---|---|---|
| Request orchestration across many stages | Typed `PublicControlPlane` vertical slice and lifecycle events | Private orchestration source and stage policy |
| Capability and evidence-aware routing | Explained scores, exclusions, circuits and synthetic outcomes | Provider inventory, live weights, thresholds and evaluation records |
| Runtime compatibility and resilience | Neutral adapters, retryability, fallback, capacity and deadlines | Provider clients, credentials, quotas and operational configuration |
| Streaming liveness | Delta, heartbeat, inactivity and terminal-event contracts | Private transports, runtime clients and timeout values |
| Human approval for consequential work | Exact-action manifests, ownership binding, one claimant and replay tombstones | Application authorization schema and internal permission policy |
| Tool dispatch | Typed safe-local tool contracts behind manifest claims | Private tools, connectors, command surfaces and integration details |
| Multi-perspective review | Bounded rule-based creation, preservation, risk and verification findings | Private prompts, instructions, scoring and escalation policy |
| Projects, sessions and durable context | Tenant-scoped memory and checkpoint contracts | Database schema, retrieval policy and customer data |
| Task-state retrieval | Tenant-scoped vector-space and dimension contracts | Embedding models, production dimensions, thresholds and stored vectors |
| Artifact lifecycle | Content-addressed immutable references and tenant checks | Storage topology, signed access and retention configuration |
| Multi-agent/decomposed work | Validated DAG waves and dependency failure propagation | Private agent definitions, prompts and delegation heuristics |
| External interoperability | Neutral registered MCP/A2A capability envelopes | Endpoints, credentials, auth flow, transports and partner configuration |
| Observability and learning | Ordered events, attempts, verification and synthetic outcome counters | Private telemetry, traces, ratings and operational dashboards |
| Terminal correctness | One terminal event, no late transition, terminal manifest liveness | Internal recovery jobs and distributed coordination details |
| Browser product | Authentic website and product-tour links/captures | Authenticated bundles, routes and UI source |

## Why this is representative

The public code does not try to match private line count. It demonstrates the coupling points that create system complexity: identity flowing through state, authority and evidence; routing separated from action permission; failure changing future eligibility; approvals consumed exactly once; artifacts verified before completion; and dependency outcomes shaping downstream execution.

Those relationships are inspectable in source and enforced by the test suite. The larger private codebase remains necessary because real providers, persistence, streaming transports, APIs, product surfaces, integrations, deployment and operational recovery multiply each boundary. Those details stay private by design.

## Safe interpretation

Reviewers may treat this repository as evidence that the architecture has been understood and can be expressed as working software. They should not treat any public adapter name, score, threshold, review rule or storage mechanism as production configuration.
