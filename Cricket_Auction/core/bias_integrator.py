"""Deprecated: bias_integrator removed during refactor.

The previous `BiasIntegrator` module used a fixed multiplier to adjust demand
scores and therefore violated the project constraint of avoiding hardcoded
boosts. Its functionality has been consolidated into `core.bias_modeler` and
the LLM-driven matching flow. Importing this module will raise ImportError to
prevent accidental usage.
"""

raise ImportError("core.bias_integrator has been removed. Use core.bias_modeler and the LLM-driven flow instead.")

