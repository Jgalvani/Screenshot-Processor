"""Shared type definitions."""

from typing import TypedDict


class BoundingBox(TypedDict):
    """Bounding box coordinates returned by Playwright's bounding_box()."""
    x: float
    y: float
    width: float
    height: float
