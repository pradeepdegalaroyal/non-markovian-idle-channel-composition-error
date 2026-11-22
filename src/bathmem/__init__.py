"""bathmem: exact bath-memory simulation of idle noise in gate sequences."""

from .circuits import (
    clifford_group,
    random_sequences,
    survival_channel,
    survival_exact,
)
from .model import (
    ModelParams,
    closed_form_population,
    coupling_from_rates,
    idle_channel_qubit,
    markov_channel,
    pseudomode_idle_superop,
)
from .nonmarkov import blp_measure, shots_to_resolve

__all__ = [
    "ModelParams",
    "closed_form_population",
    "coupling_from_rates",
    "idle_channel_qubit",
    "markov_channel",
    "pseudomode_idle_superop",
    "blp_measure",
    "shots_to_resolve",
    "clifford_group",
    "random_sequences",
    "survival_exact",
    "survival_channel",
]
__version__ = "0.1.0"
