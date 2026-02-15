# Plan: DWDM Optical Engineering Knowledge Base Wiki

## Context

Create a comprehensive, app-agnostic DWDM knowledge base as a Markdown file with Mermaid diagrams. The wiki will serve as a reusable knowledge base for empowering other applications (LLMs, planning tools, etc.) with optical networking domain knowledge. Content is grounded in formulas and concepts from the GNPy codebase but written in a general, vendor-neutral style.

## Output

**File:** `/workspaces/oopt-gnpy/docs/DWDM-Knowledge-Base.md`

## Structure

The wiki follows a bottom-up flow: physics fundamentals -> component behavior -> system metrics -> network-level planning.

### Sections (13 total)

1. **Fundamentals of DWDM** - WDM concept, ITU-T frequency grid (`f = 193.1 THz + n * 6.25 GHz`), frequency-wavelength relationship (`f = c/lambda`), power units (dBm/W/dB conversions)

2. **Fiber Propagation Physics** - Attenuation (`P(z) = P0 * exp(-az)`), chromatic dispersion (`beta2 = -(c/f)^2 * D / (2*pi*c)`), PMD (`dTau = PMD_coef * sqrt(L)`), nonlinear coefficient (`gamma = 2*pi*f*n2/(c*Aeff)`), effective length (`Leff = (1-exp(-aL))/a`)

3. **Nonlinear Interference (NLI)** - GN model (`NLI = sum P_cut * P_pump^2 * eta`), GGN extensions, raised cosine spectral shaping, SPM/XPM weights (16/27, 32/27)

4. **Raman Effects** - SRS coupling coefficient, perturbative solver (orders 1-4), numerical solver, spontaneous Raman with Bose-Einstein factor

5. **Optical Amplification** - EDFA ASE noise (`P_ASE = h*f*B*NF`), noise figure models (fixed, variable, dual-stage cascade `NF = NF1 + (NF2-G1)/G1`), gain profile/tilt/ripple, Raman amplification

6. **Signal Quality Metrics** - SNR, OSNR (0.1nm normalization), GSNR (`P_sig/(P_ASE+P_NLI)`), cascaded SNR (`1/SNR_total = sum 1/SNR_i`)

7. **Network Elements** - Transceiver, Fiber, EDFA, ROADM (add/drop/express, 3 equalization schemes), Fused, class hierarchy diagram

8. **Spectral Information Model** - Per-channel signal/ASE/NLI ratio tracking, how noise is accumulated element-by-element

9. **Network Design and Planning** - Topology as directed graph, amplifier placement/selection, path computation (constrained shortest path), spectrum assignment (first-fit on flexible grid)

10. **Transceiver Modes and Modulation** - DP-QPSK/16QAM/64QAM, bit rate formula (`Rb = Baud * log2(M) * Npol`), Shannon capacity (`C = 2B*log2(1+SNR)`), feasibility margins

11. **End-to-End Propagation Simulation** - Full signal flow from TX to RX through all elements

12. **Reference Tables** - Physical constants, typical fiber parameters (SSMF, LEAF), unit conversions, formula index

13. **Glossary** - All acronyms and terms

### Mermaid Diagrams (13)

| Diagram | Type | Section |
|---------|------|---------|
| DWDM Spectrum Bands | block-beta | 1.1 |
| Fiber Impairments Flow | flowchart | 2 |
| NLI Calculation Flow | flowchart | 3 |
| Raman Solver Decision Tree | flowchart | 4 |
| EDFA Signal Flow | flowchart | 5 |
| SNR Budget Cascade | flowchart | 6 |
| Network Element Hierarchy | classDiagram | 7 |
| Fiber Propagation Sequence | sequenceDiagram | 7 |
| ROADM Internal Paths | graph | 7 |
| SpectralInformation Structure | classDiagram | 8 |
| Network Topology Example | graph | 9 |
| Network Design Pipeline | flowchart | 9 |
| End-to-End Propagation | sequenceDiagram | 11 |

## Key Design Decisions

- **App-agnostic**: No GNPy-specific function names or file paths in the wiki body. Formulas use standard physics notation.
- **LaTeX formulas**: Use `$$...$$` block math and `$...$` inline math for all equations.
- **Mermaid for visuals**: All diagrams use Mermaid syntax for portability.
- **Self-contained**: Can be read independently without access to any codebase.
- **Knowledge-base oriented**: Written to empower LLMs and other applications with domain expertise.

## Verification

1. Render the Markdown locally or in GitHub to verify Mermaid diagrams render correctly
2. Spot-check formulas against the source code:
   - `gnpy/core/science_utils.py` for NLI/Raman formulas
   - `gnpy/core/elements.py` for fiber/EDFA/ROADM formulas
   - `gnpy/core/info.py` for SNR/GSNR/OSNR formulas
3. Verify all LaTeX math blocks are properly closed
4. Confirm no app-specific references leak into the general content
