#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: BSD-3-Clause
# tutorial_prototype.benchmark: Benchmark GNPy computation times
# Copyright (C) 2025 Telecom Infra Project and GNPy contributors

"""
GNPy Benchmark Script
=====================

Measures computation times for loading, designing, and simulating
across three example networks.

Run with: python tutorial_prototype/benchmark.py
"""

import time
import statistics
from pathlib import Path

from gnpy.core.elements import Transceiver
from gnpy.core.parameters import SimParams
from gnpy.tools.json_io import load_equipments_and_configs, load_network, load_json
from gnpy.tools.worker_utils import designed_network, transmission_simulation

_EXAMPLES_DIR = Path(__file__).resolve().parent.parent / 'gnpy' / 'example-data'

# Define the networks to benchmark
BENCHMARKS = {
    'edfa_example': {
        'topology': _EXAMPLES_DIR / 'edfa_example_network.json',
        'equipment': _EXAMPLES_DIR / 'eqpt_config.json',
        'sim_params': None,
        'source': None,  # auto-discover from network
        'destination': None,
    },
    'meshTopologyExampleV2': {
        'topology': _EXAMPLES_DIR / 'meshTopologyExampleV2.json',
        'equipment': _EXAMPLES_DIR / 'eqpt_config.json',
        'sim_params': None,
        'source': None,  # will pick first two transceivers
        'destination': None,
    },
    'multiband_example': {
        'topology': _EXAMPLES_DIR / 'multiband_example_network.json',
        'equipment': _EXAMPLES_DIR / 'eqpt_config_multiband.json',
        'sim_params': _EXAMPLES_DIR / 'sim_params.json',
        'source': None,
        'destination': None,
    },
}

NUM_RUNS = 3


def _find_transceivers(network):
    """Return a list of transceiver UIDs."""
    return [n.uid for n in network.nodes() if isinstance(n, Transceiver)]


def _time_it(func, *args, **kwargs):
    """Run func and return (result, elapsed_seconds)."""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return result, elapsed


def benchmark_network(name, config):
    """Run a full benchmark for a single network configuration.

    Returns a dict with timing lists for each phase.
    """
    results = {
        'equipment_load': [],
        'network_load': [],
        'network_design': [],
        'transmission_sim': [],
    }

    for run in range(NUM_RUNS):
        # Phase 1: Equipment load
        equipment, t_eqpt = _time_it(
            load_equipments_and_configs, config['equipment'], [], []
        )
        results['equipment_load'].append(t_eqpt)

        # Phase 2: Network load
        network, t_net = _time_it(
            load_network, config['topology'], equipment
        )
        results['network_load'].append(t_net)

        # Phase 3: Set SimParams
        if config['sim_params']:
            sim_params = load_json(config['sim_params'])
        else:
            sim_params = {}
        SimParams.set_params(sim_params)

        # Find source/destination
        source = config['source']
        destination = config['destination']
        if source is None or destination is None:
            trx_uids = _find_transceivers(network)
            if len(trx_uids) < 2:
                print(f"  WARNING: Not enough transceivers in {name}, skipping simulation.")
                return results
            source = source or trx_uids[0]
            destination = destination or trx_uids[1]

        # Phase 3: Network design
        try:
            (network_d, req, ref_req), t_design = _time_it(
                designed_network, equipment, network, source, destination
            )
            results['network_design'].append(t_design)
        except Exception as e:
            print(f"  WARNING: Network design failed for {name} run {run + 1}: {e}")
            results['network_design'].append(float('nan'))
            continue

        # Phase 4: Transmission simulation
        try:
            _, t_sim = _time_it(
                transmission_simulation, equipment, network_d, req, ref_req
            )
            results['transmission_sim'].append(t_sim)
        except Exception as e:
            print(f"  WARNING: Simulation failed for {name} run {run + 1}: {e}")
            results['transmission_sim'].append(float('nan'))

    return results


def _fmt(values):
    """Format a list of times as mean +/- std in milliseconds."""
    clean = [v for v in values if v == v]  # filter NaN
    if not clean:
        return "N/A"
    m = statistics.mean(clean) * 1000
    if len(clean) > 1:
        s = statistics.stdev(clean) * 1000
        return "%8.1f +/- %6.1f ms" % (m, s)
    return "%8.1f ms" % m


def main():
    print("=" * 80)
    print("GNPy Benchmark")
    print(f"Running {NUM_RUNS} iterations per measurement")
    print("=" * 80)

    all_results = {}

    for name, config in BENCHMARKS.items():
        print(f"\n--- Benchmarking: {name} ---")
        results = benchmark_network(name, config)
        all_results[name] = results

    # Print formatted results table
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)

    phases = ['equipment_load', 'network_load', 'network_design', 'transmission_sim']
    phase_labels = ['Equipment Load', 'Network Load', 'Network Design', 'Transmission Sim']

    # Header
    col_width = 28
    header = "%-20s" % "Phase"
    for name in BENCHMARKS:
        header += "%*s" % (col_width, name)
    print(header)
    print("-" * (20 + col_width * len(BENCHMARKS)))

    # Data rows
    for phase, label in zip(phases, phase_labels):
        row = "%-20s" % label
        for name in BENCHMARKS:
            vals = all_results[name].get(phase, [])
            row += "%*s" % (col_width, _fmt(vals))
        print(row)

    # Total row
    print("-" * (20 + col_width * len(BENCHMARKS)))
    row = f"{'TOTAL':<20}"
    for name in BENCHMARKS:
        total_vals = []
        for phase in phases:
            vals = all_results[name].get(phase, [])
            clean = [v for v in vals if v == v]
            if clean:
                total_vals.append(statistics.mean(clean))
        if total_vals:
            total_ms = sum(total_vals) * 1000
            row += f"{total_ms:>{col_width - 3}.1f} ms"
        else:
            row += f"{'N/A':>{col_width}}"
    print(row)

    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
