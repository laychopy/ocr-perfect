"""Unit tests for BBox operations."""

import pytest
from ocr_perfect.geometry import BBox, CoordinateSpace


class TestBBoxBasics:
    """Test basic BBox operations."""

    def test_creation(self):
        """Basic bbox creation."""
        bbox = BBox(100, 200, 300, 400, CoordinateSpace.PDF)
        assert bbox.x1 == 100
        assert bbox.y1 == 200
        assert bbox.x2 == 300
        assert bbox.y2 == 400
        assert bbox.space == CoordinateSpace.PDF

    def test_normalization(self):
        """Coordinates should be normalized (x1 <= x2, y1 <= y2)."""
        bbox = BBox(300, 400, 100, 200)  # Reversed
        assert bbox.x1 == 100
        assert bbox.y1 == 200
        assert bbox.x2 == 300
        assert bbox.y2 == 400

    def test_default_space(self):
        """Default space should be PDF."""
        bbox = BBox(0, 0, 100, 100)
        assert bbox.space == CoordinateSpace.PDF

    def test_from_list(self):
        """Create bbox from list."""
        bbox = BBox.from_list([100, 200, 300, 400], CoordinateSpace.RASTER)
        assert bbox.x1 == 100
        assert bbox.y1 == 200
        assert bbox.x2 == 300
        assert bbox.y2 == 400
        assert bbox.space == CoordinateSpace.RASTER

    def test_from_list_invalid(self):
        """Invalid list should raise error."""
        with pytest.raises(ValueError):
            BBox.from_list([1, 2, 3])  # Only 3 elements

    def test_from_xywh(self):
        """Create bbox from x, y, width, height."""
        bbox = BBox.from_xywh(100, 200, 200, 200)
        assert bbox.x1 == 100
        assert bbox.y1 == 200
        assert bbox.x2 == 300
        assert bbox.y2 == 400

    def test_to_list(self):
        """Convert to list."""
        bbox = BBox(100, 200, 300, 400)
        assert bbox.to_list() == [100, 200, 300, 400]


class TestBBoxProperties:
    """Test BBox computed properties."""

    def test_width(self):
        """Width calculation."""
        bbox = BBox(100, 200, 300, 400)
        assert bbox.width == 200

    def test_height(self):
        """Height calculation."""
        bbox = BBox(100, 200, 300, 400)
        assert bbox.height == 200

    def test_area(self):
        """Area calculation."""
        bbox = BBox(100, 200, 300, 400)
        assert bbox.area == 40000

    def test_center(self):
        """Center point calculation."""
        bbox = BBox(100, 200, 300, 400)
        cx, cy = bbox.center
        assert cx == 200
        assert cy == 300

    def test_corners(self):
        """Corner points."""
        bbox = BBox(100, 200, 300, 400)
        corners = bbox.corners
        assert corners == [
            (100, 200),  # top-left
            (300, 200),  # top-right
            (300, 400),  # bottom-right
            (100, 400),  # bottom-left
        ]


class TestBBoxContainment:
    """Test containment checks."""

    def test_contains_point_inside(self):
        """Point inside bbox."""
        bbox = BBox(100, 200, 300, 400)
        assert bbox.contains_point(200, 300)

    def test_contains_point_outside(self):
        """Point outside bbox."""
        bbox = BBox(100, 200, 300, 400)
        assert not bbox.contains_point(50, 300)
        assert not bbox.contains_point(200, 500)

    def test_contains_point_boundary(self):
        """Point on boundary."""
        bbox = BBox(100, 200, 300, 400)
        assert bbox.contains_point(100, 200)  # Corner
        assert bbox.contains_point(200, 200)  # Edge

    def test_contains_bbox_fully_inside(self):
        """Inner bbox fully contained."""
        outer = BBox(100, 200, 300, 400)
        inner = BBox(150, 250, 250, 350)
        assert outer.contains_bbox(inner)

    def test_contains_bbox_partial(self):
        """Partial overlap is not containment."""
        outer = BBox(100, 200, 300, 400)
        partial = BBox(150, 250, 350, 350)  # Extends past x2
        assert not outer.contains_bbox(partial)


class TestBBoxIntersection:
    """Test intersection operations."""

    def test_intersects_overlap(self):
        """Overlapping boxes intersect."""
        a = BBox(100, 100, 200, 200)
        b = BBox(150, 150, 250, 250)
        assert a.intersects(b)
        assert b.intersects(a)

    def test_intersects_no_overlap(self):
        """Non-overlapping boxes don't intersect."""
        a = BBox(100, 100, 200, 200)
        b = BBox(300, 300, 400, 400)
        assert not a.intersects(b)
        assert not b.intersects(a)

    def test_intersects_adjacent(self):
        """Adjacent boxes (touching edges) don't intersect."""
        a = BBox(100, 100, 200, 200)
        b = BBox(200, 100, 300, 200)  # Shares edge at x=200
        assert not a.intersects(b)

    def test_intersection_overlap(self):
        """Get intersection of overlapping boxes."""
        a = BBox(100, 100, 200, 200)
        b = BBox(150, 150, 250, 250)
        inter = a.intersection(b)

        assert inter is not None
        assert inter.x1 == 150
        assert inter.y1 == 150
        assert inter.x2 == 200
        assert inter.y2 == 200

    def test_intersection_no_overlap(self):
        """No intersection returns None."""
        a = BBox(100, 100, 200, 200)
        b = BBox(300, 300, 400, 400)
        assert a.intersection(b) is None


class TestBBoxUnion:
    """Test union operations."""

    def test_union_overlap(self):
        """Union of overlapping boxes."""
        a = BBox(100, 100, 200, 200)
        b = BBox(150, 150, 250, 250)
        u = a.union(b)

        assert u.x1 == 100
        assert u.y1 == 100
        assert u.x2 == 250
        assert u.y2 == 250

    def test_union_no_overlap(self):
        """Union of non-overlapping boxes."""
        a = BBox(100, 100, 200, 200)
        b = BBox(300, 300, 400, 400)
        u = a.union(b)

        assert u.x1 == 100
        assert u.y1 == 100
        assert u.x2 == 400
        assert u.y2 == 400


class TestBBoxIoU:
    """Test Intersection over Union."""

    def test_iou_identical(self):
        """Identical boxes have IoU = 1.0."""
        a = BBox(100, 100, 200, 200)
        b = BBox(100, 100, 200, 200)
        assert a.iou(b) == pytest.approx(1.0)

    def test_iou_no_overlap(self):
        """Non-overlapping boxes have IoU = 0.0."""
        a = BBox(100, 100, 200, 200)
        b = BBox(300, 300, 400, 400)
        assert a.iou(b) == pytest.approx(0.0)

    def test_iou_partial(self):
        """Partial overlap has 0 < IoU < 1."""
        a = BBox(0, 0, 100, 100)      # Area = 10000
        b = BBox(50, 50, 150, 150)    # Area = 10000

        # Intersection: (50,50) to (100,100) = 50x50 = 2500
        # Union: 10000 + 10000 - 2500 = 17500
        # IoU = 2500/17500 = 1/7 ≈ 0.143

        iou = a.iou(b)
        assert iou == pytest.approx(2500 / 17500)


class TestBBoxModification:
    """Test bbox modification methods."""

    def test_pad(self):
        """Pad bbox equally on all sides."""
        bbox = BBox(100, 100, 200, 200)
        padded = bbox.pad(10)

        assert padded.x1 == 90
        assert padded.y1 == 90
        assert padded.x2 == 210
        assert padded.y2 == 210

    def test_pad_xy(self):
        """Pad with different x and y values."""
        bbox = BBox(100, 100, 200, 200)
        padded = bbox.pad_xy(10, 20)

        assert padded.x1 == 90
        assert padded.y1 == 80
        assert padded.x2 == 210
        assert padded.y2 == 220

    def test_scale(self):
        """Scale bbox from center."""
        bbox = BBox(100, 100, 200, 200)  # Center at (150, 150), size 100x100
        scaled = bbox.scale(2.0)

        assert scaled.x1 == pytest.approx(50)   # 150 - 100
        assert scaled.y1 == pytest.approx(50)   # 150 - 100
        assert scaled.x2 == pytest.approx(250)  # 150 + 100
        assert scaled.y2 == pytest.approx(250)  # 150 + 100

    def test_clip(self):
        """Clip bbox to bounds."""
        bbox = BBox(50, 50, 150, 150)
        bounds = BBox(0, 0, 100, 100)
        clipped = bbox.clip(bounds)

        assert clipped.x1 == 50
        assert clipped.y1 == 50
        assert clipped.x2 == 100
        assert clipped.y2 == 100

    def test_with_space(self):
        """Change coordinate space tag."""
        bbox = BBox(100, 100, 200, 200, CoordinateSpace.PDF)
        raster = bbox.with_space(CoordinateSpace.RASTER)

        assert raster.x1 == 100
        assert raster.y1 == 100
        assert raster.space == CoordinateSpace.RASTER
