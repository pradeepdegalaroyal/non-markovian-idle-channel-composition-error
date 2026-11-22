# Research gap

## State of the art (from the supplied literature)

Hardware noise models used to predict circuit error are almost always memoryless: each idle period or gate is replaced by a completely positive trace-preserving (CPTP) channel and the channels are multiplied. Breuer et al., 2016 (doi:10.1103/RevModPhys.88.021002) describe the limits of this picture: a Lindblad semigroup gives a memoryless dynamics, whereas real open systems show memory effects and revivals of coherence and correlations. They define and classify non-Markovianity, with the trace-distance revival criterion of Breuer, Laine and Piilo (BLP) as the central witness, and they point to using a small system as a probe of its environment. Tanimura, 2020 (doi:10.1063/5.0011599) reviews the hierarchical equations of motion (HEOM), a numerically "exact" route to non-perturbative, non-Markovian reduced dynamics when the weak-coupling and fast-bath approximations fail. The newest paper in the brief, Pita-Vidal et al., 2027 (doi:10.1016/j.physrep.2026.10.002), reviews hybrid semiconductor-superconductor qubits and stresses robustness against local noise and decoherence as a design goal. Tran et al., 2019 (doi:10.1038/s41586-019-0975-z) is an experimental materials paper (moiré excitons) that shows how a structured solid-state environment shapes the optical response; it is adjacent context for structured environments, not a noise-model reference.

**Scope note.** The literature brief for this project contains four papers (one recent, two landmark, one review). The related-work table below therefore has four rows; no reference outside the brief is cited.

## Related work table

| Paper | Year | Role | What it does | What it does NOT cover |
|---|---|---|---|---|
| Breuer et al. (doi:10.1103/RevModPhys.88.021002) | 2016 | landmark | Defines, classifies and quantifies memory effects of open quantum systems; BLP trace-distance witness; environment probing | Whether a witness measured on one uninterrupted evolution predicts the error of a gate sequence in which pulses interrupt the evolution |
| Tanimura (doi:10.1063/5.0011599) | 2020 | review | Overview of the hierarchical equations of motion for exact non-perturbative, non-Markovian dynamics | Circuit-level use: sequences of unitary gates between bath-driven idles, and how deep a hierarchy or truncation must be for gate-sequence error |
| Pita-Vidal et al. (doi:10.1016/j.physrep.2026.10.002) | 2027 | recent | Reviews hybrid semiconductor-superconductor qubits and noise-protected encodings | Quantitative noise-model comparison for gate sequences on such devices |
| Tran et al. (doi:10.1038/s41586-019-0975-z) | 2019 | landmark | Observes moiré-confined interlayer excitons in a van der Waals heterobilayer | Anything about gate sequences; included only as an example of a structured solid-state environment |

## Gap

The Colloquium and the HEOM review establish that memory matters and give tools to simulate it, but both treat a single, uninterrupted system-bath evolution. A gate-based processor interrupts the evolution with pulses, and standard error-budget practice then characterises one idle (for example by process tomography) and composes that channel. Two questions follow, and the brief does not answer them:

1. How large is the error of that composition against exact bath dynamics, as a function of how long the idle is compared with the bath memory time?
2. Does a trace-distance revival witness (BLP) tell a practitioner whether composition is safe?

## Hypotheses and success metrics

The system is a qubit coupled to one damped bath mode (a single-Lorentzian bath, exactly solvable and simulated here with a numerically exact Lindblad treatment). Units: the Markov-limit decay rate gamma; kappa is the bath-mode linewidth, so the memory time is 1/kappa; tau is the idle length. The test circuit is a random single-qubit Clifford sequence with ideal inversion, idle after every gate, scored by survival of the ground state.

- **H1.** A Markov amplitude-damping model whose rate is fitted to a lifetime (energy-relaxation time, T1) curve mispredicts the survival of the sequence by at least 10 % of the survival that is lost whenever kappa * tau < 3.
- **H2.** Composing the exact single-idle channel removes most of that error, but cross-gate memory leaves a residual relative error of at least 10 % whenever kappa * tau < 1.
- **H3.** The relative composition error is organised by kappa * tau, not by the BLP witness: the BLP measure of the idle is zero for kappa >= 4 gamma, yet the composition error there is not negligible.

Success metric: relative survival error = mean absolute difference between model and exact survival, divided by the mean survival lost (1 minus exact survival), computed per seed and reported as mean ± standard deviation over 5 seeds.

**Deviation from the first plan.** The first analysis used the unnormalised absolute error. It rises with total idle time and therefore hides the dependence on memory; the normalised metric above was introduced after seeing this. Both are saved in `results/`.

## Novelty (one sentence)

This project measures, against exact bath dynamics and with seeds and shot costs, where the standard "characterise one idle, compose it" noise model breaks for Clifford sequences, shows that the break is organised by the idle-to-memory-time ratio and not by the trace-distance revival witness, and quantifies the measurement cost of detecting it.

## Simulation scale

Everything is a classical simulation of one qubit plus one bath mode (Fock cut 5, dimension 12), validated against the closed-form solution. It makes no claim about a particular device and does not test quantum advantage.
