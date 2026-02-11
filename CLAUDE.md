# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GNPy is an open-source Python library for optical route planning and DWDM network optimization, developed under the Telecom Infra Project. It simulates signal propagation through fiber-optic networks, including amplifier noise, nonlinear interference, and Raman effects.

## Build & Development Commands

```bash
# Install in development mode (editable)
pip install --editable .[tests]

# Run all tests (includes doctests via pytest.ini --doctest-modules)
pytest -vv

# Run a single test file
pytest tests/test_propagation.py -vv

# Run a specific test
pytest tests/test_propagation.py::test_function_name -vv

# Run with coverage
pytest --cov=gnpy --cov=tests --cov-report= -vv

# Lint (max-line-length=120, max-complexity=15, ignores: N806 W503 C901)
flake8

# Lint only changed files (diff against current branch)
git show HEAD | flake8 -v --diff

# Build docs
sphinx-build -E -W --keep-going -q -b html docs/ doc/build/html

# Full CI-equivalent via tox
tox -e py312-cover   # test + coverage
tox -e linters       # flake8
tox -e docs          # sphinx docs
```

## Architecture

### Package Structure

- **`gnpy/core/`** - Core simulation engine
  - `elements.py` - Network element classes (Fiber, Edfa, Roadm, Transceiver, Fused, RamanFiber). Each element is callable: takes `SpectralInformation`, returns modified `SpectralInformation`.
  - `info.py` - `SpectralInformation` and `Channel` classes representing the WDM signal comb (power, ASE, NLI per channel).
  - `network.py` - Network graph operations: `build_network()`, `design_network()`, `add_missing_elements_in_network()`. Networks are `networkx.DiGraph` instances.
  - `parameters.py` - Configuration parameters. **`SimParams` uses class-level shared state (`_shared_dict`)** - this is a critical global singleton pattern affecting concurrency.
  - `science_utils.py` - `NliSolver` and `RamanSolver` for nonlinear interference and Raman effect calculations.
  - `equipment.py` - Equipment library lookup and transceiver mode resolution.
  - `exceptions.py` - Exception hierarchy: `ConfigurationError` > `EquipmentConfigError` / `NetworkTopologyError` / `ParametersError`; also `ServiceError`, `SpectrumError`.

- **`gnpy/tools/`** - CLI tools and I/O
  - `worker_utils.py` - High-level API functions: `designed_network()`, `transmission_simulation()`, `planning()`. These are the main entry points for programmatic use.
  - `json_io.py` - JSON/XLS loading, equipment parsing, network construction from JSON. Contains `load_network()`, `load_equipment()`, `load_json()`.
  - `cli_examples.py` - CLI entry points (`transmission_main_example`, `path_requests_run`). Uses `argparse`, calls `worker_utils` functions.
  - `plots.py` - matplotlib visualization (reference for chart implementations).

- **`gnpy/topology/`** - Path computation and spectrum assignment
  - `request.py` - `PathRequest`, `ResultElement`, path computation with disjunction constraints.
  - `spectrum_assignment.py` - Spectrum slot assignment algorithms (first-fit, etc.).

- **`gnpy/example-data/`** - Reference network topologies, equipment configs, and service requests used by tests and CLI examples.

- **`gnpy/yang/`** - YANG data models for standardized API interfaces.

### Key Data Flow

1. Load equipment config (`json_io.load_equipment`) and network topology (`json_io.load_network`) from JSON/XLS
2. Build network graph (`networkx.DiGraph` with element objects as nodes)
3. Insert missing amplifiers (`network.add_missing_elements_in_network`)
4. Design network with reference channel (`network.design_network`)
5. Compute path and propagate signal (`topology.request.compute_constrained_path`, `propagate`)
6. Each element's `__call__` modifies `SpectralInformation` as signal traverses the path

### Testing Patterns

- Tests live in `tests/` and use `pytest` with fixtures defined in `conftest.py`
- Test data files are in `tests/data/` (topologies, equipment configs, expected outputs)
- `tests/invocation/` contains reference output files for CLI invocation regression tests
- The `set_sim_params` fixture (conftest.py) monkeypatches `SimParams._shared_dict` for test isolation
- `pytest.ini` enables `--doctest-modules` so doctests in source files run automatically
- Tests compare simulation output against known reference values (regression testing)

### Important Conventions

- License: BSD-3-Clause. Every file starts with the SPDX license header.
- All source files use `#!/usr/bin/env python3` and `# -*- coding: utf-8 -*-` headers.
- Flake8 config: max line length 120, ignores `N806` (variable names), `W503` (line break before operator), `C901` (complexity).
- Build system uses `pbr` (setup.py + setup.cfg), not pyproject.toml.
- Python 3.8+ compatibility is maintained (constrains dependency versions).
- Units: frequencies in Hz, power in Watts internally (dBm for display), distances in meters.
- The `SimParams` singleton pattern means simulation parameters are global state - tests must use monkeypatch to isolate.

### CLI Entry Points

```bash
gnpy-transmission-example    # Run transmission simulation on example data
gnpy-path-request            # Run path computation with service requests
gnpy-example-data            # Print path to example-data directory
gnpy-convert-xls             # Convert XLS topology to JSON
```
