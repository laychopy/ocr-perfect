"""
TransformChain - Composable affine transformations for coordinate mapping.

This is the foundation for coordinate accuracy in the OCR pipeline.
All bbox mappings between PDF, raster, and preprocessed spaces go through
TransformChain to maintain sub-pixel precision.
"""

from __future__ import annotations
import math
from typing import Tuple, Optional, List

import numpy as np

from ocr_perfect.geometry.spaces import CoordinateSpace
from ocr_perfect.geometry.bboxes import BBox


class TransformChain:
    """
    Composable 3x3 affine transformations for coordinate mapping.

    Invariants:
    - matrix is always 3x3
    - compose(A, B).apply(p) == B.apply(A.apply(p))
    - invert().compose(self) == identity (within float precision)

    Usage:
        # PDF (72 DPI) -> Raster (300 DPI)
        pdf_to_raster = TransformChain.scale(300/72, 300/72)

        # After deskew rotation
        deskew = TransformChain.rotate(2.5, center=(w/2, h/2))

        # Full chain: PDF -> Raster -> Preprocessed
        full_chain = pdf_to_raster.compose(deskew)

        # Map bbox from preprocessed back to PDF
        pdf_bbox = full_chain.invert().apply_bbox(prep_bbox, CoordinateSpace.PDF)
    """

    def __init__(self, matrix: np.ndarray):
        """
        Initialize with a 3x3 affine transformation matrix.

        Args:
            matrix: 3x3 numpy array representing affine transform
        """
        if matrix.shape != (3, 3):
            raise ValueError(f"Matrix must be 3x3, got {matrix.shape}")
        self._matrix = matrix.astype(np.float64)
        self._inverse: Optional[TransformChain] = None

    @property
    def matrix(self) -> np.ndarray:
        """The 3x3 transformation matrix."""
        return self._matrix.copy()

    @classmethod
    def identity(cls) -> TransformChain:
        """Create an identity transformation (no change)."""
        return cls(np.eye(3, dtype=np.float64))

    @classmethod
    def scale(cls, sx: float, sy: Optional[float] = None) -> TransformChain:
        """
        Create a scaling transformation.

        Args:
            sx: Scale factor in x direction
            sy: Scale factor in y direction (defaults to sx for uniform scaling)
        """
        if sy is None:
            sy = sx
        m = np.eye(3, dtype=np.float64)
        m[0, 0] = sx
        m[1, 1] = sy
        return cls(m)

    @classmethod
    def translate(cls, dx: float, dy: float) -> TransformChain:
        """
        Create a translation transformation.

        Args:
            dx: Translation in x direction
            dy: Translation in y direction
        """
        m = np.eye(3, dtype=np.float64)
        m[0, 2] = dx
        m[1, 2] = dy
        return cls(m)

    @classmethod
    def rotate(
        cls,
        angle_deg: float,
        center: Tuple[float, float] = (0.0, 0.0)
    ) -> TransformChain:
        """
        Create a rotation transformation.

        Args:
            angle_deg: Rotation angle in degrees (counter-clockwise positive)
            center: Center point for rotation (default: origin)
        """
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        cx, cy = center

        # Rotation around center: translate to origin, rotate, translate back
        # Combined into single matrix
        m = np.array([
            [cos_a, -sin_a, cx - cx * cos_a + cy * sin_a],
            [sin_a, cos_a, cy - cx * sin_a - cy * cos_a],
            [0, 0, 1],
        ], dtype=np.float64)

        return cls(m)

    @classmethod
    def from_dpi_scale(cls, source_dpi: float, target_dpi: float) -> TransformChain:
        """
        Create transformation for DPI conversion.

        Args:
            source_dpi: Source DPI (e.g., 72 for PDF)
            target_dpi: Target DPI (e.g., 300 for rendering)
        """
        scale = target_dpi / source_dpi
        return cls.scale(scale, scale)

    @classmethod
    def flip_y(cls, height: float) -> TransformChain:
        """
        Create vertical flip transformation (for PDF bottom-left to top-left).

        Args:
            height: Height of the coordinate space
        """
        m = np.array([
            [1, 0, 0],
            [0, -1, height],
            [0, 0, 1],
        ], dtype=np.float64)
        return cls(m)

    def compose(self, other: TransformChain) -> TransformChain:
        """
        Compose this transform with another (apply self first, then other).

        Args:
            other: Transform to apply after this one

        Returns:
            New TransformChain representing the composition
        """
        # Matrix multiplication: other @ self means apply self first, then other
        return TransformChain(other._matrix @ self._matrix)

    def invert(self) -> TransformChain:
        """
        Return the inverse transformation.

        The result is cached for efficiency.

        Raises:
            np.linalg.LinAlgError: If matrix is singular
        """
        if self._inverse is None:
            inv_matrix = np.linalg.inv(self._matrix)
            self._inverse = TransformChain(inv_matrix)
            self._inverse._inverse = self  # Cache bidirectionally
        return self._inverse

    def apply_point(self, x: float, y: float) -> Tuple[float, float]:
        """
        Transform a single point.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Tuple of (transformed_x, transformed_y)
        """
        vec = np.array([x, y, 1.0], dtype=np.float64)
        result = self._matrix @ vec
        return (float(result[0]), float(result[1]))

    def apply_points(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Transform multiple points efficiently.

        Args:
            points: List of (x, y) tuples

        Returns:
            List of transformed (x, y) tuples
        """
        if not points:
            return []

        # Create Nx3 matrix of homogeneous coordinates
        pts = np.array([[x, y, 1.0] for x, y in points], dtype=np.float64)
        # Transform: (N, 3) @ (3, 3).T = (N, 3)
        transformed = pts @ self._matrix.T
        return [(float(p[0]), float(p[1])) for p in transformed]

    def apply_bbox(self, bbox: BBox, target_space: CoordinateSpace) -> BBox:
        """
        Transform a bounding box.

        Transforms all four corners and returns the axis-aligned bounding box
        of the transformed corners.

        Args:
            bbox: Source bounding box
            target_space: Coordinate space for the result

        Returns:
            Transformed BBox in target_space
        """
        corners = bbox.corners
        transformed = self.apply_points(corners)

        xs = [p[0] for p in transformed]
        ys = [p[1] for p in transformed]

        return BBox(
            min(xs), min(ys), max(xs), max(ys),
            target_space
        )

    def round_trip_error(self, x: float, y: float) -> float:
        """
        Compute round-trip error for a point (self -> inverse -> original).

        This is useful for testing coordinate accuracy.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Euclidean distance between original and recovered point
        """
        tx, ty = self.apply_point(x, y)
        rx, ry = self.invert().apply_point(tx, ty)
        return math.sqrt((rx - x) ** 2 + (ry - y) ** 2)

    def is_identity(self, tolerance: float = 1e-10) -> bool:
        """Check if this transform is effectively identity."""
        return np.allclose(self._matrix, np.eye(3), atol=tolerance)

    def get_scale(self) -> Tuple[float, float]:
        """
        Extract approximate scale factors from the matrix.

        Returns:
            Tuple of (scale_x, scale_y)
        """
        # Scale is the length of the transformed unit vectors
        sx = math.sqrt(self._matrix[0, 0] ** 2 + self._matrix[1, 0] ** 2)
        sy = math.sqrt(self._matrix[0, 1] ** 2 + self._matrix[1, 1] ** 2)
        return (sx, sy)

    def get_rotation_deg(self) -> float:
        """
        Extract approximate rotation angle from the matrix.

        Returns:
            Rotation angle in degrees
        """
        return math.degrees(math.atan2(self._matrix[1, 0], self._matrix[0, 0]))

    def get_translation(self) -> Tuple[float, float]:
        """
        Extract translation from the matrix.

        Returns:
            Tuple of (dx, dy)
        """
        return (float(self._matrix[0, 2]), float(self._matrix[1, 2]))

    def __repr__(self) -> str:
        scale = self.get_scale()
        rot = self.get_rotation_deg()
        trans = self.get_translation()
        return (
            f"TransformChain(scale=({scale[0]:.3f}, {scale[1]:.3f}), "
            f"rotation={rot:.2f}deg, translation=({trans[0]:.2f}, {trans[1]:.2f}))"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TransformChain):
            return False
        return np.allclose(self._matrix, other._matrix)

    def __matmul__(self, other: TransformChain) -> TransformChain:
        """Allow using @ operator for composition: a @ b = a.compose(b)."""
        return self.compose(other)
