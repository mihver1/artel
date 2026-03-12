"""Artel example extension — primary import surface backed by worker_ext_example."""

from __future__ import annotations

import worker_ext_example as _worker_ext_example
from worker_ext_example import *  # noqa: F403

__all__ = getattr(_worker_ext_example, "__all__", [])
__path__ = _worker_ext_example.__path__
