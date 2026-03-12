"""Artel web — primary import surface backed by the current worker_web implementation."""

from __future__ import annotations

import worker_web as _worker_web
from worker_web import *  # noqa: F403

__all__ = getattr(_worker_web, "__all__", [])
__path__ = _worker_web.__path__
