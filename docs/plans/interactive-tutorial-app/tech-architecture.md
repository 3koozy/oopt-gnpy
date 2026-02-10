# Technical Architecture: GNPy Interactive Tutorial App

## 1. Technology Stack

### Frontend
- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite (fast HMR, optimized production builds)
- **Styling**: Tailwind CSS + component library (Radix UI for accessible primitives)
- **State Management**: Zustand (lightweight, minimal boilerplate vs Redux)
- **Routing**: React Router v6 (tutorial navigation, deep-linking to lessons)

### Backend
- **Framework**: FastAPI (Python 3.10+) -- native async, automatic OpenAPI docs, Pydantic validation
- **GNPy Integration**: Direct import of GNPy modules (same Python environment)
- **Task Queue**: None initially; use FastAPI background tasks for simulations under 30s. Add Celery + Redis only if long-running Raman simulations require it.

### Communication
- **Primary**: REST API (JSON) for request/response patterns (load topology, get equipment, run simulation)
- **Secondary**: WebSocket (via FastAPI WebSockets) for streaming simulation progress and live propagation step results
- **API Docs**: Auto-generated Swagger UI at `/docs` from FastAPI

### Development
- **Monorepo**: Single repository with `/frontend` and `/backend` directories
- **Package Manager**: pnpm (frontend), pip/uv (backend)
- **Containerization**: Docker Compose for local dev (frontend + backend + optional Redis)

---

## 2. Backend Architecture

### 2.1 Project Structure

```
backend/
  app/
    main.py              # FastAPI app, CORS, lifespan
    api/
      network.py         # Network topology endpoints
      equipment.py       # Equipment library endpoints
      simulation.py      # Propagation & simulation endpoints
      path.py            # Path computation endpoints
      spectrum.py        # Spectrum assignment endpoints
      tutorial.py        # Tutorial content & progress endpoints
    services/
      gnpy_bridge.py     # Wrapper around GNPy core functions
      network_builder.py # Network construction from JSON
      simulation_runner.py  # Propagation execution
      path_computer.py   # Path computation logic
    models/
      schemas.py         # Pydantic request/response models
      topology.py        # Network topology models
      results.py         # Simulation result models
    ws/
      simulation_ws.py   # WebSocket handlers for live results
    utils/
      serialization.py   # NumPy/GNPy object serialization
```

### 2.2 Key API Endpoints

#### Network Management
```
POST   /api/network/load          # Load network from JSON topology
POST   /api/network/build         # Build network from scratch (elements + connections)
GET    /api/network/{id}          # Get current network state
POST   /api/network/{id}/design   # Run auto-design (add_missing_elements_in_network + design_network)
GET    /api/network/{id}/topology # Get network graph (nodes + edges for visualization)
POST   /api/network/{id}/save     # Export designed network as JSON
```

#### Equipment Library
```
GET    /api/equipment                    # List all equipment categories
GET    /api/equipment/edfa               # List amplifier types
GET    /api/equipment/fiber              # List fiber types
GET    /api/equipment/roadm              # List ROADM types
GET    /api/equipment/transceiver        # List transceiver types + modes
GET    /api/equipment/si                 # Get Spectral Information defaults
POST   /api/equipment/load              # Load custom equipment config
```

#### Simulation
```
POST   /api/simulate/transmission       # Single transmission (wraps transmission_simulation)
POST   /api/simulate/propagate          # Propagate signal on a path
POST   /api/simulate/path-request       # Multi-service path computation (wraps planning)
WS     /ws/simulate/transmission        # WebSocket for live propagation updates
```

#### Spectrum Assignment
```
POST   /api/spectrum/assign             # Run spectrum assignment on computed paths
GET    /api/spectrum/oms/{id}            # Get OMS bitmap state
```

#### Tutorial
```
GET    /api/tutorials                    # List available tutorials
GET    /api/tutorials/{slug}             # Get tutorial content + steps
POST   /api/tutorials/{slug}/run-step   # Execute a tutorial step's code
```

### 2.3 GNPy Bridge Service

The central integration layer that wraps GNPy functions. Key mappings:

| Tutorial Feature | GNPy Function | Module |
|---|---|---|
| Load Equipment | `load_equipments_and_configs()` | `gnpy.tools.json_io` |
| Load Network | `load_network()` | `gnpy.tools.json_io` |
| Auto-Design | `add_missing_elements_in_network()`, `design_network()` | `gnpy.core.network` |
| Build Spectrum | `create_input_spectral_information()` | `gnpy.core.info` |
| Compute Path | `compute_constrained_path()` | `gnpy.topology.request` |
| Propagate Signal | `propagate()` | `gnpy.topology.request` |
| Full Transmission | `designed_network()`, `transmission_simulation()` | `gnpy.tools.worker_utils` |
| Path Planning | `planning()` | `gnpy.tools.worker_utils` |
| Spectrum Assignment | `build_oms_list()`, `pth_assign_spectrum()` | `gnpy.topology.spectrum_assignment` |
| Select Amplifier | `select_edfa()` | `gnpy.core.network` |
| Calculate NF | `edfa_nf()` | `gnpy.core.network` |

### 2.4 Session Management

Each user session maintains an isolated GNPy state:

```python
class SimulationSession:
    session_id: str
    equipment: dict          # Loaded equipment library
    network: DiGraph         # Current network graph
    sim_params: SimParams    # Simulation parameters
    results: dict            # Cached results keyed by run_id
    created_at: datetime
    last_accessed: datetime
```

Sessions are stored in-memory with TTL-based eviction (30 min default). No persistent database needed for the tutorial use case.

---

## 3. Data Models (JSON Schemas)

### 3.1 Network Topology (mirrors GNPy's native format)

The app reuses GNPy's existing JSON format for network topology. This is the format used in `gnpy/example-data/`:

```json
{
  "network_name": "string",
  "elements": [
    {
      "uid": "string",
      "type": "Transceiver | Fiber | Edfa | Roadm | Fused | RamanFiber",
      "type_variety": "string (references equipment library)",
      "params": { },
      "operational": { "gain_target": 0, "tilt_target": 0, "out_voa": 0 },
      "metadata": {
        "location": {
          "city": "string",
          "region": "string",
          "latitude": 0.0,
          "longitude": 0.0
        }
      }
    }
  ],
  "connections": [
    { "from_node": "uid", "to_node": "uid" }
  ]
}
```

**Element-specific params** (based on actual GNPy classes):

- **Fiber**: `{ length, loss_coef, length_units, att_in, con_in, con_out, pmd_coef }`
- **Edfa**: operational `{ gain_target, tilt_target, out_voa }`, type_variety references equipment library
- **Roadm**: `{ target_pch_out_db | target_psd_out_mWperGHz | target_out_mWperSlotWidth, restrictions, add_drop_osnr, pmd, pdl }`
- **Fused**: `{ loss }`
- **Transceiver**: minimal (metadata only, modes from equipment library)

### 3.2 Equipment Configuration (mirrors GNPy eqpt_config.json)

Reuses GNPy's equipment config schema directly. Key sections:
- `Edfa[]`: amplifier definitions (type_variety, type_def, gain ranges, NF models)
- `Fiber[]`: fiber types (dispersion, effective_area, pmd_coef)
- `Roadm[]`: ROADM specs (equalization targets, OSNR, restrictions)
- `Transceiver[]`: transceiver modes (baud_rate, bit_rate, OSNR, penalties)
- `SI`: Spectral Information defaults (f_min, f_max, spacing, power_dbm, roll_off)
- `Span`: span simulation defaults (power_mode, max_length, delta_power_range_db)

### 3.3 Simulation Results (API response models)

```typescript
// Frontend TypeScript types

interface SimulationResult {
  run_id: string;
  source: string;
  destination: string;
  path: PathElement[];
  summary: {
    total_length_km: number;
    num_spans: number;
    final_gsnr_db: number;        // mean GSNR (0.1nm)
    final_osnr_ase_db: number;    // mean OSNR ASE (0.1nm)
  };
  per_channel: ChannelResult[];
  power_sweep?: PowerSweepResult[];
}

interface PathElement {
  uid: string;
  type: 'Transceiver' | 'Fiber' | 'Edfa' | 'Roadm' | 'Fused' | 'RamanFiber';
  type_variety?: string;
  // Per-element metrics (from element.__str__() output)
  metrics: {
    loss_db?: number;
    gain_db?: number;
    noise_figure_db?: number;
    pch_out_dbm?: number;
    osnr_ase_01nm?: number;
    gsnr_01nm?: number;
    chromatic_dispersion_ps_nm?: number;
    pmd_ps?: number;
    pdl_db?: number;
    latency_ms?: number;
  };
  location?: { lat: number; lng: number; city?: string };
}

interface ChannelResult {
  channel_number: number;
  frequency_thz: number;
  power_dbm: number;
  osnr_ase_db: number;
  snr_nli_db: number;
  gsnr_db: number;
}

interface SpectralInformationSnapshot {
  // Captures SpectralInformation state at any point in the path
  frequencies: number[];
  signal_dbm: number[];
  ase_dbm: number[];
  nli_dbm: number[];
  gsnr_db: number[];
  osnr_db: number[];
}
```

### 3.4 Serialization Strategy

GNPy objects use NumPy arrays extensively. The serialization layer in `utils/serialization.py` handles:

- `numpy.ndarray` -> JSON lists (with rounding to 6 decimal places)
- `networkx.DiGraph` -> `{ nodes: [...], edges: [...] }` with node attributes
- GNPy element objects -> dictionaries via their existing `.to_json` properties
- `SpectralInformation` -> snapshot dict via custom serializer accessing `.carriers` property

---

## 4. Frontend Architecture

### 4.1 Component Hierarchy

```
App
  Layout
    Sidebar (tutorial navigation, lesson list)
    MainContent
      TutorialView
        LessonHeader (title, progress, description)
        ContentBlocks[] (markdown text, diagrams, callouts)
        InteractivePanel
          CodeEditor (read-only GNPy code snippets + parameter inputs)
          ParameterForm (sliders, inputs for simulation params)
          RunButton + StatusIndicator
        ResultsPanel
          NetworkGraph (D3/React Flow topology visualization)
          SpectrumChart (Recharts for optical spectrum)
          MetricsTable (per-element or per-channel results)
          PathView (step-by-step propagation with metrics)
      Playground (free-form experimentation mode)
        TopologyEditor (drag-and-drop network builder)
        EquipmentBrowser (browse/select equipment library)
        SimulationRunner (configure and run custom simulations)
```

### 4.2 State Management (Zustand)

```typescript
// Core stores

interface TutorialStore {
  tutorials: Tutorial[];
  currentTutorial: string | null;
  currentStep: number;
  completedSteps: Set<string>;
  // actions
  loadTutorials: () => Promise<void>;
  setStep: (step: number) => void;
  markComplete: (stepId: string) => void;
}

interface NetworkStore {
  sessionId: string | null;
  topology: NetworkTopology | null;
  equipment: EquipmentConfig | null;
  selectedElement: string | null;
  // actions
  loadNetwork: (topology: object) => Promise<void>;
  loadEquipment: (config: object) => Promise<void>;
  selectElement: (uid: string) => void;
  runAutoDesign: () => Promise<void>;
}

interface SimulationStore {
  isRunning: boolean;
  progress: number;  // 0-100 for WebSocket updates
  results: SimulationResult | null;
  pathSnapshots: SpectralInformationSnapshot[];  // per-element snapshots
  // actions
  runTransmission: (params: TransmissionParams) => Promise<void>;
  runPathRequest: (params: PathRequestParams) => Promise<void>;
  clearResults: () => void;
}
```

### 4.3 Routing

```
/                           # Landing page, tutorial overview
/tutorial/:slug             # Tutorial view (lesson content + interactive)
/tutorial/:slug/step/:n     # Deep link to specific step
/playground                 # Free-form experimentation
/playground/network         # Network topology editor
/playground/simulate        # Simulation runner
/docs                       # API documentation / reference
```

---

## 5. Key GNPy Integration Points

### 5.1 Network Building Pipeline

The core workflow mirrors `cli_examples.py:transmission_main_example()`:

```
1. load_equipments_and_configs(eqpt_file)     -> equipment dict
2. load_network(topology_file, equipment)       -> networkx.DiGraph
3. add_missing_elements_in_network(network, equipment)  -> inserts EDFAs
4. design_network(ref_channel, network, equipment)      -> sets gains, powers
5. compute_constrained_path(network, request)  -> ordered path list
6. propagate(path, request, equipment)          -> SpectralInformation
```

Each step is exposed as a separate API endpoint AND as a tutorial step, so users can see intermediate states.

### 5.2 Functions to Expose

**Tier 1 -- Core tutorial functions (must have):**

| Function | Purpose | Tutorial Use |
|---|---|---|
| `load_network()` | Parse topology JSON into DiGraph | "Building Your First Network" |
| `create_input_spectral_information()` | Create WDM signal comb | "Understanding Optical Signals" |
| `add_missing_elements_in_network()` | Auto-insert amplifiers | "Network Auto-Design" |
| `design_network()` | Set amplifier gains and powers | "Network Auto-Design" |
| `compute_constrained_path()` | Dijkstra path with constraints | "Path Computation" |
| `propagate()` | Signal propagation through path | "Signal Propagation" |
| `transmission_simulation()` | Full transmission with power sweep | "End-to-End Simulation" |

**Tier 2 -- Advanced tutorial functions:**

| Function | Purpose | Tutorial Use |
|---|---|---|
| `planning()` | Multi-request path planning | "Service Planning" |
| `select_edfa()` | Amplifier selection algorithm | "Amplifier Selection Deep Dive" |
| `edfa_nf()` | Noise figure calculation | "Understanding Noise" |
| `build_oms_list()` + `pth_assign_spectrum()` | Spectrum assignment | "Spectrum Management" |
| `Fiber.propagate()` | Individual fiber propagation | "Fiber Physics" |
| `Roadm.propagate()` | ROADM equalization behavior | "ROADM Equalization" |
| `Edfa.__call__()` | Amplifier signal processing | "Amplifier Behavior" |

**Tier 3 -- Expert/reference functions:**

| Function | Purpose |
|---|---|
| `RamanSolver.calculate_stimulated_raman_scattering()` | Raman effect simulation |
| `NliSolver` | Nonlinear interference computation |
| `estimate_srs_power_deviation()` | SRS tilt estimation |
| `_spectrum_from_json()` | Mixed-rate spectrum definition |

### 5.3 Element Class Hierarchy (for frontend type system)

Based on `gnpy/core/elements.py`:

```
_Node (base)
  Transceiver     -- signal source/sink, computes SNR/OSNR
  Roadm           -- reconfigurable add-drop mux, power equalization
  Fused           -- passive coupler/splitter (fixed loss)
  Fiber           -- optical fiber (loss, dispersion, NLI)
    RamanFiber    -- fiber with Raman amplification
  Edfa            -- erbium-doped fiber amplifier (gain, noise figure)
    Multiband_amplifier  -- multi-band amplifier wrapper
```

All elements implement `__call__(spectral_info)` which propagates signal through the element. This uniform interface is key for the step-by-step propagation visualization.

---

## 6. Tutorial Module System

### 6.1 Tutorial Data Structure

Tutorials are defined as YAML/JSON files that combine explanation, interactive code, and visualization:

```yaml
# tutorials/01-first-network.yaml
slug: first-network
title: "Building Your First Optical Network"
description: "Learn how to define network elements and connect them"
difficulty: beginner
estimated_time: 15
prerequisites: []

steps:
  - id: intro
    type: explanation
    content: |
      An optical network in GNPy consists of **elements** connected by
      **links**. Elements include transceivers, fibers, amplifiers, and ROADMs.

  - id: define-elements
    type: interactive
    content: |
      Let's define a simple point-to-point network with two transceivers
      connected by a fiber span and an amplifier.
    code_template: |
      # This is the network topology in GNPy's JSON format
      topology = {
        "network_name": "My First Network",
        "elements": [
          {"uid": "Site_A", "type": "Transceiver"},
          {"uid": "Span1", "type": "Fiber", "type_variety": "SSMF",
           "params": {"length": {{fiber_length}}, "loss_coef": {{loss_coef}},
                      "length_units": "km"}},
          {"uid": "Amp1", "type": "Edfa", "type_variety": "std_low_gain"},
          {"uid": "Site_B", "type": "Transceiver"}
        ],
        "connections": [
          {"from_node": "Site_A", "to_node": "Span1"},
          {"from_node": "Span1", "to_node": "Amp1"},
          {"from_node": "Amp1", "to_node": "Site_B"}
        ]
      }
    parameters:
      - name: fiber_length
        label: "Fiber Length (km)"
        type: slider
        min: 10
        max: 200
        default: 80
        step: 5
      - name: loss_coef
        label: "Loss Coefficient (dB/km)"
        type: slider
        min: 0.15
        max: 0.35
        default: 0.2
        step: 0.01
    api_call:
      endpoint: POST /api/network/load
      body_from: code_template
    visualization:
      type: network-graph
      highlight: ["Span1"]

  - id: view-results
    type: visualization
    content: |
      The network has been loaded. Notice the fiber span properties
      and how the total loss depends on length and loss coefficient.
    visualization:
      type: element-details
      element: "Span1"
      show: [length, loss, connector_losses]

  - id: quiz
    type: quiz
    question: "If you increase the fiber length from 80km to 120km with 0.2 dB/km loss, what is the approximate total fiber loss?"
    options: ["16 dB", "24 dB", "32 dB"]
    correct: 1
    explanation: "Total loss = length x loss_coef = 120 x 0.2 = 24 dB (plus connector losses)"
```

### 6.2 Tutorial Content Architecture

Tutorials are organized into learning paths:

```
Beginner Path:
  01. What is GNPy? (overview, concepts)
  02. Building Your First Network (topology, elements)
  03. Understanding Optical Signals (SpectralInformation, channels)
  04. Running a Simulation (end-to-end transmission)

Intermediate Path:
  05. Network Auto-Design (EDFA insertion, gain setting)
  06. Fiber Physics (loss, dispersion, nonlinear effects)
  07. Amplifier Deep Dive (NF models, gain ranges, selection)
  08. ROADM Behavior (equalization, add/drop OSNR)
  09. Path Computation (Dijkstra, constraints, loose/strict)
  10. Understanding Results (OSNR, GSNR, penalties)

Advanced Path:
  11. Multi-Service Planning (path requests, disjunction)
  12. Spectrum Assignment (bitmap, first-fit)
  13. Mixed-Rate Spectrum (multiple baud rates)
  14. Raman Amplification (RamanFiber, SRS)
  15. Multiband Systems (C+L band)
  16. Power Sweep Analysis (optimization)
```

### 6.3 Step Execution Engine

The backend tutorial runner processes each step type:

```python
class TutorialStepRunner:
    async def run_step(self, session: SimulationSession, step: TutorialStep,
                       user_params: dict) -> StepResult:
        # 1. Render code template with user parameters
        rendered_code = step.render_template(user_params)

        # 2. Execute the corresponding GNPy operation
        if step.api_call:
            result = await self.execute_api_call(session, step.api_call, rendered_code)

        # 3. Extract visualization data from results
        viz_data = self.extract_visualization(result, step.visualization)

        # 4. Return enriched result
        return StepResult(
            code=rendered_code,
            result=result,
            visualization=viz_data,
            next_step=step.next
        )
```

---

## 7. Visualization Strategy

### 7.1 Network Topology Graph

**Library**: React Flow (react-flow-renderer)
- Better suited than raw D3 for interactive node-based graphs
- Built-in pan/zoom, node dragging, edge routing
- Custom node components for each element type (Transceiver, Fiber, Edfa, Roadm, Fused)

**Data mapping** (from GNPy's networkx DiGraph):
```typescript
// Convert GNPy network to React Flow format
function networkToReactFlow(topology: NetworkTopology): { nodes: Node[], edges: Edge[] } {
  return {
    nodes: topology.elements.map(el => ({
      id: el.uid,
      type: el.type.toLowerCase(),     // custom node component
      position: { x: el.metadata.location.longitude * scale,
                  y: -el.metadata.location.latitude * scale },
      data: {
        label: el.uid,
        type_variety: el.type_variety,
        metrics: el.metrics,           // populated after simulation
        isOnPath: false                // highlighted during propagation
      }
    })),
    edges: topology.connections.map(conn => ({
      id: `${conn.from_node}-${conn.to_node}`,
      source: conn.from_node,
      target: conn.to_node,
      animated: false                  // animated during propagation
    }))
  };
}
```

**Custom node icons**: Each element type gets a distinct SVG icon:
- Transceiver: antenna/server icon
- Fiber: wavy line
- Edfa: triangle (amplifier symbol)
- Roadm: diamond with arrows
- Fused: Y-junction

**Interaction**: Click a node to see its properties in a detail panel. During propagation, edges animate to show signal flow, and nodes display live metrics.

### 7.2 Optical Spectrum Charts

**Library**: Recharts (built on D3, React-native components, good TypeScript support)

**Chart types needed**:

1. **Power Spectrum** (signal + ASE + NLI vs frequency)
   - X-axis: Frequency (THz) or Channel Number
   - Y-axis: Power (dBm)
   - Three traces: signal, ASE noise, NLI noise
   - Tooltip shows per-channel values

2. **OSNR/GSNR Profile** (per channel across frequency)
   - X-axis: Frequency (THz)
   - Y-axis: dB
   - Lines for OSNR ASE, SNR NLI, GSNR
   - Horizontal threshold line for required OSNR

3. **Power Along Path** (signal power at each element)
   - X-axis: Element index or cumulative distance
   - Y-axis: Power (dBm)
   - Shows loss in fibers, gain in EDFAs, equalization in ROADMs
   - Color-coded by element type

4. **Spectrum Bitmap** (for spectrum assignment)
   - Grid visualization: frequency slots vs OMS
   - Color: free (green), occupied (red), unusable (gray)

### 7.3 Propagation Animation

For the "step-by-step propagation" tutorial feature:

1. Backend returns `SpectralInformation` snapshot at each element boundary
2. Frontend stores snapshots in `SimulationStore.pathSnapshots[]`
3. A timeline slider lets users scrub through the propagation
4. Network graph highlights the current element
5. Spectrum chart updates to show the signal state at that point
6. Metrics panel shows the current element's contribution (loss, gain, NF, etc.)

This is the most impactful visualization for learning -- seeing how the signal degrades element by element.

---

## 8. Performance Considerations

### 8.1 Server-Side Computation

All GNPy computations run on the Python backend. The frontend never executes GNPy code. This is critical because:
- GNPy depends on NumPy, SciPy, NetworkX (cannot run in browser)
- Simulations are CPU-bound (NLI solver, Raman solver)
- Equipment library and network state are server-side

**Typical computation times** (estimated from code analysis):
- Simple network load: < 100ms
- Auto-design (small network): 200-500ms
- Single propagation (no Raman): 500ms - 2s
- Raman propagation: 5-30s (depends on spatial resolution)
- Multi-service planning (10 requests): 2-10s
- Power sweep (10 steps): 5-20s

### 8.2 Caching Strategy

```python
# In-memory cache for expensive computations
class ResultCache:
    # Equipment library: cached per config hash (loaded once per session)
    equipment_cache: dict[str, dict]

    # Network design: cached per (topology_hash, equipment_hash, ref_channel_hash)
    # Invalidated when any input changes
    design_cache: dict[str, DiGraph]

    # Propagation results: cached per (design_hash, request_hash)
    propagation_cache: dict[str, SimulationResult]
```

Key caching rules:
- Equipment library is loaded once and shared across the session
- Network design is invalidated when topology or equipment changes
- Propagation results are cached per unique (path + channel parameters)
- For tutorials with parameter sliders, previous results are kept in an LRU cache to allow quick comparison

### 8.3 WebSocket for Long-Running Simulations

For Raman simulations and power sweeps that exceed 2 seconds:

```python
@app.websocket("/ws/simulate/transmission")
async def ws_transmission(websocket: WebSocket, session_id: str):
    await websocket.accept()
    # ... setup ...

    # Stream per-element propagation progress
    for i, element in enumerate(path):
        spectral_info = element(spectral_info)
        snapshot = serialize_spectral_info(spectral_info)
        await websocket.send_json({
            "type": "element_propagated",
            "element_index": i,
            "element_uid": element.uid,
            "element_type": type(element).__name__,
            "snapshot": snapshot,
            "progress": (i + 1) / len(path) * 100
        })

    await websocket.send_json({"type": "complete", "result": final_result})
```

### 8.4 Request Debouncing

When users drag sliders in tutorial parameter forms, debounce API calls:
- Frontend: 300ms debounce on slider change events
- Backend: Cancel in-flight computation if a new request arrives for the same session
- Use HTTP request IDs to match responses to requests

---

## 9. Bundle Size and Dependencies

### 9.1 Frontend Dependencies (keep lean)

**Core (required)**:
- `react`, `react-dom`: ~45KB gzipped
- `react-router-dom`: ~13KB
- `zustand`: ~1.5KB
- `recharts`: ~55KB (tree-shakeable)
- `reactflow`: ~45KB

**UI**:
- `@radix-ui/*`: only import used primitives (~5-15KB each)
- `tailwindcss`: zero runtime (purged CSS only)

**Utilities**:
- `react-markdown` + `remark-gfm`: ~25KB (for tutorial content rendering)
- `react-syntax-highlighter`: ~35KB (for code snippets, load on demand)

**Estimated total**: ~240KB gzipped (initial load)

**Code splitting strategy**:
- Lazy load `Playground` route (topology editor is heavy)
- Lazy load `react-syntax-highlighter` (only needed when viewing code)
- Lazy load individual tutorial content (fetch on navigation)

### 9.2 Backend Dependencies

GNPy's existing dependencies are the baseline:
- `numpy`, `scipy`, `networkx`, `matplotlib`, `pandas`, `openpyxl`

Additional for the API server:
- `fastapi`: ~1MB
- `uvicorn`: ~500KB
- `pydantic` (v2): already used by FastAPI
- `websockets`: ~200KB

matplotlib is NOT used by the backend API -- all visualization is frontend-side. matplotlib is only needed if the backend generates static plot images (not recommended for the interactive app).

---

## 10. Future Integration Points

### 10.1 API-First Design

All backend functionality is exposed via REST + WebSocket APIs with:
- OpenAPI 3.0 specification (auto-generated by FastAPI)
- Versioned endpoints (`/api/v1/...`)
- Consistent error responses with error codes
- CORS configuration for cross-origin use

This allows:
- **Other frontends**: mobile apps, Jupyter notebooks, CLI tools
- **Embedding**: iframe embedding of specific visualizations
- **Automation**: CI/CD pipelines that validate network designs via API
- **Integration with other TIP OOPT tools**: REST-based interop

### 10.2 Modular Architecture

```
                    +------------------+
                    |   React Frontend |
                    |  (Tutorial App)  |
                    +--------+---------+
                             |
                     REST / WebSocket
                             |
                    +--------+---------+
                    |  FastAPI Backend  |
                    |  (API Gateway)   |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
    +---------+--+  +--------+---+  +-------+--------+
    | GNPy Bridge|  | Tutorial   |  | Session        |
    | Service    |  | Service    |  | Management     |
    +------------+  +------------+  +----------------+
```

**Extension points**:
- **Plugin system for tutorials**: New tutorials can be added by dropping YAML files into a directory
- **Custom equipment libraries**: Users can upload their own equipment configs
- **Export formats**: Results exportable as JSON, CSV, PDF reports
- **Authentication layer**: Add OAuth2/JWT when needed (not for initial tutorial app)
- **Database persistence**: Add PostgreSQL when user accounts and saved sessions are needed

### 10.3 GNPy Version Compatibility

The backend should pin to a specific GNPy version and provide:
- A clear upgrade path when GNPy releases new versions
- A compatibility layer that maps API schemas to GNPy internal structures
- Version info endpoint (`GET /api/version`) reporting both app and GNPy versions

---

## 11. Unit Test Suggestions

### 11.1 Backend API Tests

```python
# tests/api/test_network.py
class TestNetworkAPI:
    def test_load_example_network(self):
        """Load edfa_example_network.json and verify element count"""

    def test_load_invalid_topology(self):
        """Verify error response for malformed JSON"""

    def test_auto_design_inserts_edfas(self):
        """Verify that auto-design adds amplifiers after fibers"""

    def test_network_topology_response_format(self):
        """Verify nodes/edges structure for frontend consumption"""


# tests/api/test_simulation.py
class TestSimulationAPI:
    def test_simple_transmission(self):
        """Run transmission on example network, verify GSNR > 0"""

    def test_propagation_returns_per_element_snapshots(self):
        """Verify spectral info snapshot at each path element"""

    def test_power_sweep(self):
        """Verify multiple results for power range"""

    def test_path_computation_source_destination(self):
        """Verify correct path for given source/destination pair"""


# tests/api/test_equipment.py
class TestEquipmentAPI:
    def test_load_default_equipment(self):
        """Load eqpt_config.json and verify Edfa/Fiber/Roadm entries"""

    def test_list_transceiver_modes(self):
        """Verify transceiver modes include baud_rate, bit_rate, OSNR"""


# tests/services/test_gnpy_bridge.py
class TestGnpyBridge:
    def test_serialization_roundtrip(self):
        """Verify numpy arrays serialize to JSON and back correctly"""

    def test_spectral_info_snapshot(self):
        """Verify SpectralInformation serialization captures all fields"""

    def test_network_to_graph_json(self):
        """Verify DiGraph serialization preserves element attributes"""

    def test_session_isolation(self):
        """Verify two sessions have independent network state"""
```

### 11.2 Frontend Component Tests

```typescript
// __tests__/components/NetworkGraph.test.tsx
describe('NetworkGraph', () => {
  it('renders nodes for each network element');
  it('renders edges for each connection');
  it('highlights path elements during simulation');
  it('shows element details on node click');
  it('uses correct icon for each element type');
});

// __tests__/components/SpectrumChart.test.tsx
describe('SpectrumChart', () => {
  it('renders signal, ASE, and NLI traces');
  it('updates when simulation results change');
  it('shows tooltip with channel details on hover');
  it('handles empty/null data gracefully');
});

// __tests__/components/TutorialView.test.tsx
describe('TutorialView', () => {
  it('renders lesson content as markdown');
  it('renders parameter sliders for interactive steps');
  it('calls API when Run button is clicked');
  it('shows results visualization after simulation');
  it('tracks step completion');
  it('navigates to next step on completion');
});

// __tests__/stores/simulationStore.test.ts
describe('SimulationStore', () => {
  it('sets isRunning during API call');
  it('stores results after successful simulation');
  it('clears results on clearResults()');
  it('handles API errors gracefully');
});

// __tests__/utils/networkConverter.test.ts
describe('networkToReactFlow', () => {
  it('converts GNPy topology to React Flow nodes/edges');
  it('maps element locations to positions');
  it('assigns correct node types');
});
```

### 11.3 Integration Tests

```python
# tests/integration/test_tutorial_flow.py
class TestTutorialFlow:
    def test_beginner_tutorial_end_to_end(self):
        """Walk through all steps of tutorial 01, verify each step produces valid results"""

    def test_parameter_changes_affect_results(self):
        """Change fiber length in tutorial, verify GSNR changes accordingly"""

    def test_example_data_all_loadable(self):
        """Verify all files in gnpy/example-data/ can be loaded via API"""
```

---

## 12. Development Roadmap Alignment

### Phase 1: Foundation (MVP)
- FastAPI backend with GNPy bridge (network load, equipment, basic propagation)
- React frontend with tutorial viewer (markdown content, parameter forms)
- Network graph visualization (React Flow)
- 3-4 beginner tutorials
- REST API only (no WebSocket yet)

### Phase 2: Rich Interactivity
- Step-by-step propagation with spectrum snapshots
- Power spectrum and GSNR charts (Recharts)
- WebSocket for long-running simulations
- 8-10 tutorials covering intermediate topics
- Playground mode (free-form simulation)

### Phase 3: Advanced Features
- Topology editor (drag-and-drop network builder)
- Spectrum assignment visualization
- Multi-service planning UI
- Raman and multiband tutorials
- Export/share results
