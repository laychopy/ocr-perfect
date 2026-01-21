"""Coordinate space definitions for the OCR pipeline."""

from enum import Enum, auto


class CoordinateSpace(Enum):
    """
    Coordinate spaces used throughout the OCR pipeline.

    The pipeline maintains strict coordinate tracking to ensure sub-pixel
    accuracy when mapping between spaces.

    Spaces:
        PDF: Native PDF coordinates (72 DPI, origin at bottom-left typically)
        RASTER: Rendered image coordinates at target DPI (origin at top-left)
        PREPROCESSED: After preprocessing transforms (deskew, crop, etc.)
    """

    PDF = auto()
    """PDF coordinate space - 72 DPI, used for final output positioning."""

    RASTER = auto()
    """Raster image space - rendered at target DPI (e.g., 300 DPI)."""

    PREPROCESSED = auto()
    """Preprocessed image space - after deskew, denoise, etc."""

    def __str__(self) -> str:
        return self.name
