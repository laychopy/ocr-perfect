"""Unit tests for TransformChain."""

import pytest
import numpy as np
import math

from ocr_perfect.geometry import TransformChain, BBox, CoordinateSpace


class TestTransformChainBasics:
    """Test basic TransformChain operations."""

    def test_identity_creation(self):
        """Identity transform should not change coordinates."""
        t = TransformChain.identity()
        x, y = t.apply_point(100.0, 200.0)
        assert x == pytest.approx(100.0)
        assert y == pytest.approx(200.0)

    def test_identity_check(self):
        """is_identity should return True for identity matrix."""
        t = TransformChain.identity()
        assert t.is_identity()

    def test_scale_creation(self):
        """Scale transform should multiply coordinates."""
        t = TransformChain.scale(2.0, 3.0)
        x, y = t.apply_point(100.0, 200.0)
        assert x == pytest.approx(200.0)
        assert y == pytest.approx(600.0)

    def test_uniform_scale(self):
        """Uniform scale with single argument."""
        t = TransformChain.scale(2.0)
        x, y = t.apply_point(100.0, 200.0)
        assert x == pytest.approx(200.0)
        assert y == pytest.approx(400.0)

    def test_translate_creation(self):
        """Translate transform should offset coordinates."""
        t = TransformChain.translate(50.0, -30.0)
        x, y = t.apply_point(100.0, 200.0)
        assert x == pytest.approx(150.0)
        assert y == pytest.approx(170.0)

    def test_dpi_scale(self):
        """DPI scale should convert between DPI values."""
        t = TransformChain.from_dpi_scale(72, 300)
        x, y = t.apply_point(72.0, 72.0)
        assert x == pytest.approx(300.0)
        assert y == pytest.approx(300.0)


class TestTransformChainRotation:
    """Test rotation transformations."""

    def test_rotate_90_degrees(self):
        """90 degree rotation around origin."""
        t = TransformChain.rotate(90.0)
        x, y = t.apply_point(100.0, 0.0)
        assert x == pytest.approx(0.0, abs=1e-10)
        assert y == pytest.approx(100.0)

    def test_rotate_180_degrees(self):
        """180 degree rotation around origin."""
        t = TransformChain.rotate(180.0)
        x, y = t.apply_point(100.0, 50.0)
        assert x == pytest.approx(-100.0)
        assert y == pytest.approx(-50.0)

    def test_rotate_around_center(self):
        """Rotation around a custom center point."""
        center = (50.0, 50.0)
        t = TransformChain.rotate(90.0, center=center)

        # Point at center should not move
        x, y = t.apply_point(50.0, 50.0)
        assert x == pytest.approx(50.0)
        assert y == pytest.approx(50.0)

    def test_get_rotation_deg(self):
        """Extract rotation angle from transform."""
        t = TransformChain.rotate(45.0)
        angle = t.get_rotation_deg()
        assert angle == pytest.approx(45.0)


class TestTransformChainComposition:
    """Test transform composition."""

    def test_compose_identity(self):
        """Composing with identity should not change transform."""
        t = TransformChain.scale(2.0)
        identity = TransformChain.identity()
        composed = t.compose(identity)

        x, y = composed.apply_point(100.0, 100.0)
        assert x == pytest.approx(200.0)
        assert y == pytest.approx(200.0)

    def test_compose_scale_translate(self):
        """Compose scale then translate."""
        scale = TransformChain.scale(2.0)
        translate = TransformChain.translate(50.0, 50.0)

        # Apply scale first, then translate
        composed = scale.compose(translate)
        x, y = composed.apply_point(100.0, 100.0)

        # Expected: (100 * 2) + 50 = 250
        assert x == pytest.approx(250.0)
        assert y == pytest.approx(250.0)

    def test_compose_translate_scale(self):
        """Compose translate then scale (different order)."""
        translate = TransformChain.translate(50.0, 50.0)
        scale = TransformChain.scale(2.0)

        # Apply translate first, then scale
        composed = translate.compose(scale)
        x, y = composed.apply_point(100.0, 100.0)

        # Expected: (100 + 50) * 2 = 300
        assert x == pytest.approx(300.0)
        assert y == pytest.approx(300.0)

    def test_matmul_operator(self):
        """Test @ operator for composition."""
        scale = TransformChain.scale(2.0)
        translate = TransformChain.translate(50.0, 50.0)

        composed = scale @ translate
        x, y = composed.apply_point(100.0, 100.0)

        assert x == pytest.approx(250.0)
        assert y == pytest.approx(250.0)


class TestTransformChainInversion:
    """Test transform inversion."""

    def test_invert_scale(self):
        """Inverse of scale should divide."""
        t = TransformChain.scale(2.0)
        inv = t.invert()

        x, y = inv.apply_point(200.0, 200.0)
        assert x == pytest.approx(100.0)
        assert y == pytest.approx(100.0)

    def test_invert_translate(self):
        """Inverse of translate should offset opposite."""
        t = TransformChain.translate(50.0, 30.0)
        inv = t.invert()

        x, y = inv.apply_point(150.0, 130.0)
        assert x == pytest.approx(100.0)
        assert y == pytest.approx(100.0)

    def test_invert_caching(self):
        """Inverse should be cached."""
        t = TransformChain.scale(2.0)
        inv1 = t.invert()
        inv2 = t.invert()
        assert inv1 is inv2

    def test_double_invert(self):
        """Double inversion should return original."""
        t = TransformChain.scale(2.0, 3.0)
        double_inv = t.invert().invert()

        assert t == double_inv


class TestTransformChainRoundTrip:
    """Test round-trip accuracy - critical for coordinate precision."""

    def test_round_trip_scale(self):
        """Round-trip through scale transform."""
        t = TransformChain.from_dpi_scale(72, 300)

        original_x, original_y = 123.456, 789.012
        tx, ty = t.apply_point(original_x, original_y)
        rx, ry = t.invert().apply_point(tx, ty)

        assert rx == pytest.approx(original_x, abs=1e-10)
        assert ry == pytest.approx(original_y, abs=1e-10)

    def test_round_trip_complex(self):
        """Round-trip through complex composed transform."""
        scale = TransformChain.from_dpi_scale(72, 300)
        rotate = TransformChain.rotate(2.5, center=(500, 500))
        translate = TransformChain.translate(10, 20)

        full_chain = scale.compose(rotate).compose(translate)

        original_x, original_y = 100.0, 200.0
        tx, ty = full_chain.apply_point(original_x, original_y)
        rx, ry = full_chain.invert().apply_point(tx, ty)

        assert rx == pytest.approx(original_x, abs=1e-9)
        assert ry == pytest.approx(original_y, abs=1e-9)

    def test_round_trip_error_method(self):
        """Test round_trip_error method."""
        t = TransformChain.from_dpi_scale(72, 300)
        error = t.round_trip_error(100.0, 200.0)

        # Error should be negligible for simple transforms
        assert error < 1e-10

    def test_round_trip_error_sub_pixel(self):
        """Round-trip error should be less than 1 pixel at target DPI."""
        scale = TransformChain.from_dpi_scale(72, 300)
        rotate = TransformChain.rotate(5.0, center=(1000, 1500))

        full_chain = scale.compose(rotate)

        # Test multiple points
        test_points = [
            (0, 0), (100, 200), (500, 500),
            (612, 792), (306, 396),
        ]

        for x, y in test_points:
            error = full_chain.round_trip_error(x, y)
            # Error should be less than 1 pixel at 300 DPI
            # 1 pixel at 300 DPI = 72/300 = 0.24 points at PDF scale
            assert error < 0.01, f"Error at ({x}, {y}): {error}"


class TestTransformChainBBox:
    """Test bounding box transformation."""

    def test_apply_bbox_identity(self):
        """Identity should not change bbox."""
        t = TransformChain.identity()
        bbox = BBox(100, 200, 300, 400, CoordinateSpace.PDF)

        result = t.apply_bbox(bbox, CoordinateSpace.RASTER)

        assert result.x1 == pytest.approx(100)
        assert result.y1 == pytest.approx(200)
        assert result.x2 == pytest.approx(300)
        assert result.y2 == pytest.approx(400)
        assert result.space == CoordinateSpace.RASTER

    def test_apply_bbox_scale(self):
        """Scale should multiply bbox coordinates."""
        t = TransformChain.scale(2.0)
        bbox = BBox(100, 200, 300, 400, CoordinateSpace.PDF)

        result = t.apply_bbox(bbox, CoordinateSpace.RASTER)

        assert result.x1 == pytest.approx(200)
        assert result.y1 == pytest.approx(400)
        assert result.x2 == pytest.approx(600)
        assert result.y2 == pytest.approx(800)

    def test_apply_bbox_rotation(self):
        """Rotation should create AABB of rotated corners."""
        t = TransformChain.rotate(90.0)
        bbox = BBox(0, 0, 100, 50, CoordinateSpace.PDF)

        result = t.apply_bbox(bbox, CoordinateSpace.RASTER)

        # After 90 degree rotation:
        # (0,0) -> (0,0), (100,0) -> (0,100), (100,50) -> (-50,100), (0,50) -> (-50,0)
        assert result.x1 == pytest.approx(-50)
        assert result.y1 == pytest.approx(0)
        assert result.x2 == pytest.approx(0)
        assert result.y2 == pytest.approx(100)


class TestTransformChainExtraction:
    """Test extracting transform components."""

    def test_get_scale(self):
        """Extract scale factors."""
        t = TransformChain.scale(2.0, 3.0)
        sx, sy = t.get_scale()

        assert sx == pytest.approx(2.0)
        assert sy == pytest.approx(3.0)

    def test_get_translation(self):
        """Extract translation."""
        t = TransformChain.translate(50.0, 100.0)
        dx, dy = t.get_translation()

        assert dx == pytest.approx(50.0)
        assert dy == pytest.approx(100.0)

    def test_get_scale_from_composed(self):
        """Extract scale from composed transform."""
        scale = TransformChain.scale(2.0)
        translate = TransformChain.translate(50.0, 50.0)
        composed = scale.compose(translate)

        sx, sy = composed.get_scale()
        assert sx == pytest.approx(2.0)
        assert sy == pytest.approx(2.0)
