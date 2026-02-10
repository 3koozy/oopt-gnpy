# GNPy Interactive Tutorial App - UX Analysis

## 1. User Personas

### 1.1 Network Planning Engineer (Primary)
- **Background**: 5-10 years experience in optical/DWDM network planning at a telecom operator or vendor
- **Technical level**: Comfortable with optical parameters (OSNR, GSNR, chromatic dispersion, PMD), understands fiber types and amplifier specifications
- **Goals**: Evaluate GNPy for production network planning workflows, compare results against proprietary tools, validate equipment library configurations
- **Pain points**: Steep learning curve with CLI-only tooling, difficulty understanding JSON configuration schemas, wants rapid what-if analysis without writing scripts
- **Tutorial needs**: Jump to specific topics (e.g., ROADM impairment modelling, multiband), equipment library customization, batch service request evaluation

### 1.2 Graduate Student / Researcher (Secondary)
- **Background**: MSc or PhD in optical communications, photonics, or telecommunications engineering
- **Technical level**: Strong theoretical foundation but limited practical network planning experience; proficient in Python
- **Goals**: Understand GNPy's physical layer models (GN model, Raman solver, NLI), use GNPy for thesis research, contribute to the project
- **Pain points**: Needs conceptual bridging between textbook equations and GNPy's implementation, unfamiliar with real-world equipment parameters
- **Tutorial needs**: Step-by-step from first principles, inline equations mapped to code, ability to tweak NLI/Raman solver parameters and see immediate effects

### 1.3 Open Source Contributor / Developer (Tertiary)
- **Background**: Software engineer or DevOps professional with interest in telecom or network infrastructure
- **Technical level**: Strong in Python/software architecture but limited domain knowledge in optical networking
- **Goals**: Contribute to GNPy, understand architecture for extending functionality, add new element types or equipment models
- **Pain points**: Needs architecture overview, element propagation pipeline explanation, JSON schema documentation
- **Tutorial needs**: Code walkthrough with architecture diagrams, element lifecycle, how SpectralInformation flows through the network

### 1.4 Technical Decision Maker
- **Background**: CTO, VP of Engineering, or Network Architect evaluating GNPy for organizational adoption
- **Technical level**: High-level understanding of optical networking; does not need implementation details
- **Goals**: Quickly assess GNPy's capabilities, see example outputs, understand integration possibilities
- **Tutorial needs**: Executive summary mode, pre-built demo scenarios with impressive visualizations, minimal interaction required

---

## 2. Tutorial Flow Design

### Phase 1: Foundations (Lessons 1-3)

**Lesson 1: "What is GNPy?"**
- Overview of optical route planning and DWDM concepts
- Interactive glossary panel (OSNR, GSNR, EDFA, ROADM, WDM, NLI, etc.)
- Show the simplest possible network: `Transceiver -> Fiber -> EDFA -> Transceiver` (the `edfa_example_network.json` topology)
- User action: Click nodes on a visual diagram to see their properties
- Learning outcome: Understand network element types and their roles

**Lesson 2: "Your First Simulation"**
- Load the EDFA example network (Site_A -> Span1 -> Edfa1 -> Site_B)
- Walk through JSON topology format: `elements[]` and `connections[]`
- Show how to specify a source and destination transceiver
- Run `transmission_main_example` with default parameters
- Display: per-element propagation results, final GSNR at destination
- User action: Toggle between viewing raw JSON and a visual network diagram
- Learning outcome: Run a point-to-point simulation and read results

**Lesson 3: "Understanding Equipment"**
- Explore `eqpt_config.json` structure: Edfa types (variable_gain, fixed_gain, advanced_model, openroadm, dual_stage), Fiber types (SSMF, NZDF, LOF), Span parameters, SI (Spectral Information), Transceiver modes
- Interactive parameter editor: change `power_dbm`, `spacing`, `baud_rate` in SI and see how channel count changes
- Compare amplifier types: show NF vs. gain curves for different EDFA models
- User action: Drag sliders to modify equipment parameters; observe immediate effect on simulation output
- Learning outcome: Understand the equipment library and its role in simulation

### Phase 2: Core Concepts (Lessons 4-6)

**Lesson 4: "Network Topologies"**
- Load `meshTopologyExampleV2.json` -- a realistic mesh network with multiple ROADMs, fibers, and transceivers across Brittany (France)
- Interactive topology map with geo-coordinates (latitude/longitude already in metadata)
- Demonstrate: listing nodes, selecting source/destination, computing paths
- Show path constraints: explicit routing via ROADM waypoints (the `--path` flag with `|` or `,` separators)
- User action: Click on map to select source/destination; see shortest path highlighted
- Learning outcome: Work with mesh topologies and understand path computation

**Lesson 5: "Signal Propagation Deep Dive"**
- Visualize SpectralInformation as it propagates through each element
- Per-element view: show how signal power, ASE noise, NLI noise, chromatic dispersion, PMD, PDL, and latency accumulate
- Side-by-side: element input vs. output spectral information
- Show how ROADMs equalize power (target_pch_out_db, PSD modes, per-slot-width modes)
- Interactive: step through propagation element-by-element with play/pause controls
- User action: Click "Next Element" to advance propagation; inspect spectral info at each stage
- Learning outcome: Understand how each element type transforms the optical signal

**Lesson 6: "Service Requests & Path Planning"**
- Load `meshTopologyExampleV2_services.json`
- Explain the path-request JSON format: request-id, source, destination, path constraints (trx_type, trx_mode, spacing, bandwidth), explicit route objects
- Run `path_requests_run` with multiple service requests
- Show results table: GSNR, OSNR, blocking reasons, spectrum assignment (N, M values)
- Demonstrate bidirectional mode and spectrum policy (first_fit)
- User action: Create a new service request via form, submit, and see results
- Learning outcome: Use GNPy for multi-service path computation

### Phase 3: Advanced Topics (Lessons 7-9)

**Lesson 7: "Autodesign & Amplifier Selection"**
- Explain the autodesign process: `add_missing_elements_in_network()` + `design_network()`
- Show how GNPy automatically inserts EDFAs after ROADMs and fibers
- Demonstrate amplifier selection algorithm: gain target, power target, noise figure optimization
- Compare: network before vs. after autodesign (save_network_before_autodesign vs. save_network)
- Interactive: toggle `--no-insert-edfas` to see the difference
- User action: Run autodesign, compare topologies, adjust amplifier restrictions
- Learning outcome: Understand automatic network design

**Lesson 8: "Advanced Impairments & Raman"**
- Introduce RamanFiber elements and sim_params.json configuration
- Explain NLI solver methods: `gn_model_analytic` vs. `ggn_spectrally_separated`
- Show Raman power profile along fiber position
- Demonstrate ROADM detailed impairments: express/add/drop paths, frequency-dependent PMD/PDL/OSNR
- User action: Toggle Raman on/off, change solver method, observe GSNR impact
- Learning outcome: Configure advanced physical layer models

**Lesson 9: "Multiband & Custom Spectra"**
- Load `multiband_example_network.json` and `eqpt_config_multiband.json`
- Explain C-band + L-band operation, multiband amplifier configuration
- Load custom spectrum definitions from `initial_spectrum1.json` / `initial_spectrum2.json`
- Mixed-rate spectrum propagation: channels with different baud rates and spacings
- User action: Design a multiband spectrum, assign channels to bands, simulate
- Learning outcome: Work with multiband networks and custom spectral loads

### Phase 4: Integration (Lesson 10)

**Lesson 10: "From Tutorial to Production"**
- Converting XLS spreadsheets to JSON using `gnpy-convert-xls`
- OpenROADM interoperability (v4, v5 examples)
- API integration patterns (worker_utils.py as the programmatic interface)
- Exporting results to CSV/JSON for further analysis
- User action: Upload an XLS file, convert, and run simulation
- Learning outcome: Use GNPy in real-world workflows

---

## 3. UI Component Design

### 3.1 Layout Structure

```
+------------------------------------------------------------------+
|  Header: Logo | Lesson Navigation (breadcrumbs) | Settings | Help |
+------------------------------------------------------------------+
|         |                                          |              |
| Sidebar |          Main Content Area               |  Inspector   |
| (ToC +  |   (Split: Instruction + Interactive)     |  Panel       |
| Progress|                                          |  (Details)   |
|         |                                          |              |
+---------+------------------------------------------+--------------+
|  Console / Output Panel (collapsible)                             |
+------------------------------------------------------------------+
```

### 3.2 Core Components

**NetworkTopologyViewer**
- Renders network as an interactive graph using geo-coordinates (lat/lng from element metadata)
- Node shapes by type: circles for Transceivers, diamonds for ROADMs, rectangles for EDFAs, lines for Fibers, triangles for Fused elements
- Color coding: grey for inactive path, red/highlighted for active propagation path (matching plots.py behavior)
- Click node to inspect properties; click edge to see fiber parameters
- Zoom, pan, fit-to-view controls
- Path highlighting with animation showing signal flow direction
- Technology: D3.js force-directed or Leaflet/MapLibre for geo-positioned layouts

**EquipmentParameterEditor**
- Tree-structured form mirroring `eqpt_config.json` sections: Edfa[], Fiber[], RamanFiber[], Span[], Roadm[], SI[], Transceiver[]
- Each parameter has: label, input control (number, dropdown, toggle), unit annotation, tooltip with description
- Validation: range checks (e.g., gain_min < gain_flatmax), type checks, cross-field constraints (e.g., baud_rate <= min_spacing)
- "Reset to default" button per section
- Diff view: show what changed from the default configuration

**SpectralInformationVisualizer**
- Horizontal bar/waterfall chart showing all WDM channels
- X-axis: frequency (THz) or channel number
- Y-axis: power (dBm)
- Color layers: signal power (blue), ASE noise (orange), NLI noise (red)
- Hover tooltip: per-channel details (frequency, baud_rate, slot_width, OSNR, GSNR, CD, PMD)
- Supports mixed-rate display where different channel groups have different baud rates

**PropagationTimeline**
- Vertical timeline showing each network element in propagation order
- Each element card shows: element type icon, uid, key metrics (loss, gain, power out)
- Click to expand: full element __str__ output with all computed values
- Animated "signal pulse" moving through the timeline during simulation playback
- Side panel: line chart of cumulative OSNR/GSNR degradation along path

**ResultsTable**
- Sortable, filterable data table for path request results
- Columns matching CLI output: req id, demand (source-dest), GSNR@bandwidth, GSNR@0.1nm, OSNR@bandwidth, OSNR@0.1nm, receiver minOSNR, mode, Gbit/s, nb tsp pairs, N/M or blocking reason
- Color-coded rows: green for feasible, red for blocked
- Export to CSV/JSON buttons
- Click row to highlight corresponding path on topology viewer

**JSONEditor**
- Syntax-highlighted JSON editor with schema validation
- Collapsible sections for large files
- Side-by-side: raw JSON and "visual form" toggle
- Error annotations inline (red squiggly underlines on invalid fields)
- Auto-completion for known field names from GNPy schemas

**CodeSnippetPanel**
- Shows equivalent Python code for the current tutorial step
- Syntax highlighting with line numbers
- "Copy to clipboard" button
- Maps tutorial actions to `gnpy.tools.worker_utils` API calls (e.g., `designed_network()`, `transmission_simulation()`, `planning()`)

**GlossaryTooltip**
- Hoverable terms throughout tutorial text that show definitions
- Key terms: OSNR, GSNR, ASE, NLI, EDFA, ROADM, PMD, PDL, CD, WDM, DWDM, Flexi-grid, Baud rate, Roll-off, Slot width, Tx OSNR, Power mode, Gain mode
- Links to relevant lesson for deeper explanation

### 3.3 Supplementary Components

**AmplifierCurveChart**
- NF vs. Gain plot for selected EDFA type_variety
- Overlay multiple amplifier types for comparison
- Interactive: drag vertical line to set gain_target, read off NF

**FiberProfileChart**
- Power vs. distance along fiber (especially for Raman fibers)
- Shows lumped losses at specified positions
- Loss coefficient vs. frequency for multi-band fibers

**SpectrumAssignmentViewer**
- Bitmap visualization of the OMS (Optical Multiplex Section)
- Shows FREE (green), OCCUPIED (red), UNUSABLE (grey) slots
- Channel assignment overlay with N, M values
- Guardband indicators

**NetworkDiffViewer**
- Side-by-side comparison of two network states (e.g., before and after autodesign)
- Highlights added elements (new EDFAs), changed parameters
- Useful for Lesson 7 (autodesign)

---

## 4. Interaction Patterns

### 4.1 Progressive Disclosure
- Each lesson starts with minimal UI complexity; advanced panels appear as concepts are introduced
- First visit: guided walkthrough with highlighted regions and step indicators
- Return visit: all panels available, no forced sequencing
- "Expert mode" toggle: skip explanatory text, show all controls immediately

### 4.2 Input Forms
- **Simulation Parameters Form**: source (dropdown of transceivers), destination (dropdown), power_dbm (slider: -6 to +6 dBm), spectrum options (spacing, baud_rate dropdowns)
- **Service Request Builder**: request_id (auto-generated), source/destination (map click or dropdown), transceiver type (dropdown from equipment), mode (dropdown filtered by selected trx), bandwidth (number input with unit), explicit route (add waypoint ROADMs via drag-and-drop on map)
- **Equipment Editor**: nested accordion panels matching JSON structure, with "Apply & Re-simulate" button

### 4.3 Live Preview
- Parameter changes trigger debounced re-simulation (300ms delay after last keystroke)
- Loading indicator on affected result panels during computation
- Diff highlighting: changed values flash briefly before settling
- "Pin" button on result panels to keep a snapshot for comparison

### 4.4 Step-Through Execution
- "Propagation Debugger" mode for Lesson 5
- Play / Pause / Step Forward / Step Back controls
- Current element highlighted on both topology viewer and propagation timeline
- SpectralInformation state shown as snapshot at current element
- "Watch" panel: select specific metrics (e.g., mean GSNR) to track across elements

### 4.5 Error Handling
- Invalid configurations show inline errors matching GNPy's exception types:
  - `EquipmentConfigError`: highlight offending field in Equipment Editor
  - `NetworkTopologyError`: highlight problematic node/edge on topology viewer
  - `ServiceError`: highlight affected row in results table
  - `SpectrumError`: highlight overlapping channels in spectrum visualizer
- Error messages use plain language with "Learn more" links to relevant lesson
- "Suggest fix" where possible (e.g., "Baud rate 66 GHz exceeds min_spacing 50 GHz -- increase min_spacing to at least 75 GHz")

### 4.6 Data Import/Export
- Drag-and-drop upload zones for: topology JSON/XLS, equipment JSON, service requests JSON/XLS, spectrum JSON, sim_params JSON
- File type detection and validation before processing
- Export: download current configuration as JSON, results as CSV/JSON, network diagram as SVG/PNG

---

## 5. Visualization Requirements

### 5.1 Network Topology Graph (derived from plots.py)
- **Baseline view** (`plot_baseline`): all nodes plotted by (lng, lat) coordinates, Transceiver nodes labeled with city names, grey nodes/edges for inactive network
- **Results view** (`plot_results`): active path highlighted in a contrasting color (red in original), path edges drawn on top, title showing source-destination cities
- **Hover interaction**: replicate the matplotlib hover behavior from `plot_results` -- show spectral information text box when hovering over path nodes
- **Web adaptation**: replace matplotlib with a web-native library; use SVG/Canvas rendering; provide equivalent interactivity via click/hover events

### 5.2 Signal Spectrum Chart
- **Channel power spectrum**: bar chart with one bar per WDM channel
- **Noise floor overlay**: ASE noise level as a continuous line beneath signal bars
- **NLI contribution**: stacked or separate trace showing nonlinear interference noise
- **Reference**: OSNR and GSNR annotations per channel or as average
- **Frequency axis**: switchable between THz and channel number
- **Power axis**: dBm scale with configurable range

### 5.3 Propagation Waterfall
- **X-axis**: element index along path (0 to N)
- **Y-axis**: power level (dBm) or SNR (dB)
- **Traces**: signal power, ASE, NLI, total GSNR -- each as a separate line
- **Element markers**: vertical dashed lines at each element boundary with type icon
- **Annotations**: gain/loss values at amplifier/fiber positions

### 5.4 Amplifier Performance Charts
- **NF vs. Gain**: scatter/line plot for each amplifier type_variety
- **Power output vs. input**: operating point visualization
- **Gain tilt**: if applicable, show spectral gain shape

### 5.5 Raman Profile (for advanced lessons)
- **Power vs. Position**: signal power profile along fiber length (z-axis in meters)
- **Multi-frequency**: overlay profiles for different channel frequencies
- **Pump power**: show co/counter-propagating pump contributions

### 5.6 Spectrum Bitmap (for spectrum assignment)
- **Grid visualization**: each slot as a small square in a long horizontal strip
- **Color coding**: FREE=green, OCCUPIED=red, UNUSABLE=grey
- **Overlay**: assigned channels shown as labeled blocks spanning their N,M slots
- **Zoom**: ability to zoom into frequency regions of interest

---

## 6. Accessibility (a11y)

### 6.1 Color Contrast
- All chart colors must meet WCAG 2.1 AA contrast ratio (4.5:1 for text, 3:1 for large text and graphical objects)
- Optical spectrum colors (C-band ~1530-1565nm, L-band ~1565-1625nm) are used metaphorically, not literally -- use distinguishable palette instead of actual infrared wavelength colors
- Provide a high-contrast mode alternative palette
- Never rely on color alone to convey information: use patterns, shapes, or labels as redundant cues
- Specific palette recommendations:
  - Signal power: solid blue (#2563EB)
  - ASE noise: dashed orange (#F59E0B)
  - NLI noise: dotted red (#DC2626)
  - Active path: thick solid (#DC2626) vs. inactive (#9CA3AF)
  - Spectrum FREE: green (#16A34A) + diagonal hatch pattern
  - Spectrum OCCUPIED: red (#DC2626) + solid fill
  - Spectrum UNUSABLE: grey (#6B7280) + cross-hatch pattern
  - Feasible result row: light green background (#F0FFF4)
  - Blocked result row: light red background (#FFF5F5)

### 6.2 Keyboard Navigation
- Full keyboard navigation for all interactive elements (Tab, Shift+Tab, Enter, Escape, Arrow keys)
- Focus indicators visible on all focusable elements (2px solid outline with offset)
- Network topology: arrow keys to move between nodes, Enter to select/inspect, Escape to deselect
- Propagation timeline: Up/Down arrows to move between elements, Enter to expand details
- Forms: standard tab order, Enter to submit, Escape to cancel
- Keyboard shortcuts panel (accessible via `?`):
  - `N` / `P`: Next / Previous lesson
  - `Space`: Play/Pause propagation
  - `Right` / `Left`: Step forward/back in propagation
  - `E`: Toggle equipment editor
  - `R`: Run simulation
  - `F`: Focus search/filter

### 6.3 Screen Reader Support
- All charts have `aria-label` descriptions summarizing the data
- Network topology provides a text-based adjacency list alternative
- Results tables use proper `<table>`, `<thead>`, `<th scope>` markup
- Live regions (`aria-live="polite"`) for simulation status updates ("Simulation running...", "Simulation complete: GSNR = 24.5 dB")
- Chart data downloadable as CSV for screen-reader-friendly consumption
- Form labels associated with inputs via `for`/`id` or `aria-labelledby`
- Error messages linked to inputs via `aria-describedby`

### 6.4 Motion & Animation
- All animations respect `prefers-reduced-motion` media query
- Propagation playback has explicit play/pause; no auto-play on page load
- Loading spinners use `aria-busy="true"` on their containers
- No flashing content faster than 3 flashes per second

---

## 7. Responsive Design

### 7.1 Desktop-First (Primary: 1280px+)
- Three-column layout: sidebar (240px) + main content (flexible) + inspector panel (320px)
- All panels visible simultaneously
- Drag-to-resize panel boundaries
- Topology viewer has generous space for complex mesh networks

### 7.2 Tablet (768px - 1279px)
- Two-column layout: collapsible sidebar + main content
- Inspector panel becomes a slide-over drawer from the right
- Topology viewer occupies full main content width
- Touch-friendly: larger tap targets (minimum 44x44px), pinch-to-zoom on topology

### 7.3 Mobile (< 768px)
- Single-column stacked layout
- Bottom navigation tabs replacing sidebar (Lesson | Network | Results | Settings)
- Topology viewer: simplified view with pan/zoom gestures
- Equipment editor: full-screen modal when opened
- Results table: horizontal scroll with sticky first column
- Propagation timeline: vertical swipeable cards
- Note: Mobile is a reference/review experience, not the primary design target; some advanced interactions (e.g., drag-and-drop routing) degrade to simpler alternatives (dropdown selection)

### 7.4 Print
- Lesson content renders cleanly for print (CSS `@media print`)
- Charts export as static images
- Results tables maintain formatting
- Hide interactive controls, navigation, and sidebars

---

## 8. Component Test Suggestions

### 8.1 Render Tests (verify components mount and display correctly)

| Component | Test Description |
|---|---|
| `NetworkTopologyViewer` | Renders nodes from `edfa_example_network.json` with correct count (4 elements) and positions |
| `NetworkTopologyViewer` | Renders mesh topology with correct node types (Transceiver, Roadm, Fiber) |
| `NetworkTopologyViewer` | Highlights path when source/destination are selected |
| `EquipmentParameterEditor` | Renders all sections from `eqpt_config.json` (Edfa, Fiber, Span, Roadm, SI, Transceiver) |
| `EquipmentParameterEditor` | Shows validation error when gain_min > gain_flatmax |
| `EquipmentParameterEditor` | Shows validation error when baud_rate > min_spacing |
| `SpectralInformationVisualizer` | Renders correct number of channel bars for 76-channel C-band spectrum (191.3-195.1 THz, 50 GHz spacing) |
| `SpectralInformationVisualizer` | Displays mixed-rate spectrum with visually distinct channel groups |
| `PropagationTimeline` | Renders correct element sequence for linear network (Transceiver -> Fiber -> Edfa -> Transceiver) |
| `PropagationTimeline` | Shows expanded details when element card is clicked |
| `ResultsTable` | Renders service request results with correct column headers |
| `ResultsTable` | Applies green/red styling based on feasibility (blocking_reason) |
| `JSONEditor` | Renders valid JSON with syntax highlighting |
| `JSONEditor` | Shows error annotation for malformed JSON |
| `GlossaryTooltip` | Renders tooltip on hover with correct definition |
| `SpectrumAssignmentViewer` | Renders bitmap with correct FREE/OCCUPIED/UNUSABLE distribution |
| `AmplifierCurveChart` | Renders NF vs. Gain curve with correct axis labels and units |

### 8.2 Interaction Tests (verify user interactions produce expected behavior)

| Component | Test Description |
|---|---|
| `NetworkTopologyViewer` | Clicking a node opens the inspector panel with correct element properties |
| `NetworkTopologyViewer` | Clicking two Transceiver nodes in sequence sets source/destination |
| `NetworkTopologyViewer` | Zoom in/out changes viewport scale |
| `EquipmentParameterEditor` | Changing power_dbm slider triggers debounced re-simulation callback |
| `EquipmentParameterEditor` | "Reset to default" restores original values |
| `EquipmentParameterEditor` | Diff view highlights only changed parameters |
| `PropagationTimeline` | Step Forward advances to next element and updates SpectralInformationVisualizer |
| `PropagationTimeline` | Step Back returns to previous element state |
| `PropagationTimeline` | Play button auto-advances through elements with configurable speed |
| `ResultsTable` | Sorting by GSNR column reorders rows correctly |
| `ResultsTable` | Clicking a row highlights the corresponding path on the topology viewer |
| `ResultsTable` | Export CSV button downloads file with correct data |
| `JSONEditor` | Editing JSON and clicking "Apply" triggers topology reload |
| `JSONEditor` | Toggling to "visual form" renders equivalent form controls |
| `ServiceRequestBuilder` | Adding waypoint ROADMs updates explicit-route-objects in request JSON |
| `ServiceRequestBuilder` | Submitting form triggers path computation and updates results |
| `SimulationControls` | "Run" button triggers simulation; "Cancel" aborts in-progress simulation |

### 8.3 Accessibility Tests

| Component | Test Description |
|---|---|
| All interactive | Tab order follows logical reading order |
| All interactive | Focus indicator visible on every focusable element |
| `NetworkTopologyViewer` | Arrow keys navigate between nodes when viewer is focused |
| `ResultsTable` | Screen reader announces column headers for each cell |
| Charts | `aria-label` present and descriptive on all chart containers |
| Forms | All inputs have associated labels (programmatically linked) |
| Error states | Error messages linked via `aria-describedby` to their inputs |
| Animations | Propagation playback respects `prefers-reduced-motion` |

### 8.4 Integration Tests

| Scenario | Test Description |
|---|---|
| End-to-end transmission | Load example network, select source/destination, run simulation, verify GSNR output matches CLI reference value |
| End-to-end path request | Load mesh topology + services, run path computation, verify results table matches CLI tabulate output |
| Equipment change propagation | Modify amplifier NF in equipment editor, re-simulate, verify GSNR changes in expected direction |
| File upload | Upload XLS topology file, verify conversion to JSON and successful network rendering |
| Error recovery | Load invalid topology JSON, verify error message appears and points to the problematic element |

---

## Appendix A: Data Flow Summary

```
User Input (UI forms / JSON editor / file upload)
    |
    v
Equipment Library (eqpt_config.json)  +  Network Topology (*.json / *.xls)
    |                                      |
    v                                      v
load_equipments_and_configs()         load_network()
    |                                      |
    +--------- designed_network() ---------+
    |
    v
Autodesign: add_missing_elements_in_network() + design_network()
    |
    v
transmission_simulation()  OR  planning()
    |                            |
    v                            v
Per-element propagation      Multi-service path computation
(SpectralInformation.__call__)  (compute_path_with_disjunction)
    |                            |
    v                            v
Results: GSNR, OSNR, CD,    Results: per-request feasibility,
PMD, PDL, latency per        GSNR, OSNR, spectrum assignment
channel at destination       (N, M), blocking reasons
    |                            |
    v                            v
Visualization components     Results table + export
```

## Appendix B: Key GNPy Concepts for Tutorial Content

| Concept | GNPy Module | Key Classes/Functions |
|---|---|---|
| Network elements | `gnpy.core.elements` | `Transceiver`, `Fiber`, `RamanFiber`, `Edfa`, `Roadm`, `Fused`, `Multiband_amplifier` |
| Spectral information | `gnpy.core.info` | `SpectralInformation`, `Channel`, `Carrier` |
| Equipment configuration | `gnpy.tools.json_io` | `SI`, `Amp`, `Span`, load functions |
| Equipment params | `gnpy.core.equipment` | `trx_mode_params()` |
| Network operations | `gnpy.core.network` | `select_edfa()`, `add_missing_elements_in_network()`, `design_network()` |
| Physical models | `gnpy.core.science_utils` | `NliSolver`, `RamanSolver`, `raised_cosine()` |
| Simulation parameters | `gnpy.core.parameters` | `SimParams`, `NLIParams`, `RamanParams`, `FiberParams`, `EdfaParams`, `RoadmParams` |
| Path computation | `gnpy.topology.request` | `PathRequest`, `compute_constrained_path()`, `propagate()`, `ResultElement` |
| Spectrum assignment | `gnpy.topology.spectrum_assignment` | `Bitmap`, `BitmapValue`, `Oms`, `build_oms_list()`, `pth_assign_spectrum()` |
| Worker utilities | `gnpy.tools.worker_utils` | `designed_network()`, `transmission_simulation()`, `planning()` |
| CLI entry points | `gnpy.tools.cli_examples` | `transmission_main_example()`, `path_requests_run()` |
| Data conversion | `gnpy.tools.convert` | `xls_to_json_data()` |
| Visualization | `gnpy.tools.plots` | `plot_baseline()`, `plot_results()` |
