"""
Runtime Data Configuration — Canonical storage outside Git worktree.

Architecture:
  SOURCE / DEPLOY CHECKOUT → immutable application code
  RUNTIME_DATA_ROOT       → persistent data outside repository
  OBJECT/ASSET STORAGE    → user media and generated media
  TEMP/SCRATCH            → disposable
  EVIDENCE                → verification artifacts only

Every path in this module reads RUNTIME_DATA_ROOT from the environment.
Default: ~/shunya_data/
"""

import os
from pathlib import Path
from typing import Union

PathLike = Union[str, os.PathLike[str]]


def _resolve(root: str) -> str:
    """Expand user home and resolve to absolute path."""
    return os.path.abspath(os.path.expanduser(root))


def runtime_data_root() -> str:
    """
    Canonical persistent-storage root.
    Override via env var RUNTIME_DATA_ROOT or default to ~/shunya_data/.
    """
    default = os.path.expanduser("~/shunya_data")
    root = os.environ.get("RUNTIME_DATA_ROOT", default)
    root = _resolve(root)
    os.makedirs(root, exist_ok=True)
    return root


def uploads_dir() -> str:
    """Uploaded user files (documents, images, etc.)."""
    p = os.path.join(runtime_data_root(), "uploads")
    os.makedirs(p, exist_ok=True)
    return p


def media_uploads_dir() -> str:
    """Generated media files (images, audio, video)."""
    p = os.path.join(runtime_data_root(), "media", "uploads")
    os.makedirs(p, exist_ok=True)
    return p


def screenshots_dir() -> str:
    """Coherence board screenshots."""
    p = os.path.join(runtime_data_root(), "screenshots")
    os.makedirs(p, exist_ok=True)
    return p


def reports_dir() -> str:
    """Generated PDF reports."""
    p = os.path.join(runtime_data_root(), "reports")
    os.makedirs(p, exist_ok=True)
    return p


def logs_dir() -> str:
    """Application logs."""
    p = os.path.join(runtime_data_root(), "logs")
    os.makedirs(p, exist_ok=True)
    return p


def static_uploads_dir() -> str:
    """Static uploaded files served via /static/uploads/."""
    p = os.path.join(runtime_data_root(), "static", "uploads")
    os.makedirs(p, exist_ok=True)
    return p


def backups_dir() -> str:
    """Database backups."""
    p = os.path.join(runtime_data_root(), "backups")
    os.makedirs(p, exist_ok=True)
    return p


def cache_dir() -> str:
    """Application cache files."""
    p = os.path.join(runtime_data_root(), "cache")
    os.makedirs(p, exist_ok=True)
    return p