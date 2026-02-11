#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: BSD-3-Clause
# tutorial_prototype.app: Interactive tutorial prototype for GNPy
# Copyright (C) 2025 Telecom Infra Project and GNPy contributors

"""
GNPy Interactive Tutorial Prototype
====================================

A Streamlit app with interactive tutorials for learning GNPy.
Run with: streamlit run tutorial_prototype/app.py
"""

import streamlit as st
import plotly.graph_objects as go
from pathlib import Path
from numpy import mean

from gnpy.core.elements import Transceiver, Fiber, RamanFiber, Edfa, Roadm, Fused
from gnpy.core.parameters import SimParams
from gnpy.core.utils import lin2db
from gnpy.tools.json_io import load_equipments_and_configs, load_network
from gnpy.tools.worker_utils import designed_network, transmission_simulation

_EXAMPLES_DIR = Path(__file__).resolve().parent.parent / 'gnpy' / 'example-data'

# Available example networks
NETWORKS = {
    'edfa_example': {
        'topology': _EXAMPLES_DIR / 'edfa_example_network.json',
        'equipment': _EXAMPLES_DIR / 'eqpt_config.json',
        'description': 'Simple 2-node network (Brest to Rennes) with EDFA amplifiers.',
    },
    'meshTopologyExampleV2': {
        'topology': _EXAMPLES_DIR / 'meshTopologyExampleV2.json',
        'equipment': _EXAMPLES_DIR / 'eqpt_config.json',
        'description': 'Mesh topology with multiple paths and ROADMs.',
    },
}


def _element_type_name(node):
    """Return a human-readable type name for a network element."""
    for cls in (Transceiver, Fiber, RamanFiber, Edfa, Roadm, Fused):
        if isinstance(node, cls):
            return cls.__name__
    return type(node).__name__


def _load_network_cached(network_key):
    """Load equipment and network for a given example key. Uses st.cache_resource to avoid reloading."""
    info = NETWORKS[network_key]
    equipment = load_equipments_and_configs(info['equipment'], [], [])
    network = load_network(info['topology'], equipment)
    return equipment, network


def _get_transceivers(network):
    """Return a dict of {uid: node} for all Transceiver nodes."""
    return {n.uid: n for n in network.nodes() if isinstance(n, Transceiver)}


# ---------------------------------------------------------------------------
# Tutorial 1: Your First Network
# ---------------------------------------------------------------------------
def tutorial_1():
    st.header("Tutorial 1: Your First Network")
    st.markdown("""
    In this tutorial you will load an example optical network and explore its topology.
    GNPy models DWDM networks as directed graphs where nodes are network elements
    (transceivers, fibers, amplifiers, ROADMs) and edges represent physical connections.
    """)

    network_key = st.selectbox(
        "Select an example network",
        list(NETWORKS.keys()),
        format_func=lambda k: f"{k} -- {NETWORKS[k]['description'][:60]}",
    )

    st.info(NETWORKS[network_key]['description'])

    try:
        equipment, network = _load_network_cached(network_key)
    except Exception as e:
        st.error(f"Failed to load network: {e}")
        return

    # --- Topology summary ---
    st.subheader("Topology Summary")
    nodes = list(network.nodes())
    edges = list(network.edges())

    type_counts = {}
    for node in nodes:
        t = _element_type_name(node)
        type_counts[t] = type_counts.get(t, 0) + 1

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Nodes", len(nodes))
        st.metric("Total Edges", len(edges))
    with col2:
        for t, count in sorted(type_counts.items()):
            st.metric(t, count)

    # --- Equipment summary ---
    st.subheader("Equipment Summary")
    eqpt_types = list(equipment.keys())
    with st.expander("Equipment types loaded", expanded=False):
        for eqpt_type in sorted(eqpt_types):
            items = equipment[eqpt_type]
            if isinstance(items, dict):
                st.write(f"**{eqpt_type}**: {', '.join(items.keys())}")
            else:
                st.write(f"**{eqpt_type}**: {items}")

    # --- SI (Spectral Information) defaults ---
    si = equipment['SI']['default']
    st.subheader("Default Spectral Information (SI)")
    si_col1, si_col2, si_col3 = st.columns(3)
    with si_col1:
        st.metric("Power (dBm)", "%.1f" % si.power_dbm)
        st.metric("F_min (THz)", "%.3f" % (si.f_min * 1e-12))
    with si_col2:
        st.metric("F_max (THz)", "%.3f" % (si.f_max * 1e-12))
        st.metric("Spacing (GHz)", "%.1f" % (si.spacing * 1e-9))
    with si_col3:
        st.metric("Roll-off", "%.2f" % si.roll_off)
        st.metric("Baud rate (GBd)", "%.1f" % (si.baud_rate * 1e-9))

    # --- Network diagram ---
    st.subheader("Network Diagram")
    _draw_network_diagram(network)

    # --- Node listing ---
    st.subheader("Node Details")
    transceivers = _get_transceivers(network)
    st.write(f"**Transceivers ({len(transceivers)}):** {', '.join(sorted(transceivers.keys()))}")

    with st.expander("All nodes", expanded=False):
        for node in sorted(nodes, key=lambda n: n.uid):
            tname = _element_type_name(node)
            st.write(f"- `{node.uid}` ({tname})")


def _draw_network_diagram(network):
    """Draw a simple network diagram using plotly with a spring layout."""
    import networkx as nx

    try:
        pos = nx.spring_layout(network, seed=42)
    except Exception:
        pos = nx.kamada_kawai_layout(network)

    # Classify nodes by type for coloring
    color_map = {
        'Transceiver': '#2196F3',
        'Roadm': '#4CAF50',
        'Edfa': '#FF9800',
        'Fiber': '#9E9E9E',
        'RamanFiber': '#795548',
        'Fused': '#607D8B',
    }

    # Draw edges
    edge_x, edge_y = [], []
    for u, v in network.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(width=1, color='#888'),
        hoverinfo='none',
    )

    # Draw nodes grouped by type
    node_traces = []
    nodes_by_type = {}
    for node in network.nodes():
        t = _element_type_name(node)
        nodes_by_type.setdefault(t, []).append(node)

    for t, node_list in nodes_by_type.items():
        xs = [pos[n][0] for n in node_list]
        ys = [pos[n][1] for n in node_list]
        texts = [n.uid for n in node_list]
        color = color_map.get(t, '#000000')
        # Only show text labels for Transceivers and Roadms
        text_mode = 'markers+text' if t in ('Transceiver', 'Roadm') else 'markers'
        trace = go.Scatter(
            x=xs, y=ys,
            mode=text_mode,
            text=texts if t in ('Transceiver', 'Roadm') else None,
            textposition='top center',
            textfont=dict(size=9),
            marker=dict(size=10 if t in ('Transceiver', 'Roadm') else 6, color=color),
            name=t,
            hovertext=texts,
            hoverinfo='text',
        )
        node_traces.append(trace)

    fig = go.Figure(
        data=[edge_trace] + node_traces,
        layout=go.Layout(
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=30),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=500,
        )
    )
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Tutorial 2: Run a Transmission Simulation
# ---------------------------------------------------------------------------
def tutorial_2():
    st.header("Tutorial 2: Run a Transmission Simulation")
    st.markdown("""
    In this tutorial you will select source and destination transceivers,
    run a full transmission simulation, and explore the results: GSNR per channel,
    power levels along the path, and the list of traversed elements.
    """)

    network_key = st.selectbox(
        "Select an example network",
        list(NETWORKS.keys()),
        format_func=lambda k: f"{k}",
        key='t2_network',
    )

    try:
        equipment, network = _load_network_cached(network_key)
    except Exception as e:
        st.error(f"Failed to load network: {e}")
        return

    transceivers = _get_transceivers(network)
    trx_uids = sorted(transceivers.keys())

    if len(trx_uids) < 2:
        st.error("Network needs at least 2 transceivers.")
        return

    col1, col2 = st.columns(2)
    with col1:
        source = st.selectbox("Source transceiver", trx_uids, key='t2_src')
    with col2:
        dest_options = [uid for uid in trx_uids if uid != source]
        destination = st.selectbox("Destination transceiver", dest_options, key='t2_dst')

    if st.button("Run Simulation", key='t2_run'):
        _run_simulation(equipment, network_key, source, destination)


def _run_simulation(equipment_orig, network_key, source, destination, power_dbm=None):
    """Run a simulation and display results. Reloads network from scratch to avoid state issues."""
    info = NETWORKS[network_key]

    with st.spinner("Loading network and running simulation..."):
        try:
            # Reload a fresh network for each simulation to avoid mutation issues
            equipment = load_equipments_and_configs(info['equipment'], [], [])
            network = load_network(info['topology'], equipment)
            SimParams.set_params({})

            kwargs = {}
            if power_dbm is not None:
                kwargs['args_power'] = power_dbm

            network, req, ref_req = designed_network(
                equipment, network, source, destination, **kwargs
            )
            path, propagations, powers_dbm_list, infos = transmission_simulation(
                equipment, network, req, ref_req
            )
        except Exception as e:
            st.error(f"Simulation failed: {e}")
            return None

    # Display results
    dest_node = path[-1]

    # Summary metrics
    st.subheader("Simulation Results")
    if hasattr(dest_node, 'snr') and dest_node.snr is not None:
        avg_gsnr = mean(dest_node.snr)
        avg_osnr = mean(dest_node.osnr_ase)
        avg_gsnr_01nm = mean(dest_node.snr_01nm)

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Avg GSNR (signal BW)", "%.2f dB" % avg_gsnr)
        with m2:
            st.metric("Avg OSNR ASE (signal BW)", "%.2f dB" % avg_osnr)
        with m3:
            st.metric("Avg GSNR (0.1 nm)", "%.2f dB" % avg_gsnr_01nm)

    # Path info
    spans = [s.params.length for s in path if isinstance(s, (Fiber, RamanFiber))]
    total_km = sum(spans) / 1000
    st.write(f"**Path:** {len(path)} elements, {len(spans)} fiber spans, "
             f"{'%.1f' % total_km} km total fiber")

    # Chart 1: GSNR spectrum
    st.subheader("GSNR Spectrum")
    _plot_gsnr_spectrum(path, infos)

    # Chart 2: Power along path
    st.subheader("Power Along Path")
    _plot_power_along_path(path)

    # Path elements table
    st.subheader("Path Elements")
    _show_path_table(path)

    return {
        'avg_gsnr': float(mean(dest_node.snr)) if dest_node.snr is not None else None,
        'avg_osnr': float(mean(dest_node.osnr_ase)) if dest_node.osnr_ase is not None else None,
        'path_length_km': sum(spans) / 1000,
        'num_elements': len(path),
        'num_spans': len(spans),
    }


def _plot_gsnr_spectrum(path, infos):
    """Plot GSNR, OSNR ASE, and OSNR NLI per channel at the destination."""
    dest = path[-1]
    if not hasattr(dest, 'snr') or dest.snr is None:
        st.warning("No SNR data available at destination.")
        return

    freqs_thz = [c.frequency * 1e-12 for c in infos.carriers]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=freqs_thz, y=list(dest.snr),
        mode='lines+markers', name='GSNR (signal BW)',
        marker=dict(size=3),
    ))
    fig.add_trace(go.Scatter(
        x=freqs_thz, y=list(dest.osnr_ase),
        mode='lines+markers', name='OSNR ASE (signal BW)',
        marker=dict(size=3),
    ))
    fig.add_trace(go.Scatter(
        x=freqs_thz, y=list(dest.osnr_nli),
        mode='lines+markers', name='OSNR NLI (signal BW)',
        marker=dict(size=3),
    ))
    fig.update_layout(
        xaxis_title='Frequency (THz)',
        yaxis_title='dB',
        height=400,
        margin=dict(l=50, r=20, t=30, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def _plot_power_along_path(path):
    """Plot signal power at each element along the path."""
    element_names = []
    power_dbm_vals = []

    for elem in path:
        if hasattr(elem, 'pch_out_db'):
            element_names.append(elem.uid)
            power_dbm_vals.append(elem.pch_out_db)
        elif isinstance(elem, Transceiver) and hasattr(elem, 'snr') and elem.snr is not None:
            # Final transceiver -- use carrier signal power
            element_names.append(elem.uid)
            carriers = getattr(elem, '_carriers', None)
            if carriers:
                power_dbm_vals.append(lin2db(carriers[0].signal * 1e3))
            else:
                power_dbm_vals.append(None)

    if not power_dbm_vals or all(v is None for v in power_dbm_vals):
        st.info("Power-along-path data not available for this simulation.")
        return

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(element_names))),
        y=power_dbm_vals,
        mode='lines+markers',
        name='Pch out (dBm)',
        text=element_names,
        hoverinfo='text+y',
    ))
    fig.update_layout(
        xaxis_title='Element Index',
        yaxis_title='Power (dBm)',
        height=400,
        margin=dict(l=50, r=20, t=30, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)


def _show_path_table(path):
    """Show a table of path elements with their types."""
    rows = []
    for i, elem in enumerate(path):
        row = {
            'Index': i,
            'UID': elem.uid,
            'Type': _element_type_name(elem),
        }
        if isinstance(elem, (Fiber, RamanFiber)):
            row['Length (km)'] = "%.1f" % (elem.params.length / 1000)
        else:
            row['Length (km)'] = '-'

        if hasattr(elem, 'pch_out_db') and elem.pch_out_db is not None:
            row['Pch out (dBm)'] = "%.2f" % elem.pch_out_db
        else:
            row['Pch out (dBm)'] = '-'

        rows.append(row)

    st.dataframe(rows, use_container_width=True)


# ---------------------------------------------------------------------------
# Tutorial 3: Explore Parameters
# ---------------------------------------------------------------------------
def tutorial_3():
    st.header("Tutorial 3: Explore Parameters")
    st.markdown("""
    In this tutorial you can tweak the channel reference power level and compare
    simulation results before and after the change. This demonstrates how input
    power affects GSNR and OSNR performance.
    """)

    network_key = st.selectbox(
        "Select an example network",
        list(NETWORKS.keys()),
        format_func=lambda k: f"{k}",
        key='t3_network',
    )

    try:
        equipment, network = _load_network_cached(network_key)
    except Exception as e:
        st.error(f"Failed to load network: {e}")
        return

    transceivers = _get_transceivers(network)
    trx_uids = sorted(transceivers.keys())

    if len(trx_uids) < 2:
        st.error("Network needs at least 2 transceivers.")
        return

    col1, col2 = st.columns(2)
    with col1:
        source = st.selectbox("Source transceiver", trx_uids, key='t3_src')
    with col2:
        dest_options = [uid for uid in trx_uids if uid != source]
        destination = st.selectbox("Destination transceiver", dest_options, key='t3_dst')

    # Default power from SI
    si_power = equipment['SI']['default'].power_dbm

    st.subheader("Power Comparison")
    st.markdown(f"The default channel power from equipment config is **{'%.1f' % si_power} dBm**.")

    p1, p2 = st.columns(2)
    with p1:
        power_a = st.slider(
            "Power A (dBm)", min_value=-6.0, max_value=6.0,
            value=float(si_power), step=0.5, key='t3_pa'
        )
    with p2:
        power_b = st.slider(
            "Power B (dBm)", min_value=-6.0, max_value=6.0,
            value=float(si_power) + 1.0, step=0.5, key='t3_pb'
        )

    if st.button("Compare", key='t3_compare'):
        st.subheader("Results with Power A = %.1f dBm" % power_a)
        result_a = _run_simulation(equipment, network_key, source, destination, power_dbm=power_a)

        st.markdown("---")

        st.subheader("Results with Power B = %.1f dBm" % power_b)
        result_b = _run_simulation(equipment, network_key, source, destination, power_dbm=power_b)

        # Comparison summary
        if result_a and result_b and result_a['avg_gsnr'] and result_b['avg_gsnr']:
            st.markdown("---")
            st.subheader("Comparison Summary")
            delta_gsnr = result_b['avg_gsnr'] - result_a['avg_gsnr']
            delta_osnr = result_b['avg_osnr'] - result_a['avg_osnr']
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric(
                    "Power change",
                    "%.1f dBm" % power_b,
                    delta="%+.1f dBm" % (power_b - power_a),
                )
            with c2:
                st.metric(
                    "Avg GSNR change",
                    "%.2f dB" % result_b['avg_gsnr'],
                    delta="%+.2f dB" % delta_gsnr,
                )
            with c3:
                st.metric(
                    "Avg OSNR change",
                    "%.2f dB" % result_b['avg_osnr'],
                    delta="%+.2f dB" % delta_osnr,
                )


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(
        page_title="GNPy Interactive Tutorial",
        page_icon="fiber_optic",
        layout="wide",
    )

    st.title("GNPy Interactive Tutorial")
    st.markdown("""
    Welcome to the GNPy interactive tutorial! GNPy is an open-source library for
    optical route planning and DWDM network optimization. Use the sidebar to
    navigate between tutorials.
    """)

    tutorial = st.sidebar.radio(
        "Select a tutorial",
        [
            "1. Your First Network",
            "2. Run a Transmission Simulation",
            "3. Explore Parameters",
        ],
    )

    if tutorial.startswith("1"):
        tutorial_1()
    elif tutorial.startswith("2"):
        tutorial_2()
    elif tutorial.startswith("3"):
        tutorial_3()

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "Built with [Streamlit](https://streamlit.io) and "
        "[GNPy](https://github.com/TelecomInfraProject/oopt-gnpy)"
    )


if __name__ == '__main__':
    main()
