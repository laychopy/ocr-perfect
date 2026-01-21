"""Pytest fixtures for OCR Perfect tests."""

import pytest
from pathlib import Path

from ocr_perfect.config import AppConfig
from ocr_perfect.geometry import BBox, TransformChain, CoordinateSpace
from ocr_perfect.ir import PageIR, TextBlock, Span, Origin


@pytest.fixture
def default_config() -> AppConfig:
    """Default application configuration."""
    return AppConfig.from_preset("default")


@pytest.fixture
def high_quality_config() -> AppConfig:
    """High quality configuration."""
    return AppConfig.from_preset("high_quality")


@pytest.fixture
def sample_bbox() -> BBox:
    """Sample bounding box for testing."""
    return BBox(100.0, 200.0, 300.0, 400.0, CoordinateSpace.PDF)


@pytest.fixture
def sample_span() -> Span:
    """Sample span for testing."""
    return Span(
        text="Hello",
        bbox=[100.0, 200.0, 150.0, 220.0],
        origin=Origin.VECTOR,
        confidence=1.0,
        font_name="Arial",
        font_size_pt=12.0,
        is_bold=False,
    )


@pytest.fixture
def sample_text_block(sample_span: Span) -> TextBlock:
    """Sample text block for testing."""
    return TextBlock(
        bbox=[100.0, 200.0, 500.0, 300.0],
        role="body",
        lines=[[sample_span]],
    )


@pytest.fixture
def sample_page_ir(sample_text_block: TextBlock) -> PageIR:
    """Sample PageIR for testing."""
    return PageIR(
        page_number=1,
        width=612.0,
        height=792.0,
        blocks=[sample_text_block],
    )


@pytest.fixture
def identity_transform() -> TransformChain:
    """Identity transformation."""
    return TransformChain.identity()


@pytest.fixture
def scale_transform() -> TransformChain:
    """Scale transformation (72 DPI -> 300 DPI)."""
    return TransformChain.from_dpi_scale(72, 300)


@pytest.fixture
def test_fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"
