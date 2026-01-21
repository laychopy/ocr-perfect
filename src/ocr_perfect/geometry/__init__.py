"""Geometry module for coordinate spaces and transformations."""

from ocr_perfect.geometry.spaces import CoordinateSpace
from ocr_perfect.geometry.bboxes import BBox
from ocr_perfect.geometry.transforms import TransformChain

__all__ = ["CoordinateSpace", "BBox", "TransformChain"]
