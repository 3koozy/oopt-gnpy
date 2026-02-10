# Devil's Advocate Review: GNPy Interactive Tutorial Web App

## Executive Summary

This review identifies risks, blind spots, and potential failure modes for the proposed interactive tutorial web app wrapping the GNPy optical network planning library. The goal is not to discourage the project, but to surface issues early so they can be addressed by design rather than discovered in production.

**Verdict:** The project is feasible but carries significant hidden complexity. The biggest risks are (1) underestimating GNPy's computational cost for web responsiveness, (2) the fragility of GNPy's internal APIs and global state, and (3) scope creep from "tutorial" to "IDE." A phased approach with clear scope boundaries and an alternative technology evaluation is strongly recommended.

---

## 1. Scope Creep Risk

**The gap between "tutorial app" and "full web IDE" is dangerously narrow.**

GNPy is not a simple library with a few functions. It is a full simulation engine with:
- 7+ element types (Transceiver, Roadm, Fiber, RamanFiber, Fused, Edfa, Multiband_amplifier) totaling 1,827 lines in `elements.py`
- A 2,168-line network module handling auto-design, amplifier selection, SRS tilt estimation, and multi-band configurations
- Complex equipment configurations (~300+ lines of JSON with nested structures)
- Request routing, spectrum assignment, and disjunction handling (1,352 lines in `request.py`)

### Where scope creep will happen:
1. **"Let users edit the network topology"** -- This sounds simple but requires implementing a graph editor that understands GNPy's connectivity constraints (Fiber must connect between Roadm/Edfa, no mixed multi-band/single-band OMS, etc.)
2. **"Let users adjust equipment parameters"** -- The equipment config has deeply nested structures with inter-dependent validation (e.g., ROADM equalization must have exactly one type, EDFA models have 6+ model types with different parameter sets)
3. **"Show results visually"** -- GNPy's current plots (`plots.py`, 75 lines) use matplotlib with blocking `show()` calls and mouse event handlers. These are fundamentally incompatible with web rendering.
4. **"Let users define service requests"** -- Requires understanding of PathRequest objects with 17+ parameters, transceiver mode selection, and spectrum slot computation

### Recommendation:
Define explicit "not in scope" boundaries before starting. Suggested Phase 1 scope: read-only visualization of pre-defined examples with parameter tweaking on a single transmission path. No topology editing, no service request creation, no spectrum assignment.

---

## 2. GNPy API Stability

**GNPy has no stable public API. The web app will be tightly coupled to internal implementation details.**

### Evidence of instability:
- `SimParams` uses a **class-level shared mutable dictionary** (`_shared_dict`) as global state (`parameters.py:95`). This is mutated via `SimParams.set_params()` and affects all instances. This pattern is inherently thread-unsafe and makes concurrent usage hazardous.
- Element constructors accept `**kwargs` dictionaries with no schema validation -- parameter names are string keys checked at runtime (`RoadmParams.__init__` uses `kwargs.get()` and `kwargs['key']`)
- The `build_network()` function (`network.py:2087`) modifies the network graph **in place**, adding/removing nodes and edges. There is no immutable representation.
- `network.py` uses `SimParams.set_params()` to temporarily change global simulation parameters during Raman gain estimation (`network.py:316`), then restores them -- a fragile pattern that breaks under concurrency.
- `json_io.py` mixes data loading, equipment creation, and network construction in tightly coupled functions

### What breaks if GNPy updates:
- Any change to element constructor signatures breaks the web app's parameter mapping
- Changes to `build_network()` behavior change the auto-design results the web app displays
- New element types (like `Multiband_amplifier`, which was added relatively recently) require web app UI updates
- Changes to JSON schema require corresponding updates to input validation and forms

### Recommendation:
Create a **stable adapter layer** between the web app and GNPy internals. Version-pin GNPy and test against specific releases. Do not expose GNPy's internal parameter structures directly to the frontend.

---

## 3. Computation Complexity

**Several GNPy operations are CPU-intensive and will cause web UI freezes if run synchronously.**

### Measured complexity hotspots:

1. **Raman Solver** (`science_utils.py:105-326`):
   - `calculate_stimulated_raman_scattering()` creates large matrices: `outer(spectral_info.pch, ones(z.size))` where z can have 1000+ points for a 100km fiber at 100m resolution
   - The iterative algorithm (`iterative_algorithm()`) loops up to 1,000 iterations with O(n^2) matrix operations per iteration
   - SRS calculation is called **per fiber span** during propagation

2. **NLI Solver** (`science_utils.py:329-400+`):
   - The GGN model performs channel-by-channel integration with O(n^2) complexity where n = number of channels
   - With 96 channels at 50GHz spacing (standard C-band), this creates 96x96 matrices
   - Multi-band configurations multiply this further

3. **Network Auto-Design** (`network.py:2087-2168`):
   - `build_network()` iterates over all ROADMs, transceivers, and fibers
   - For the CORONET CONUS topology (7,631 lines of JSON, ~75 nodes), this involves hundreds of amplifier selection iterations
   - `estimate_raman_gain()` is called per fiber during design, compounding the Raman solver cost

4. **Spectrum Assignment** (`spectrum_assignment.py`, 605 lines):
   - First-fit algorithms with constraint checking across all OMS in the network
   - O(paths * slots * OMS) complexity

### Estimated computation times (based on code analysis):
- Simple 3-node P2P propagation: 0.5-2 seconds
- 10-node mesh with auto-design: 5-15 seconds
- CORONET CONUS full propagation: 30-120+ seconds
- Raman-enabled network: 3-10x multiplier on all above

### Recommendation:
- All GNPy computations MUST run in background workers (Celery, asyncio process pool, or similar)
- Implement progress reporting for long-running operations
- Cache auto-design results aggressively
- Consider pre-computing results for tutorial examples rather than running live simulations
- Set hard timeouts (30s suggested) with user-friendly error messages

---

## 4. Data Validation

**GNPy has complex, dispersed validation that will be painful to replicate in a web UI.**

### Validation is scattered across:
- `parameters.py`: `RoadmParams` checks equalization type exclusivity, `FiberParams` validates length/loss, `EdfaParams` validates gain ranges
- `elements.py`: Constructor-time validation (e.g., `RamanFiber` requires operational params with specific keys at lines 1178-1188)
- `network.py`: Topology validation during `build_network()` (connectivity, OMS type consistency)
- `json_io.py`: Schema validation during load, equipment cross-referencing
- `exceptions.py`: 7 distinct exception types (ConfigurationError, EquipmentConfigError, NetworkTopologyError, ServiceError, DisjunctionError, SpectrumError, ParametersError)

### Specific validation pain points:
1. **Interdependent parameters**: Fiber loss depends on length, loss coefficient, and connector losses. Changing one may invalidate others.
2. **Equipment cross-references**: Amplifier `type_variety` must match an entry in the equipment library. ROADM `restrictions` reference amplifier varieties.
3. **Frequency band consistency**: Multi-band configurations require non-overlapping frequency bands across amplifiers in an OMS (`check_oms_single_type()`)
4. **Implicit defaults**: Many parameters have default values spread across `_JsonThing.update_attr()` with warning logging -- hard to surface in a UI
5. **Unit confusion**: Internally GNPy uses meters, Hz, and Watts, but JSON inputs use km, THz/GHz, and dBm. The conversion happens at load time (`convert_length()`, `dbm2watt()`)

### Recommendation:
- Implement a validation API layer that runs GNPy's validation and returns structured error messages
- Use JSON Schema for frontend validation of equipment/topology inputs before sending to backend
- Display units clearly in the UI with automatic conversion
- Show validation errors inline, not as modal dialogs

---

## 5. Security Risks (OWASP Analysis)

### A1 - Injection
- **Risk: HIGH** -- If users can upload JSON topology/equipment files, these are parsed by `json.load()` (safe) but then passed to constructors via `**kwargs` (potentially dangerous if any constructor uses `eval()` or similar)
- GNPy uses `pickle` for some internal operations -- ensure no user-controlled data reaches pickle
- `sys.exit()` is called in multiple places in CLI code (`cli_examples.py:96,101,106,111,114`) -- a web wrapper must catch these

### A2 - Broken Authentication
- The tutorial app likely won't have authentication, but if multi-user: SimParams global state means one user's simulation parameters affect another's

### A5 - Security Misconfiguration
- GNPy logging outputs potentially sensitive network topology information
- `matplotlib` backends may have security implications in server context

### A6 - Vulnerable Components
- numpy, scipy are large C-extension libraries with occasional CVEs
- networkx has had deserialization vulnerabilities

### Denial of Service
- **Risk: CRITICAL** -- A user can craft inputs that cause:
  - Infinite loops in `iterative_algorithm()` (convergence not guaranteed for all inputs, though max_iter=1000 exists)
  - Memory exhaustion: Large topology files (CORONET Global = 10,277 lines) combined with fine Raman resolution = GB-scale arrays
  - CPU exhaustion: Raman solver with `solver_spatial_resolution=1` (1 meter steps on a 100km fiber = 100,000 z-points, creating 96x100,000 matrices)

### Recommendation:
- Validate all numeric inputs against sane ranges before passing to GNPy
- Set memory limits per computation (e.g., 2GB max)
- Set CPU time limits (e.g., 60 seconds max)
- Run computations in sandboxed processes
- Never allow direct file upload to production -- validate JSON structure first
- Sanitize all GNPy logging output before sending to frontend

---

## 6. Dependency Hell

### Current GNPy dependencies (analyzed from imports):
- **numpy**: Core numerical arrays, used everywhere. Version-sensitive for array API changes.
- **scipy**: Constants, interpolation, signal processing. Large binary dependency.
- **matplotlib**: Only used in `plots.py` (75 lines) for blocking GUI plots. **Should not be needed in web app.**
- **networkx**: Graph representation. Serialization of DiGraph objects is non-trivial.
- **pandas**: Used in `cli_examples.py` for tabulate output. May not be needed.
- **openpyxl**: For reading XLS topology files. Only needed if supporting Excel import.
- **tabulate**: Pretty-printing tables. CLI-only dependency.

### Dependency concerns:
1. **matplotlib is problematic for servers**: Requires a display backend configuration. Using `Agg` backend avoids X11 but still pulls in ~30MB of dependencies. Since the web app will use its own visualization (D3.js, Plotly, etc.), matplotlib should be eliminated.
2. **numpy/scipy version pinning**: GNPy uses specific numpy APIs (e.g., `trapz` which was renamed to `trapezoid` in numpy 2.0). Version conflicts with other Python web frameworks are likely.
3. **networkx serialization**: DiGraph objects are not JSON-serializable. Converting network state to JSON for the frontend requires custom serialization using the existing `to_json` properties on each element.
4. **Total dependency footprint**: numpy + scipy + matplotlib + networkx + pandas = ~200-300MB of installed dependencies for the Python backend.

### Recommendation:
- Strip matplotlib from web app requirements; implement web-native visualizations
- Pin exact versions of numpy, scipy, networkx in requirements
- Consider containerization (Docker) to isolate the Python environment
- Evaluate if pandas/openpyxl are needed for the tutorial scope

---

## 7. Alternative Approaches

**Before building a custom web app, consider whether simpler tools achieve 80% of the goal.**

### Option A: Jupyter Notebooks with Voila
- **Pros**: Already Python, direct GNPy integration, interactive widgets (ipywidgets), community knows it, zero custom backend code
- **Cons**: Limited customization, widget UX is basic, deployment requires JupyterHub, not easily embeddable
- **Effort**: Days, not months
- **Best for**: Internal team learning, prototyping

### Option B: Streamlit
- **Pros**: Python-native, rapid prototyping, built-in caching (`@st.cache_data`), easy deployment, handles long computations with spinners
- **Cons**: Limited layout control, re-runs entire script on interaction, not ideal for complex multi-page apps
- **Effort**: 1-2 weeks for a functional prototype
- **Best for**: Quick demo, parameter exploration

### Option C: Panel/HoloViews (by HoloViz)
- **Pros**: More flexible than Streamlit, good for scientific data, supports bokeh/plotly backends, reactive programming model
- **Cons**: Steeper learning curve, smaller community
- **Effort**: 2-3 weeks
- **Best for**: Interactive scientific visualization

### Option D: Gradio
- **Pros**: Simplest option, API-first design, auto-generates UI from function signatures
- **Cons**: Very limited customization, not suitable for complex workflows
- **Effort**: Days
- **Best for**: Simple "input parameters, get results" demos

### Option E: Custom Web App (React + FastAPI)
- **Pros**: Full control over UX, scalable, can evolve into production tool, modern tech stack
- **Cons**: Highest development effort, requires full-stack expertise, all the risks in this document
- **Effort**: 2-4 months for MVP
- **Best for**: Long-term product ambition

### Recommendation:
**Start with Streamlit for a prototype (2 weeks), then evaluate if the custom web app is justified.** The Streamlit prototype will surface the real computation and UX challenges before investing in a full React/FastAPI build. If the project proceeds with a custom app, the Streamlit prototype serves as a functional specification.

---

## 8. What Could Break in Existing GNPy

**Adding a web interface should not modify GNPy's core code, but integration risks exist.**

### Direct risks:
1. **SimParams global state** (`parameters.py:94-108`): `SimParams._shared_dict` is a class variable shared across all instances. In a web server handling multiple requests, one user's `SimParams.set_params()` call will affect another user's computation. This is a **showstopper for concurrent usage**.
2. **sys.exit() calls**: `cli_examples.py` calls `sys.exit()` on validation errors (lines 96, 101, 106, 111, 114, 384, 386, 391). If the web app imports and calls these functions, `sys.exit()` will kill the web server process.
3. **print() statements**: Numerous `print()` calls in CLI code bypass logging. These will pollute server stdout.
4. **matplotlib show()**: `plots.py` calls `show()` which blocks the thread waiting for user interaction. Must never be called from a web server.
5. **In-place mutations**: `build_network()` mutates the DiGraph in place. Re-using a network object across requests without deep-copying will cause state corruption.

### Indirect risks:
6. **Logging configuration**: `_setup_logging()` in `cli_examples.py` calls `logging.basicConfig()` which configures the root logger. This will conflict with the web framework's logging.
7. **File path assumptions**: `_examples_dir` is resolved relative to the Python package location. This may not be accessible in a containerized deployment.

### Recommendation:
- **Never import or call CLI functions** (`transmission_main_example`, `path_request_run`) directly. Instead, use the lower-level functions from `worker_utils.py` (`designed_network`, `transmission_simulation`, `planning`).
- **Deep-copy the network** before each computation.
- **Wrap SimParams in a context manager** or replace with thread-local storage for concurrent usage.
- **Patch sys.exit** when calling any GNPy code that might invoke it.

---

## 9. Scalability Concerns

### Memory per user session:
- A loaded network graph (CORONET CONUS): ~50-100MB in-memory (networkx DiGraph with element objects)
- Spectral information during propagation (96 channels): ~10-20MB of numpy arrays
- Raman solver intermediate matrices: 50-500MB depending on resolution
- **Total per concurrent user: 100MB - 600MB**

### CPU per simulation:
- Simple propagation: 1-5 CPU-seconds
- Full auto-design + propagation: 10-60 CPU-seconds
- Raman-enabled: 30-300 CPU-seconds

### Concurrent user estimates:
- 10 concurrent users running simulations = 1-6GB RAM, sustained CPU load
- Without process isolation, SimParams global state corrupts results
- networkx DiGraph is not thread-safe for concurrent modifications

### Recommendation:
- Use process-based concurrency (multiprocessing, not threading) to avoid GIL and global state issues
- Limit concurrent simulations (e.g., 4 max per server)
- Implement a job queue with position feedback for users
- Consider pre-computed results for tutorial steps rather than live computation

---

## 10. Browser Compatibility

### Visualization concerns:
- Network topology visualization requires a graph rendering library (D3.js, vis.js, Cytoscape.js). These are well-supported across browsers.
- Spectrum plots (power vs. frequency, OSNR vs. distance) need a charting library (Plotly, Chart.js, Recharts). Also well-supported.
- **Real risk**: Complex SVG rendering for large networks (100+ nodes) may be slow in older browsers. The CORONET CONUS topology has ~75 nodes -- manageable but at the edge.
- WebSocket support needed for real-time progress updates during long computations.

### Data transfer:
- Serialized network state can be large (CORONET Global JSON = 10,277 lines). Compression and lazy loading needed.
- Propagation results per element per channel can generate large result sets (96 channels x 20 elements = 1,920 data points per metric).

### Recommendation:
- Target modern browsers only (Chrome, Firefox, Edge, Safari latest 2 versions)
- Use Canvas-based rendering for large networks instead of SVG
- Implement pagination/virtualization for large result tables
- Use WebSockets or Server-Sent Events for computation progress

---

## 11. Maintenance Burden

### Who maintains the web app when GNPy evolves?
- GNPy is actively developed by the Telecom Infra Project community
- Recent commits show ongoing changes: multi-band support, equipment naming, flake8 compliance
- Each GNPy release potentially requires web app updates for:
  - New element types or parameters
  - Changed validation rules
  - New output metrics
  - Modified JSON schemas

### Maintenance cost drivers:
1. **Two codebases**: Python backend + React frontend, each with their own dependency updates, security patches, and build tooling
2. **Integration testing**: Must verify web app produces same results as CLI for each GNPy version
3. **Documentation sync**: Tutorial content must match GNPy version behavior
4. **Infrastructure**: Web server, database (if any), task queue, monitoring

### Recommendation:
- Automate integration tests that compare web app output with CLI output for reference scenarios
- Pin GNPy version and update deliberately, not automatically
- Keep the web app's GNPy adapter layer thin and well-tested
- Document the maintenance procedure for GNPy version bumps

---

## 12. Edge Cases

### Network topology edge cases:
1. **Single-node network**: A network with only one Transceiver -- existing code handles this with `sys.exit()` which kills the process
2. **Disconnected components**: A network graph with isolated subgraphs -- `build_network()` will process them but path finding will fail silently
3. **Loops in topology**: `get_oms_edge_list()` has loop detection (`network.py:652-654`) but raises `NetworkTopologyError` -- web app must handle gracefully
4. **Self-referencing nodes**: A node connected to itself -- networkx allows this, GNPy behavior is undefined
5. **Massive topologies**: The CORONET Global topology (10,277 lines) represents a realistic upper bound, but users could upload larger custom topologies

### Parameter edge cases:
6. **Zero fiber length**: `Fiber.__init__` converts length from km to m (`params.length * 1e-3`); zero length causes division-by-zero in loss calculations
7. **Negative parameters**: Negative loss coefficient, negative power -- some are physically impossible but may not be validated
8. **Extreme frequencies**: Frequencies outside the C/L/S bands (191-197 THz) -- `SpectrumError` is raised when fiber parameters are out of range
9. **Single channel**: The test file `test_propagation.py:37` has a TODO note: "pytests doesn't pass with 1 channel: interpolate fail" -- known bug
10. **NaN/Inf propagation**: If any element produces NaN in output power, subsequent elements will silently propagate NaN through the chain

### Equipment configuration edge cases:
11. **Missing equipment references**: Topology references a `type_variety` not in the equipment library -- `find_type_variety()` raises an error
12. **Conflicting equalization**: Multiple equalization types set on a ROADM -- detected but error message is cryptic
13. **Empty amplifier list**: No amplifiers match the gain/power targets -- `min(acceptable_power_list)` raises ValueError on empty sequence

---

## 13. Performance Bottlenecks

### Serialization:
- **networkx DiGraph to JSON**: Each element's `to_json` property must be called individually. For a 75-node network with ~200 elements (including auto-inserted amplifiers), this involves 200 property accesses and dictionary constructions.
- **numpy array serialization**: GNPy results contain numpy arrays (per-channel OSNR, power, NF). These must be converted to Python lists for JSON serialization. `numpy.ndarray.tolist()` is slow for large arrays.
- **Round-trip time**: Loading a network from JSON, running auto-design, serializing back to JSON, and sending to frontend could take 2-5 seconds for a medium network even without propagation.

### matplotlib rendering:
- Server-side matplotlib rendering is slow (100-500ms per figure) and produces large PNG/SVG files
- **Do not use matplotlib for web rendering** -- use a JavaScript charting library instead

### networkx pathfinding:
- `dijkstra_path()` on the CORONET CONUS graph (75 nodes, ~200 edges) takes <10ms -- not a bottleneck
- However, `compute_path_with_disjunction()` for multiple service requests with constraints is O(requests^2 * nodes)

### Memory allocation:
- Each propagation creates new numpy arrays at every element. For a 20-element path with 96 channels, this creates ~100 intermediate arrays that must be garbage collected.
- The Raman solver allocates the largest arrays: `outer(spectral_info.pch, ones(z.size))` with z.size up to 100,000

### Recommendation:
- Pre-compute and cache network serialization
- Use orjson or msgpack instead of stdlib json for faster serialization
- Implement incremental result streaming (element-by-element during propagation)
- Pool numpy array allocations if possible (unlikely with GNPy's current design)

---

## 14. Testing Gaps

### What's hardest to test in a web UI wrapping a scientific library:

1. **Numerical accuracy**: The web app must produce the same results as the CLI. Floating-point differences between different execution paths (concurrent vs. sequential, different numpy versions) can cause subtle discrepancies.

2. **State leakage**: SimParams global state, element in-place mutations, and networkx graph modifications create state that can leak between tests and between user sessions.

3. **Asynchronous computation**: Testing background task completion, progress reporting, timeout handling, and cancellation requires async test infrastructure.

4. **Visual correctness**: Network topology visualizations and spectrum plots are difficult to verify programmatically. Consider snapshot testing.

5. **Error propagation**: GNPy raises 7 different exception types across 4 modules. The web app must catch all of them and present user-friendly messages. Missing a single exception path causes a 500 error.

6. **Concurrency correctness**: Two users modifying network parameters simultaneously -- testing requires careful orchestration of parallel requests.

7. **Browser rendering**: Different browsers render SVG/Canvas differently. Cross-browser visual testing requires tools like Playwright or Cypress.

### Current test coverage analysis:
- Existing tests (`tests/` directory) cover: amplifiers, propagation, network functions, JSON I/O, science utils, spectrum assignment, equalization, disjunction
- Notable test patterns: parametrized tests with multiple configurations, comparison against reference values, topology construction from JSON data
- **Missing from existing tests**: No integration tests for full CLI workflow, no performance benchmarks, no concurrent execution tests

---

## 15. Edge Case and Error Handling Test Suggestions

### Category A: Input Validation Tests

```
test_empty_topology: Submit an empty network JSON ({elements: [], connections: []})
test_single_transceiver: Network with only one Transceiver, no fibers
test_disconnected_graph: Two disconnected network segments
test_self_loop: Node connected to itself
test_duplicate_uid: Two elements with the same uid
test_missing_equipment_ref: Topology references non-existent type_variety
test_negative_fiber_length: Fiber with length = -10 km
test_zero_fiber_length: Fiber with length = 0 km
test_extreme_fiber_length: Fiber with length = 10,000 km
test_negative_loss_coefficient: Fiber with loss_coef = -0.2 dB/km
test_zero_power: Channel power = 0 dBm (valid) vs 0 watts (edge case)
test_nan_input_power: Channel power = NaN
test_inf_input_power: Channel power = infinity
test_frequency_outside_band: f_min=100e12, far below C-band
test_single_channel: Only 1 channel in the spectrum
test_overlapping_channels: Channels with spacing < baud_rate
test_conflicting_equalization: ROADM with both target_pch_out_db and target_psd_out_mWperGHz
```

### Category B: Computation Boundary Tests

```
test_raman_convergence_failure: Parameters that cause iterative_algorithm to hit max_iter=1000
test_large_network_timeout: CORONET Global topology with 60-second timeout
test_high_resolution_raman: solver_spatial_resolution=1 (1 meter) on 100km fiber
test_max_channels: 960 channels at 5GHz spacing across S+C+L bands
test_multiband_three_bands: S+C+L band simultaneous propagation
test_raman_with_pumps: 4 counter-propagating pumps at edge-case powers
test_zero_gain_amplifier: Edfa with gain_target = 0
test_amplifier_saturation: Edfa gain_target exceeds gain_flatmax
test_negative_span_loss: Network where Raman gain exceeds fiber loss
```

### Category C: Concurrency Tests

```
test_simparams_isolation: Two simultaneous requests with different SimParams
test_network_object_isolation: Two requests modifying the same network object
test_request_cancellation: Cancel a long-running computation mid-execution
test_memory_limit_enforcement: Request that would exceed memory limit
test_cpu_timeout_enforcement: Request that would exceed CPU time limit
test_queue_overflow: Submit more requests than the queue can hold
```

### Category D: API/Web Layer Tests

```
test_json_serialization_roundtrip: Serialize network to JSON and back, verify identical
test_large_response_payload: Propagation results for 96-channel, 20-element path
test_error_response_format: Each GNPy exception type produces correct HTTP error code
test_progress_reporting: Long computation sends progress updates via WebSocket
test_input_sanitization: JSON with unexpected keys, extra fields, wrong types
test_file_upload_size_limit: Topology JSON > 10MB
test_unicode_in_node_names: Element uid with non-ASCII characters
test_special_chars_in_paths: Node names with |, comma, quotes (used as separators in CLI)
```

### Category E: Regression Tests

```
test_reference_propagation_match: Web app results match CLI output for edfa_example_network
test_reference_autodesign_match: Auto-design results match CLI for meshTopologyExampleV2
test_reference_multiband_match: Multi-band results match CLI for multiband_example_network
test_reference_raman_match: Raman results match CLI for raman_edfa_example_network
```

---

## Summary of Critical Risks (Ranked)

| # | Risk | Severity | Likelihood | Mitigation Difficulty |
|---|------|----------|------------|----------------------|
| 1 | SimParams global state breaks concurrency | Critical | Certain | Medium (requires GNPy changes or process isolation) |
| 2 | Computation timeout / DoS via expensive inputs | Critical | High | Medium (input validation + timeouts) |
| 3 | Scope creep from tutorial to IDE | High | High | Low (discipline + clear requirements) |
| 4 | Memory exhaustion from Raman solver | High | Medium | Medium (limits + monitoring) |
| 5 | sys.exit() in CLI code kills web server | High | Certain | Low (don't import CLI functions) |
| 6 | GNPy version update breaks web app | Medium | Certain (over time) | Medium (adapter layer + integration tests) |
| 7 | Complex validation hard to surface in UI | Medium | High | High (significant frontend work) |
| 8 | matplotlib dependency issues on server | Medium | Medium | Low (eliminate matplotlib) |
| 9 | Maintenance burden of dual codebase | Medium | Certain (over time) | High (inherent complexity) |
| 10 | Numerical accuracy differences web vs CLI | Low | Medium | High (floating-point subtleties) |
