import numpy as np

from bathmem import (
    ModelParams,
    blp_measure,
    clifford_group,
    closed_form_population,
    idle_channel_qubit,
    markov_channel,
    pseudomode_idle_superop,
    random_sequences,
    shots_to_resolve,
    survival_channel,
    survival_exact,
)


def test_clifford_group_has_24_elements():
    assert len(clifford_group()) == 24


def test_pseudomode_matches_closed_form():
    for kappa in (0.25, 1.0, 8.0):
        s = idle_channel_qubit(ModelParams(1.0, kappa), 5, 0.6)
        assert abs(s[3, 3].real - closed_form_population(0.6, 1.0, kappa)) < 1e-8


def test_channels_are_trace_preserving():
    s = idle_channel_qubit(ModelParams(1.0, 2.0), 4, 0.3)
    # vec(identity) must be preserved by the adjoint: trace of every output is 1
    tr = np.array([1, 0, 0, 1])
    assert np.allclose(tr @ s, tr, atol=1e-9)
    assert np.allclose(tr @ markov_channel(1.0, 0.3), tr, atol=1e-12)


def test_noiseless_sequences_return_to_ground_state():
    gates = random_sequences(np.random.default_rng(1), 8, 10)
    assert np.allclose(survival_channel(gates, np.eye(4)), 1.0, atol=1e-10)


def _composition_error(kappa):
    gates = random_sequences(np.random.default_rng(2), 10, 20)
    p = ModelParams(1.0, kappa)
    exact = survival_exact(gates, pseudomode_idle_superop(p, 3, 0.4), 3)
    comp = survival_channel(gates, idle_channel_qubit(p, 3, 0.4))
    return np.abs(exact - comp).mean()


def test_composition_error_shrinks_for_wider_bath():
    # residual memory is O(gamma / kappa): wider bath -> smaller error
    assert _composition_error(64.0) < _composition_error(4.0)
    assert _composition_error(64.0) < 2e-2


def test_blp_vanishes_for_wide_bath_and_positive_for_narrow():
    assert blp_measure(1.0, 32.0) == 0.0
    assert blp_measure(1.0, 0.25) > 0.1


def test_shot_cost_scales_inverse_square():
    assert np.isclose(shots_to_resolve(0.5, 0.01) / shots_to_resolve(0.5, 0.02), 4.0)
