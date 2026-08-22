"""Importing this package registers every solver. Add new algorithms by
adding a module + an import line here — nothing else in the app should need
to change."""

from app.ml import (  # noqa: F401
    algorithm_picker,  # delegates to the solvers below at solve time, not import time
    neural_solver,
)
from app.solvers import (  # noqa: F401
    backtracking,
    constraint_propagation,
    dancing_links,
    fish_patterns,
    simulated_annealing,
)
from app.solvers.base import get_solver, list_solvers, register

__all__ = ["get_solver", "list_solvers", "register"]
