# Master Plan: GNPy Interactive Tutorial Web App

## Context

**Feature**: An interactive tutorial web application that explains and runs the functions of the GNPy optical network planning library, with a polished UI. This serves as a foundational step for improving the GNPy project and integrating it with future projects.

**Goals**:
1. Make GNPy accessible to new users through guided, interactive tutorials
2. Provide live, in-browser execution of GNPy simulations with visual results
3. Establish a modern web architecture that can evolve into a production tool
4. Create an API-first backend that enables future integrations

**Scope**: Tutorial-focused web app with read-only examples and parameter tweaking. NOT a full network design IDE (Phase 1).

---

## Phase 0: Prototype & Validation (1-2 weeks)

**Goal**: Validate the approach with a Streamlit prototype before committing to a full build.

| # | Task | Complexity | Notes |
|---|------|-----------|-------|
| 0.1 | Build Streamlit prototype with 2-3 basic tutorials | Medium | Wraps `worker_utils.designed_network()` and `transmission_simulation()` |
| 0.2 | Measure GNPy computation times for target examples | Low | Benchmark: edfa_example, meshTopologyExampleV2, multiband |
| 0.3 | Validate SimParams concurrency workaround | Medium | Test process isolation vs. deep-copy + thread-local |
| 0.4 | Evaluate user feedback on prototype | Low | Show to 2-3 target users, gather feedback |
| 0.5 | Go/no-go decision on custom web app | Low | If Streamlit suffices, stop here |

**Dependencies**: None (starting point)

---

## Phase 1: Backend Foundation (2-3 weeks)

**Goal**: FastAPI backend wrapping GNPy core functions with a stable API layer.

| # | Task | Complexity | Notes |
|---|------|-----------|-------|
| 1.1 | Set up monorepo structure (`/frontend`, `/backend`, Docker Compose) | Low | pnpm + pip/uv, development containers |
| 1.2 | Create FastAPI app with CORS, lifespan, OpenAPI docs | Low | Base scaffolding |
| 1.3 | Build GNPy Bridge Service (`gnpy_bridge.py`) | High | Adapter layer wrapping `worker_utils`, `json_io`, `network` functions |
| 1.4 | Implement session management (in-memory, TTL-based) | Medium | Isolate per-user GNPy state; deep-copy networks per request |
| 1.5 | Solve SimParams global state issue | High | Process-pool isolation or thread-local patching; CRITICAL for correctness |
| 1.6 | Build network API endpoints (load, build, design, topology) | Medium | `POST /api/network/load`, `GET /api/network/{id}/topology` |
| 1.7 | Build equipment API endpoints | Low | `GET /api/equipment/*`, `POST /api/equipment/load` |
| 1.8 | Build simulation API endpoints | Medium | `POST /api/simulate/transmission`, `POST /api/simulate/propagate` |
| 1.9 | Build serialization layer (numpy, networkx, SpectralInfo -> JSON) | Medium | Use `orjson` for performance; handle ndarray, DiGraph, element objects |
| 1.10 | Implement input validation with sane ranges | Medium | Prevent DoS: max topology size, max channels, computation timeout (60s) |
| 1.11 | Catch `sys.exit()` calls from GNPy CLI code | Low | Wrap in try/except or use `worker_utils` functions only |
| 1.12 | Backend API test suite | Medium | Tests for all endpoints with reference data from gnpy/example-data |

**Dependencies**: Phase 0 complete (go decision)

---

## Phase 2: Frontend Foundation (2-3 weeks)

**Goal**: React + TypeScript frontend with tutorial viewer, network graph, and basic charts.

| # | Task | Complexity | Notes |
|---|------|-----------|-------|
| 2.1 | Set up React + TypeScript + Vite project | Low | Tailwind CSS, Radix UI primitives |
| 2.2 | Implement Zustand stores (TutorialStore, NetworkStore, SimulationStore) | Medium | Type-safe stores matching backend API models |
| 2.3 | Build layout shell (sidebar, main content, inspector, console) | Medium | Desktop-first 3-column layout, responsive breakpoints |
| 2.4 | Build NetworkTopologyViewer (React Flow) | High | Custom node types per element, geo-positioned layout, click-to-inspect |
| 2.5 | Build SpectrumChart (Recharts) | Medium | Signal + ASE + NLI traces, per-channel tooltips |
| 2.6 | Build PropagationWaterfall chart | Medium | Power/GSNR along path with element markers |
| 2.7 | Build ResultsTable (sortable, filterable) | Low | Color-coded rows, CSV export |
| 2.8 | Build TutorialView (markdown renderer + interactive panels) | Medium | react-markdown + parameter forms + run button |
| 2.9 | Build EquipmentParameterEditor | High | Tree-structured form, validation, diff view |
| 2.10 | Build CodeSnippetPanel (read-only with syntax highlighting) | Low | Lazy-load react-syntax-highlighter |
| 2.11 | Build GlossaryTooltip system | Low | Hoverable terms with definitions |
| 2.12 | Implement routing (`/`, `/tutorial/:slug`, `/tutorial/:slug/step/:n`) | Low | React Router v6 |
| 2.13 | Frontend TypeScript types matching backend schemas | Medium | SimulationResult, PathElement, ChannelResult, etc. |
| 2.14 | Frontend component test suite (Vitest + Testing Library) | Medium | Render tests, interaction tests per UX analysis |

**Dependencies**: Phase 1 API endpoints available (tasks 1.6-1.8)

---

## Phase 3: Tutorial Content - Beginner Path (2 weeks)

**Goal**: 4 beginner tutorials with full interactivity.

| # | Task | Complexity | Notes |
|---|------|-----------|-------|
| 3.1 | Tutorial data structure (YAML/JSON schema for tutorials) | Medium | Steps: explanation, interactive, visualization, quiz |
| 3.2 | Tutorial step execution engine (backend) | Medium | Render templates with user params, execute GNPy calls, return viz data |
| 3.3 | Tutorial 01: "What is GNPy?" | Low | Overview, glossary, click-to-explore network diagram |
| 3.4 | Tutorial 02: "Your First Simulation" | Medium | Load edfa_example, run transmission, view GSNR results |
| 3.5 | Tutorial 03: "Understanding Equipment" | Medium | Equipment editor, parameter sliders, amplifier comparison |
| 3.6 | Tutorial 04: "Running End-to-End" | Medium | Full workflow: load -> design -> propagate -> results |
| 3.7 | Integration tests: tutorial flow matches CLI output | Medium | Reference values from GNPy CLI for each tutorial |

**Dependencies**: Phase 2 components (2.4-2.8 specifically)

---

## Phase 4: Rich Interactivity (2-3 weeks)

**Goal**: Step-through propagation, WebSocket for live updates, intermediate tutorials.

| # | Task | Complexity | Notes |
|---|------|-----------|-------|
| 4.1 | WebSocket endpoint for streaming propagation | Medium | Per-element SpectralInformation snapshots |
| 4.2 | PropagationTimeline component (play/pause/step) | High | Animated signal flow, element-by-element inspection |
| 4.3 | Live preview with debounced re-simulation | Medium | 300ms debounce, cancel in-flight requests |
| 4.4 | "Pin & Compare" for result snapshots | Medium | Keep previous results for side-by-side comparison |
| 4.5 | Tutorial 05: "Signal Propagation Deep Dive" | High | Step-through propagation, per-element metrics |
| 4.6 | Tutorial 06: "Network Topologies" | Medium | Mesh topology (meshTopologyExampleV2), path computation, map view |
| 4.7 | Tutorial 07: "Service Requests & Path Planning" | Medium | Path requests, results table, spectrum assignment |
| 4.8 | Tutorial 08: "Autodesign & Amplifier Selection" | Medium | Before/after network comparison |
| 4.9 | AmplifierCurveChart (NF vs Gain) | Low | Per amplifier type_variety |
| 4.10 | NetworkDiffViewer (before/after autodesign) | Medium | Highlight added elements |

**Dependencies**: Phase 3 complete

---

## Phase 5: Advanced Topics & Playground (3-4 weeks)

**Goal**: Advanced tutorials, free-form experimentation, and production readiness.

| # | Task | Complexity | Notes |
|---|------|-----------|-------|
| 5.1 | Playground mode (free-form simulation without tutorial) | High | Topology selection, parameter editing, simulation runner |
| 5.2 | SpectrumAssignmentViewer (bitmap visualization) | Medium | FREE/OCCUPIED/UNUSABLE slots |
| 5.3 | Tutorial 09: "Advanced Impairments & Raman" | High | Raman toggle, solver comparison, power profiles |
| 5.4 | Tutorial 10: "Multiband & Custom Spectra" | Medium | C+L band, mixed-rate spectrum |
| 5.5 | Tutorial 11: "From Tutorial to Production" | Low | XLS conversion, API integration patterns |
| 5.6 | File upload (topology JSON/XLS, equipment, services) | Medium | Drag-and-drop, validation before processing |
| 5.7 | Export features (CSV, JSON, SVG/PNG) | Low | Download results, network diagrams |
| 5.8 | Accessibility audit (WCAG 2.1 AA) | Medium | Color contrast, keyboard nav, screen reader, reduced motion |
| 5.9 | Performance optimization | Medium | Code splitting, lazy loading, caching |
| 5.10 | Docker production deployment | Medium | Multi-stage build, nginx frontend, uvicorn backend |
| 5.11 | Documentation (README, API docs, contributing guide) | Low | Auto-generated OpenAPI + deployment guide |

**Dependencies**: Phase 4 complete

---

## Dependency Graph

```
Phase 0 (Prototype)
    |
    v
Phase 1 (Backend) ──────> Phase 2 (Frontend)
    |                           |
    v                           v
    +----------> Phase 3 (Beginner Tutorials) <---------+
                       |
                       v
                Phase 4 (Rich Interactivity)
                       |
                       v
                Phase 5 (Advanced + Playground)
```

- Phase 1 and Phase 2 can overlap once API endpoints (1.6-1.8) are available
- Phase 3 depends on both Phase 1 (backend API) and Phase 2 (frontend components)
- Phases 4 and 5 are strictly sequential after Phase 3

---

## Test Plan

### Unit Tests
- **Backend API**: All endpoints tested with reference data from `gnpy/example-data/`
- **GNPy Bridge**: Serialization roundtrips, session isolation, error handling
- **Frontend Components**: Render tests and interaction tests per UX analysis (37 tests specified)
- **Stores**: Zustand store state transitions, API integration, error handling

### Integration Tests
- **Tutorial Flow**: Each tutorial step produces results matching GNPy CLI reference values
- **End-to-End Transmission**: Load example -> simulate -> verify GSNR matches CLI
- **Parameter Changes**: Modify equipment -> re-simulate -> verify results change correctly
- **File Upload**: Upload XLS -> convert -> render -> simulate

### Edge Case Tests (from Devil's Advocate)
- **Input Validation**: Empty topology, single node, disconnected graph, duplicate UIDs, invalid references
- **Computation Boundaries**: Raman convergence, large networks, high channel count, extreme parameters
- **Concurrency**: SimParams isolation, network object isolation, request cancellation
- **Error Handling**: Each GNPy exception type maps to correct HTTP error

### Accessibility Tests
- WCAG 2.1 AA color contrast on all visualizations
- Keyboard navigation for all interactive elements
- Screen reader compatibility for charts and tables
- `prefers-reduced-motion` respected for animations

### Performance Tests
- Backend computation time benchmarks for target examples
- Frontend rendering performance for large networks (75+ nodes)
- Serialization performance for large result sets
- WebSocket latency for live propagation updates

---

## Risk Register

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|------------|------------|
| 1 | **SimParams global state breaks concurrent users** | Critical | Certain | Use process-pool isolation (multiprocessing); each simulation runs in a separate process with its own SimParams state |
| 2 | **DoS via expensive computation inputs** | Critical | High | Input validation (max topology size, max channels), hard computation timeout (60s), memory limits (2GB per process), rate limiting |
| 3 | **Scope creep from tutorial to IDE** | High | High | Strict Phase 1 scope: read-only examples + parameter sliders. No topology editing. Clear "not in scope" document. Phase 0 prototype forces scope clarity |
| 4 | **Memory exhaustion from Raman solver** | High | Medium | Limit spatial resolution in tutorials, pre-compute Raman results for advanced tutorials, memory monitoring with process-level limits |
| 5 | **sys.exit() in GNPy CLI kills web server** | High | Certain | Never import CLI functions directly; use only `worker_utils` functions. Wrap all GNPy calls in try/except catching SystemExit |
| 6 | **GNPy version update breaks web app** | Medium | Certain (long-term) | Stable adapter layer, version-pinned GNPy, automated regression tests comparing web vs CLI output |
| 7 | **Complex validation hard to surface in UI** | Medium | High | Backend validation API returns structured errors; frontend shows inline errors per field; progressive disclosure of advanced options |
| 8 | **Dual codebase maintenance burden** | Medium | Certain (long-term) | Thin adapter layer, automated integration tests, Docker-based deployment, clear documentation |
| 9 | **matplotlib dependency issues on server** | Medium | Medium | Eliminate matplotlib from web app; all visualization is frontend-side using Recharts/React Flow |
| 10 | **Numerical accuracy differences web vs CLI** | Low | Medium | Reference value regression tests; pin numpy/scipy versions; same computation code path |

---

## Technology Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Frontend framework | React 18 + TypeScript + Vite | Ecosystem maturity, TypeScript safety, fast dev builds |
| Styling | Tailwind CSS + Radix UI | Utility-first CSS, accessible primitives |
| State management | Zustand | Lightweight, minimal boilerplate |
| Network visualization | React Flow | Built-in pan/zoom, custom nodes, good React integration |
| Charts | Recharts | React-native, tree-shakeable, good TypeScript support |
| Backend framework | FastAPI (Python 3.10+) | Native async, auto-OpenAPI, Pydantic validation, same Python as GNPy |
| Communication | REST + WebSocket | REST for request/response, WebSocket for live propagation streaming |
| Concurrency | Process pool | Required for SimParams isolation and GIL avoidance |
| Serialization | orjson | 10-50x faster than stdlib json for numpy arrays |
| Containerization | Docker Compose | Isolate Python dependencies, reproducible builds |

---

## References

### Analysis Files
- [UX Analysis](./ux-analysis.md) - User personas, tutorial flow, UI components, interaction patterns, a11y, responsive design, test suggestions
- [Technical Architecture](./tech-architecture.md) - Tech stack, backend/frontend architecture, GNPy integration, data models, performance, tests
- [Devil's Advocate Review](./devils-advocate.md) - Risks, edge cases, alternatives, security, scalability, maintenance concerns

### Key Source Files
- `gnpy/core/elements.py` - Network element classes (1,827 lines)
- `gnpy/core/network.py` - Network building and auto-design (2,168 lines)
- `gnpy/core/parameters.py` - Simulation parameters, SimParams global state
- `gnpy/core/science_utils.py` - NLI solver, Raman solver
- `gnpy/core/info.py` - SpectralInformation, Channel, Carrier
- `gnpy/tools/worker_utils.py` - High-level API: designed_network(), transmission_simulation(), planning()
- `gnpy/tools/json_io.py` - JSON loading and serialization
- `gnpy/tools/cli_examples.py` - CLI entry points (reference workflows)
- `gnpy/tools/plots.py` - matplotlib plotting (reference for web visualizations)
- `gnpy/topology/request.py` - Path computation and service requests
- `gnpy/topology/spectrum_assignment.py` - Spectrum assignment algorithms
- `gnpy/example-data/` - Sample networks, equipment configs, service requests
