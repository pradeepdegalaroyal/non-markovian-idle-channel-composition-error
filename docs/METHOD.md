# Method

## Exact model (reference)

A qubit (excited state |1>) is resonantly coupled with strength g to one bosonic mode that decays at rate kappa; the Hamiltonian is g (sigma+ a + sigma- a-dagger) and the mode is damped by the Lindblad term kappa D[a]. With g = sqrt(gamma kappa) / 2 the Markov-limit qubit decay rate is gamma = 4 g^2 / kappa, and the memory time is 1/kappa. For kappa < 4 gamma the qubit population shows revivals. The Lindblad generator of qubit (x) mode (Fock cut 5) is exponentiated once per (kappa, tau) to give the idle superoperator. All times are in units of 1/gamma. The qubit-only population is validated against the closed-form damped Jaynes-Cummings amplitude (maximum deviation stored in `results/summary_stats.json`).

## Circuit

A sequence draws m random single-qubit Cliffords (24 elements), appends the ideal inverse, and applies an idle of length tau after every gate (gates are instantaneous and ideal in the main sweep). The score is the probability of finding the qubit in |0>, which is 1 without noise. m = 2, 5, 10, 20, 30; the main comparison uses m = 20. 60 sequences per seed and length; seeds 0-4.

## Compared noise models

| Model | Role | What it assumes |
|---|---|---|
| Exact bath (qubit plus damped mode) | reference | Bath memory kept across gates |
| Composed idle channel | standard quantum-device practice | One idle from a fresh bath is characterised as a 4 x 4 channel (process-tomography style) and repeated after every gate: the bath is reset at each gate |
| Markov amplitude damping, rate fitted to an energy-relaxation time (T1) curve | classical memoryless baseline (Lindblad semigroup) | Exponential decay, rate fitted to the exact population curve on [0, 3/gamma] |
| Markov amplitude damping, rate matched per idle | control | Rate chosen to reproduce the exact loss of one idle |

For this bath the control and the composed idle channel coincide to 4e-16 (the single-idle channel is amplitude damping with the same population loss and a positive coherence factor over the grid); they are reported as one model.

## Metrics

- Mean absolute survival error per sequence, averaged over sequences.
- Relative error = that error divided by (1 - mean exact survival).
- Bound on measurement cost: shots needed to resolve the mean survival difference at 3 standard errors, N = 9 p (1 - p) / delta^2 (binomial, one averaged curve).
- Breuer-Laine-Piilo (BLP) measure: summed positive increments of the trace distance of |0> and |1> over one uninterrupted evolution.
- Spearman rank correlation of relative error with the BLP measure and with kappa * tau over the 32 (kappa, tau) grid cells.

## Sweep

kappa in {0.25, 0.5, 1, 2, 4, 8, 16, 32} gamma, tau in {0.05, 0.1, 0.2, 0.4} / gamma, so kappa * tau ranges over 0.0125-12.8.

## Ablation

Fock-cut depth of the bath mode (1, 2, 3, 4) compared with a depth-8 reference at tau = 0.2 / gamma, m = 20, kappa in {0.25, 1, 4} gamma. This plays the role the hierarchy depth plays in the hierarchical equations of motion (HEOM).

## Noise / robustness sweep

Coherent X over-rotation of every gate by 0, 0.02, 0.05, 0.1 rad (the inverse gate included), tau = 0.2 / gamma, m = 20, kappa in {0.5, 2, 8} gamma, with the noise models built for ideal pulses (the realistic situation of a mismatched characterisation). A shot-cost analysis follows from the error table.

## Seeds and compute

Seeds 0-4 set the random Clifford sequences. Total run time about 70 s on the development laptop (CPU only, numpy).
