"""Bounding box operations for spatial computations."""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional

from ocr_perfect.geometry.spaces import CoordinateSpace


@dataclass
class BBox:
    """
    Axis-aligned bounding box with coordinate space tracking.

    All coordinates are in the specified space. Use TransformChain to
    convert between spaces.

    Attributes:
        x1: Left edge (minimum x)
        y1: Top edge (minimum y)
        x2: Right edge (maximum x)
        y2: Bottom edge (maximum y)
        space: The coordinate space this bbox is in
    """

    x1: float
    y1: float
    x2: float
    y2: float
    space: CoordinateSpace = CoordinateSpace.PDF

    def __post_init__(self):
        """Ensure coordinates are normalized (x1 <= x2, y1 <= y2)."""
        if self.x1 > self.x2:
            self.x1, self.x2 = self.x2, self.x1
        if self.y1 > self.y2:
            self.y1, self.y2 = self.y2, self.y1

    @property
    def width(self) -> float:
        """Width of the bounding box."""
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        """Height of the bounding box."""
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        """Area of the bounding box."""
        return self.width * self.height

    @property
    def center(self) -> Tuple[float, float]:
        """Center point (cx, cy) of the bounding box."""
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

    @property
    def corners(self) -> List[Tuple[float, float]]:
        """Four corners: top-left, top-right, bottom-right, bottom-left."""
        return [
            (self.x1, self.y1),
            (self.x2, self.y1),
            (self.x2, self.y2),
            (self.x1, self.y2),
        ]

    def to_list(self) -> List[float]:
        """Convert to [x1, y1, x2, y2] list for serialization."""
        return [self.x1, self.y1, self.x2, self.y2]

    @classmethod
    def from_list(cls, coords: List[float], space: CoordinateSpace = CoordinateSpace.PDF) -> BBox:
        """Create BBox from [x1, y1, x2, y2] list."""
        if len(coords) != 4:
            raise ValueError(f"Expected 4 coordinates, got {len(coords)}")
        return cls(coords[0], coords[1], coords[2], coords[3], space)

    @classmethod
    def from_xywh(
        cls, x: float, y: float, w: float, h: float,
        space: CoordinateSpace = CoordinateSpace.PDF
    ) -> BBox:
        """Create BBox from x, y, width, height."""
        return cls(x, y, x + w, y + h, space)

    def contains_point(self, x: float, y: float) -> bool:
        """Check if point (x, y) is inside the bbox."""
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def contains_bbox(self, other: BBox) -> bool:
        """Check if this bbox fully contains another bbox."""
        return (
            self.x1 <= other.x1 and
            self.y1 <= other.y1 and
            self.x2 >= other.x2 and
            self.y2 >= other.y2
        )

    def intersects(self, other: BBox) -> bool:
        """Check if this bbox intersects with another bbox."""
        return not (
            self.x2 < other.x1 or
            self.x1 > other.x2 or
            self.y2 < other.y1 or
            self.y1 > other.y2
        )

    def intersection(self, other: BBox) -> Optional[BBox]:
        """Return intersection bbox, or None if no intersection."""
        if not self.intersects(other):
            return None
        return BBox(
            max(self.x1, other.x1),
            max(self.y1, other.y1),
            min(self.x2, other.x2),
            min(self.y2, other.y2),
            self.space,
        )

    def union(self, other: BBox) -> BBox:
        """Return smallest bbox containing both bboxes."""
        return BBox(
            min(self.x1, other.x1),
            min(self.y1, other.y1),
            max(self.x2, other.x2),
            max(self.y2, other.y2),
            self.space,
        )

    def iou(self, other: BBox) -> float:
        """
        Compute Intersection over Union (IoU) with another bbox.

        Returns:
            IoU value between 0.0 and 1.0
        """
        inter = self.intersection(other)
        if inter is None:
            return 0.0

        inter_area = inter.area
        union_area = self.area + other.area - inter_area

        if union_area <= 0:
            return 0.0

        return inter_area / union_area

    def pad(self, padding: float) -> BBox:
        """Expand bbox by padding on all sides."""
        return BBox(
            self.x1 - padding,
            self.y1 - padding,
            self.x2 + padding,
            self.y2 + padding,
            self.space,
        )

    def pad_xy(self, pad_x: float, pad_y: float) -> BBox:
        """Expand bbox by different padding in x and y."""
        return BBox(
            self.x1 - pad_x,
            self.y1 - pad_y,
            self.x2 + pad_x,
            self.y2 + pad_y,
            self.space,
        )

    def scale(self, factor: float) -> BBox:
        """Scale bbox from center by factor."""
        cx, cy = self.center
        half_w = self.width * factor / 2
        half_h = self.height * factor / 2
        return BBox(
            cx - half_w,
            cy - half_h,
            cx + half_w,
            cy + half_h,
            self.space,
        )

    def clip(self, bounds: BBox) -> BBox:
        """Clip bbox to fit within bounds."""
        return BBox(
            max(self.x1, bounds.x1),
            max(self.y1, bounds.y1),
            min(self.x2, bounds.x2),
            min(self.y2, bounds.y2),
            self.space,
        )

    def with_space(self, space: CoordinateSpace) -> BBox:
        """Return a copy with a different coordinate space tag."""
        return BBox(self.x1, self.y1, self.x2, self.y2, space)

    def __repr__(self) -> str:
        return f"BBox({self.x1:.2f}, {self.y1:.2f}, {self.x2:.2f}, {self.y2:.2f}, {self.space})"
