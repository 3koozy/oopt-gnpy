#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: BSD-3-Clause
# tutorial_prototype.test_concurrency: Validate SimParams concurrency approaches
# Copyright (C) 2025 Telecom Infra Project and GNPy contributors

"""
SimParams Concurrency Validation
=================================

Tests two approaches for running GNPy simulations concurrently:
1. Process Pool Isolation (multiprocessing.Pool)
2. Deep Copy + Thread Local (threading.local)

Run with: python tutorial_prototype/test_concurrency.py
"""

import multiprocessing
import threading
import time
import traceback
from copy import deepcopy
from pathlib import Path

from numpy import mean, allclose

from gnpy.core.elements import Transceiver
from gnpy.core.parameters import SimParams
from gnpy.tools.json_io import load_equipments_and_configs, load_network
from gnpy.tools.worker_utils import designed_network, transmission_simulation

_EXAMPLES_DIR = Path(__file__).resolve().parent.parent / 'gnpy' / 'example-data'

NUM_WORKERS = 4


def _get_edfa_config():
    """Return paths for the edfa_example network."""
    return {
        'topology': _EXAMPLES_DIR / 'edfa_example_network.json',
        'equipment': _EXAMPLES_DIR / 'eqpt_config.json',
    }


def _run_single_simulation(config, power_dbm=None):
    """Run a single simulation end-to-end and return the average GSNR.

    This reloads everything from scratch, which is what we need for process isolation.
    """
    equipment = load_equipments_and_configs(config['equipment'], [], [])
    network = load_network(config['topology'], equipment)
    SimParams.set_params({})

    trxs = [n.uid for n in network.nodes() if isinstance(n, Transceiver)]
    source, destination = trxs[0], trxs[1]

    kwargs = {}
    if power_dbm is not None:
        kwargs['args_power'] = power_dbm

    network, req, ref_req = designed_network(
        equipment, network, source, destination, **kwargs
    )
    path, propagations, powers_dbm_list, infos = transmission_simulation(
        equipment, network, req, ref_req
    )

    dest = path[-1]
    return {
        'avg_gsnr': float(mean(dest.snr)),
        'avg_osnr': float(mean(dest.osnr_ase)),
        'gsnr_values': list(dest.snr),
        'osnr_values': list(dest.osnr_ase),
    }


def _process_worker(args):
    """Worker function for multiprocessing Pool. Receives (config, power_dbm)."""
    config, power_dbm = args
    return _run_single_simulation(config, power_dbm)


# ---------------------------------------------------------------------------
# Approach 1: Process Pool Isolation
# ---------------------------------------------------------------------------
def test_process_pool_isolation():
    """Test concurrent simulations using multiprocessing.Pool.

    Each process gets its own copy of SimParams (separate address space),
    so there should be no cross-contamination.
    """
    print("\n" + "=" * 70)
    print("APPROACH 1: Process Pool Isolation (multiprocessing.Pool)")
    print("=" * 70)

    config = _get_edfa_config()

    # Get reference result (single-threaded)
    print("\n  Running single-threaded reference...")
    t0 = time.perf_counter()
    reference = _run_single_simulation(config)
    t_ref = time.perf_counter() - t0
    print(f"  Reference GSNR: {reference['avg_gsnr']:.4f} dB (took {t_ref * 1000:.1f} ms)")

    # Run concurrent simulations with same parameters
    print(f"\n  Running {NUM_WORKERS} concurrent simulations...")
    tasks = [(config, None)] * NUM_WORKERS
    t0 = time.perf_counter()

    try:
        # Use spawn context to ensure clean processes on all platforms
        ctx = multiprocessing.get_context('spawn')
        with ctx.Pool(processes=NUM_WORKERS) as pool:
            results = pool.map(_process_worker, tasks)
        t_concurrent = time.perf_counter() - t0
    except Exception as e:
        print(f"  FAILED: {e}")
        traceback.print_exc()
        return False

    # Verify results match reference
    print(f"  Concurrent execution took {t_concurrent * 1000:.1f} ms "
          f"({t_concurrent / t_ref:.1f}x vs single-threaded)")

    all_match = True
    for i, result in enumerate(results):
        gsnr_match = allclose(result['gsnr_values'], reference['gsnr_values'], atol=1e-6)
        osnr_match = allclose(result['osnr_values'], reference['osnr_values'], atol=1e-6)
        status = "PASS" if (gsnr_match and osnr_match) else "FAIL"
        if status == "FAIL":
            all_match = False
        print(f"  Worker {i + 1}: GSNR={result['avg_gsnr']:.4f} dB, "
              f"OSNR={result['avg_osnr']:.4f} dB [{status}]")

    # Test with different power levels to verify isolation
    print(f"\n  Running {NUM_WORKERS} concurrent simulations with DIFFERENT powers...")
    powers = [-2.0, -1.0, 0.0, 1.0][:NUM_WORKERS]
    tasks_diff = [(config, p) for p in powers]

    try:
        with ctx.Pool(processes=NUM_WORKERS) as pool:
            results_diff = pool.map(_process_worker, tasks_diff)
    except Exception as e:
        print(f"  FAILED: {e}")
        traceback.print_exc()
        return False

    # Verify that different powers give different results (isolation works)
    gsnr_vals = [r['avg_gsnr'] for r in results_diff]
    all_same = all(abs(g - gsnr_vals[0]) < 1e-6 for g in gsnr_vals)
    if all_same:
        print("  WARNING: All power levels produced identical GSNR -- isolation may not be working")
    else:
        print("  Different powers produced different GSNR values (isolation confirmed):")
        for p, r in zip(powers, results_diff):
            print(f"    Power={p:+.1f} dBm -> GSNR={r['avg_gsnr']:.4f} dB")

    # Get single-threaded references for each power to verify correctness
    references_diff = []
    for p in powers:
        ref = _run_single_simulation(config, power_dbm=p)
        references_diff.append(ref)

    diff_match = True
    for i, (result, ref) in enumerate(zip(results_diff, references_diff)):
        gsnr_match = allclose(result['gsnr_values'], ref['gsnr_values'], atol=1e-6)
        if not gsnr_match:
            diff_match = False
            print(f"  Worker {i + 1} (power={powers[i]}): MISMATCH "
                  f"concurrent={result['avg_gsnr']:.4f} vs ref={ref['avg_gsnr']:.4f}")

    if diff_match:
        print("  All concurrent results match single-threaded references.")

    overall = all_match and diff_match
    print(f"\n  APPROACH 1 RESULT: {'PASS' if overall else 'FAIL'}")
    return overall


# ---------------------------------------------------------------------------
# Approach 2: Deep Copy + Thread Local
# ---------------------------------------------------------------------------
_thread_local = threading.local()


def _thread_worker(config, power_dbm, results_dict, index, lock):
    """Worker function for threading approach.

    Uses deep copy of SimParams._shared_dict and thread-local storage
    to isolate state between threads.
    """
    try:
        equipment = load_equipments_and_configs(config['equipment'], [], [])
        network = load_network(config['topology'], equipment)

        # Save and restore SimParams using deep copy + thread local
        _thread_local.sim_params_backup = deepcopy(SimParams._shared_dict)
        SimParams.set_params({})

        trxs = [n.uid for n in network.nodes() if isinstance(n, Transceiver)]
        source, destination = trxs[0], trxs[1]

        kwargs = {}
        if power_dbm is not None:
            kwargs['args_power'] = power_dbm

        network, req, ref_req = designed_network(
            equipment, network, source, destination, **kwargs
        )
        path, propagations, powers_dbm_list, infos = transmission_simulation(
            equipment, network, req, ref_req
        )

        dest = path[-1]
        result = {
            'avg_gsnr': float(mean(dest.snr)),
            'avg_osnr': float(mean(dest.osnr_ase)),
            'gsnr_values': list(dest.snr),
            'osnr_values': list(dest.osnr_ase),
        }

        with lock:
            results_dict[index] = result

    except Exception as e:
        with lock:
            results_dict[index] = {'error': str(e)}
    finally:
        # Restore original SimParams
        if hasattr(_thread_local, 'sim_params_backup'):
            SimParams._shared_dict = _thread_local.sim_params_backup


def test_deep_copy_thread_local():
    """Test concurrent simulations using threading with deep copy of SimParams.

    WARNING: SimParams._shared_dict is class-level (shared across all threads).
    Deep copy + thread local storage may NOT provide true isolation since
    SimParams is accessed via class-level reference. This test validates whether
    this approach is feasible.
    """
    print("\n" + "=" * 70)
    print("APPROACH 2: Deep Copy + Thread Local (threading)")
    print("=" * 70)
    print("  NOTE: SimParams uses class-level shared state (_shared_dict).")
    print("  Threads share this state, so true isolation requires careful handling.")

    config = _get_edfa_config()

    # Get reference result
    print("\n  Running single-threaded reference...")
    t0 = time.perf_counter()
    reference = _run_single_simulation(config)
    t_ref = time.perf_counter() - t0
    print(f"  Reference GSNR: {reference['avg_gsnr']:.4f} dB (took {t_ref * 1000:.1f} ms)")

    # Run concurrent simulations with SAME parameters (best-case test)
    print(f"\n  Running {NUM_WORKERS} concurrent threads (same parameters)...")
    results_dict = {}
    lock = threading.Lock()
    threads = []

    t0 = time.perf_counter()
    for i in range(NUM_WORKERS):
        t = threading.Thread(
            target=_thread_worker,
            args=(config, None, results_dict, i, lock)
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()
    t_concurrent = time.perf_counter() - t0

    print(f"  Concurrent execution took {t_concurrent * 1000:.1f} ms "
          f"({t_concurrent / t_ref:.1f}x vs single-threaded)")

    same_param_pass = True
    for i in range(NUM_WORKERS):
        result = results_dict.get(i)
        if result is None:
            print(f"  Thread {i + 1}: NO RESULT")
            same_param_pass = False
        elif 'error' in result:
            print(f"  Thread {i + 1}: ERROR - {result['error']}")
            same_param_pass = False
        else:
            gsnr_match = allclose(result['gsnr_values'], reference['gsnr_values'], atol=1e-4)
            status = "PASS" if gsnr_match else "FAIL"
            if not gsnr_match:
                same_param_pass = False
            print(f"  Thread {i + 1}: GSNR={result['avg_gsnr']:.4f} dB [{status}]")

    # Run with DIFFERENT powers to test isolation
    print(f"\n  Running {NUM_WORKERS} concurrent threads with DIFFERENT powers...")
    powers = [-2.0, -1.0, 0.0, 1.0][:NUM_WORKERS]
    results_dict_diff = {}
    threads_diff = []

    t0 = time.perf_counter()
    for i, p in enumerate(powers):
        t = threading.Thread(
            target=_thread_worker,
            args=(config, p, results_dict_diff, i, lock)
        )
        threads_diff.append(t)
        t.start()

    for t in threads_diff:
        t.join()
    t_diff = time.perf_counter() - t0

    # Get single-threaded references for each power
    references_diff = []
    for p in powers:
        ref = _run_single_simulation(config, power_dbm=p)
        references_diff.append(ref)

    diff_param_pass = True
    for i in range(NUM_WORKERS):
        result = results_dict_diff.get(i)
        if result is None or 'error' in result:
            err_msg = result.get('error', 'NO RESULT') if result else 'NO RESULT'
            print(f"  Thread {i + 1} (power={powers[i]}): ERROR - {err_msg}")
            diff_param_pass = False
        else:
            ref = references_diff[i]
            gsnr_match = allclose(result['gsnr_values'], ref['gsnr_values'], atol=1e-4)
            status = "PASS" if gsnr_match else "FAIL (race condition?)"
            if not gsnr_match:
                diff_param_pass = False
            print(f"  Thread {i + 1} (power={powers[i]:+.1f} dBm): "
                  f"GSNR={result['avg_gsnr']:.4f} dB (ref={ref['avg_gsnr']:.4f}) [{status}]")

    overall = same_param_pass and diff_param_pass
    if not overall:
        print("\n  NOTE: Thread-based approach may exhibit race conditions due to")
        print("  SimParams class-level shared state. Process-based isolation is recommended.")
    print(f"\n  APPROACH 2 RESULT: {'PASS' if overall else 'FAIL'}")
    return overall


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("SimParams Concurrency Validation")
    print(f"Workers: {NUM_WORKERS}")
    print("=" * 70)

    result_1 = test_process_pool_isolation()
    result_2 = test_deep_copy_thread_local()

    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"  Approach 1 (Process Pool):       {'PASS' if result_1 else 'FAIL'}")
    print(f"  Approach 2 (Deep Copy + Thread):  {'PASS' if result_2 else 'FAIL'}")
    print()
    if result_1 and not result_2:
        print("  RECOMMENDATION: Use multiprocessing.Pool for concurrent simulations.")
        print("  SimParams class-level state makes thread-based approaches unreliable.")
    elif result_1 and result_2:
        print("  Both approaches passed. Process pool is still recommended for safety.")
    elif not result_1 and not result_2:
        print("  Both approaches failed. Simulations should be run sequentially.")
    print("=" * 70)


if __name__ == '__main__':
    main()
