# Plan: DWDM Optical Engineering Knowledge Base Wiki

## Context

Create a comprehensive, app-agnostic DWDM knowledge base as a Markdown file with Mermaid diagrams. The wiki will serve as a reusable knowledge base for empowering other applications (LLMs, planning tools, etc.) with optical networking domain knowledge. Content is grounded in formulas and concepts from the GNPy codebase but written in a general, vendor-neutral style.

## Output

**File:** `/workspaces/oopt-gnpy/docs/DWDM-Knowledge-Base.md`

## Structure

The wiki follows a bottom-up flow: physics fundamentals -> component behavior -> system metrics -> network-level planning.

### Sections (13 total)

1. **Fundamentals of DWDM** - WDM concept, ITU-T frequency grid (`f = 193.1 THz + n * 6.25 GHz`; note: 6.25 GHz is the **flexible grid** granularity per ITU-T G.694.1 [1]; fixed grids use 12.5/25/50/100 GHz channel spacing), frequency-wavelength relationship (`f = c/lambda`), power units (dBm/W/dB conversions), DWDM spectrum bands (O, E, S, C, L, U) [1]

2. **Fiber Propagation Physics** - Attenuation (`P(z) = P0 * exp(-az)`, Beer-Lambert law; note: `a` must be in Nepers/km, not dB/km) [2][3], chromatic dispersion (`beta2 = -(c/f)^2 * D / (2*pi*c)`, equivalent to standard form `beta2 = -D*lambda^2/(2*pi*c)`) [3], PMD (`dTau = PMD_coef * sqrt(L)`) [4], nonlinear coefficient (`gamma = 2*pi*f*n2/(c*Aeff)`, equivalent to `gamma = 2*pi*n2/(lambda*Aeff)`) [3], effective length (`Leff = (1-exp(-aL))/a`) [3]

3. **Nonlinear Interference (NLI)** - GN model (`NLI = sum P_cut * P_pump^2 * eta`) [5][6], GGN/EGN extensions [7], raised cosine spectral shaping (note: the classical GN model [5] assumes **rectangular** channel spectra; raised cosine shaping is handled by the **generalized GN (GGN)** and **EGN model** extensions [7]), SPM/XPM weights (16/27, 32/27) [5]

4. **Raman Effects** - SRS coupling coefficient [14], perturbative solver (orders 1-4) [13], numerical solver, spontaneous Raman noise with Bose-Einstein factor [3][15]

5. **Optical Amplification** - EDFA ASE noise: **corrected formula** `P_ASE = 2 * n_sp * (G-1) * h * f * B` (equivalently, `P_ASE = (NF * G - 1) * h * f * B` for total ASE power in both polarizations, where `NF` is the noise figure, `G` is the amplifier gain, `h` is Planck's constant, `f` is the optical frequency, and `B` is the optical bandwidth) [8]. ~~`P_ASE = h*f*B*NF`~~ (original formula was incomplete: missing the gain factor `(G-1)` and the factor of 2 for dual polarization). Noise figure models (fixed, variable, dual-stage cascade): **corrected Friis formula** `NF_total = NF1 + (NF2 - 1) / G1` [9]. ~~`NF = NF1 + (NF2-G1)/G1`~~ (original had `NF2-G1` instead of `NF2-1`). Gain profile/tilt/ripple, Raman amplification.

6. **Signal Quality Metrics** - SNR, OSNR (0.1nm normalization, ~12.5 GHz reference bandwidth at 1550 nm per ITU-T G.697) [12], GSNR (`P_sig/(P_ASE+P_NLI)`) [5], cascaded SNR (`1/SNR_total = sum 1/SNR_i`, valid for independent noise sources where noise powers add linearly) [11]

7. **Network Elements** - Transceiver, Fiber, EDFA, ROADM (add/drop/express; the document references "3 equalization schemes" — this should be clarified with the specific schemes intended, e.g., target power equalization, channel power equalization, and gain equalization, as literature does not standardize on a single set of three), Fused, class hierarchy diagram

8. **Spectral Information Model** - Per-channel signal/ASE/NLI ratio tracking, how noise is accumulated element-by-element

9. **Network Design and Planning** - Topology as directed graph, amplifier placement/selection, path computation (constrained shortest path), spectrum assignment (first-fit on flexible grid) [16]

10. **Transceiver Modes and Modulation** - DP-QPSK/16QAM/64QAM, bit rate formula (`Rb = Baud * log2(M) * Npol`) [3], Shannon capacity (`C = 2B*log2(1+SNR)`, the factor of 2 accounts for dual-polarization) [10][11], feasibility margins

11. **End-to-End Propagation Simulation** - Full signal flow from TX to RX through all elements

12. **Reference Tables** - Physical constants, typical fiber parameters (SSMF per ITU-T G.652 [17], LEAF), unit conversions, formula index

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

## Fact-Check Summary (v2 Changelog)

### Errors Corrected

| # | Section | Original | Corrected | Source |
|---|---------|----------|-----------|--------|
| 1 | 5 (Amplification) | `P_ASE = h*f*B*NF` | `P_ASE = 2*n_sp*(G-1)*h*f*B` | Desurvire [8] |
| 2 | 5 (Amplification) | `NF = NF1 + (NF2-G1)/G1` | `NF_total = NF1 + (NF2-1)/G1` | Friis [9] |

### Clarifications Added

| # | Section | Item | Clarification |
|---|---------|------|---------------|
| 3 | 1 (Fundamentals) | ITU-T grid formula | Noted that 6.25 GHz is flexi-grid granularity; fixed grids use different spacing |
| 4 | 7 (Network Elements) | "3 equalization schemes" | Flagged that literature does not standardize on exactly three; should specify which three |
| 5 | 3 (NLI) | Raised cosine in NLI | Clarified that classical GN model assumes rectangular spectra; raised cosine is GGN/EGN |

### Verified Correct (No Changes Needed)

- Fiber attenuation `P(z) = P0 * exp(-az)` (Beer-Lambert law) [2][3]
- Chromatic dispersion `beta2` formula [3]
- PMD `dTau = PMD_coef * sqrt(L)` [4]
- Nonlinear coefficient `gamma` [3]
- Effective length `Leff` [3]
- GSNR definition [5]
- Cascaded SNR formula [11]
- Shannon capacity with dual-polarization factor [10][11]
- Bit rate formula [3]
- Raman claims (SRS coupling, perturbative orders 1-4, Bose-Einstein factor) [3][13][14][15]
- DWDM spectrum bands (O, E, S, C, L, U) [1]
- OSNR 0.1 nm normalization [12]
- First-fit spectrum assignment [16]

## References

[1] ITU-T Recommendation G.694.1, "Spectral grids for WDM applications: DWDM frequency grid," International Telecommunication Union, 2020.

[2] Beer-Lambert Law (fiber attenuation). See also: Agrawal, G.P., *Nonlinear Fiber Optics*, 6th ed., Academic Press, 2019, Chapter 1.

[3] Agrawal, G.P., *Nonlinear Fiber Optics*, 6th ed., Academic Press, 2019. (Covers chromatic dispersion, nonlinear coefficient, effective length, Raman scattering, and modulation formats.)

[4] Wikipedia, "Polarization mode dispersion," https://en.wikipedia.org/wiki/Polarization_mode_dispersion. (PMD formula: differential group delay scales as square root of fiber length.)

[5] Poggiolini, P., "The GN Model of Non-Linear Propagation in Uncompensated Coherent Optical Systems," *Journal of Lightwave Technology*, vol. 30, no. 24, pp. 3857–3879, Dec. 2012.

[6] Poggiolini, P. et al., "A Detailed Analytical Derivation of the GN Model of Non-Linear Interference in Coherent Optical Transmission Systems," arXiv:1209.0394, 2012.

[7] Carena, A. et al., "EGN model of non-linear fiber propagation," *Optics Express*, vol. 22, no. 13, pp. 16335–16362, 2014.

[8] Desurvire, E., *Erbium-Doped Fiber Amplifiers: Principles and Applications*, Wiley-Interscience, 2002. (EDFA ASE noise formula: `P_ASE = 2*n_sp*(G-1)*h*f*B`.)

[9] Friis, H.T., "Noise Figures of Radio Receivers," *Proceedings of the IRE*, vol. 32, no. 7, pp. 419–422, July 1944. (Cascade noise figure formula: `NF_total = NF1 + (NF2-1)/G1`.)

[10] Shannon, C.E., "A Mathematical Theory of Communication," *Bell System Technical Journal*, vol. 27, pp. 379–423, 623–656, July & October 1948.

[11] Essiambre, R.-J. et al., "Capacity Limits of Optical Fiber Networks," *Journal of Lightwave Technology*, vol. 28, no. 4, pp. 662–701, Feb. 2010. (Dual-polarization Shannon limit and cascaded SNR.)

[12] ITU-T Recommendation G.697, "Optical monitoring for dense wavelength division multiplexing systems," International Telecommunication Union. (OSNR measured with 0.1 nm reference bandwidth, ~12.5 GHz at 1550 nm.)

[13] D'Amico, A. et al., "Perturbative Solution of Inter-Channel Stimulated Raman Scattering in Wideband WDM Transmission Systems," arXiv:2304.11756, 2023.

[14] Stolen, R.H. and Ippen, E.P., "Raman gain in glass optical waveguides," *Applied Physics Letters*, vol. 22, no. 6, pp. 276–278, 1973.

[15] Christodoulides, D.N. and Jander, R.B., "Evolution of stimulated Raman crosstalk in wavelength division multiplexed systems," *IEEE Photonics Technology Letters*, vol. 8, no. 12, pp. 1722–1724, 1996.

[16] Jinno, M. et al., "Spectrum-Efficient and Scalable Elastic Optical Path Network: Architecture, Benefits, and Enabling Technologies," *IEEE Communications Magazine*, vol. 47, no. 11, pp. 66–73, Nov. 2009.

[17] ITU-T Recommendation G.652, "Characteristics of a single-mode optical fibre and cable," International Telecommunication Union.
