"""Artel core — primary import surface backed by the current worker_core implementation."""

from __future__ import annotations

import worker_core as _worker_core
from worker_core import *  # noqa: F403

__all__ = getattr(_worker_core, "__all__", [])
__path__ = _worker_core.__path__
