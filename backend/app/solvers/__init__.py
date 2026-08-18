"""Importing this package registers every solver. Add new algorithms by
adding a module + an import line here — nothing else in the app should need
to change."""

from app.solvers import backtracking, constraint_propagation, dancing_links  # noqa: F401
from app.solvers.base import get_solver, list_solvers, register

__all__ = ["get_solver", "list_solvers", "register"]
