# GNPy Interactive Tutorial Prototype

Phase 0 deliverables for the GNPy Interactive Tutorial Web App.

## Prerequisites

- Python 3.8+
- GNPy installed (editable mode: `pip install -e .[tests]`)
- Streamlit, Plotly, NetworkX installed (`pip install streamlit plotly`)

## Deliverables

### 1. Streamlit App (`app.py`)

Interactive tutorial with three sections:

- **Tutorial 1: Your First Network** - Load and explore example network topologies
- **Tutorial 2: Run a Transmission Simulation** - Select source/destination and run a full simulation
- **Tutorial 3: Explore Parameters** - Compare simulation results with different power levels

```bash
streamlit run tutorial_prototype/app.py
```

### 2. Benchmark Script (`benchmark.py`)

Measures computation times across three example networks (edfa_example, meshTopologyExampleV2, multiband_example). Reports mean and standard deviation for equipment load, network load, network design, and transmission simulation.

```bash
python tutorial_prototype/benchmark.py
```

### 3. SimParams Concurrency Validation (`test_concurrency.py`)

Tests two approaches for running concurrent simulations:

- **Approach 1: Process Pool Isolation** - Uses `multiprocessing.Pool` for full process isolation
- **Approach 2: Deep Copy + Thread Local** - Uses `threading.local()` with deep copy of SimParams

Each approach is validated against single-threaded reference results.

```bash
python tutorial_prototype/test_concurrency.py
```
