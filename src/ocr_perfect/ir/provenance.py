"""Origin and provenance tracking for extracted content."""

from enum import Enum, auto


class Origin(str, Enum):
    """
    Provenance tracking for text extraction origin.

    Tracks how text was extracted to enable:
    - Quality analysis (vector vs OCR confidence)
    - Debugging (trace source of issues)
    - Output optimization (prefer vector when available)
    """

    VECTOR = "vector"
    """Text extracted from PDF vector content (embedded fonts)."""

    OCR = "ocr"
    """Text extracted via OCR from raster image."""

    MERGED = "merged"
    """Text combined from multiple sources (vector + OCR)."""

    CLOUD = "cloud"
    """Text extracted via cloud OCR (Document AI, Vision API)."""

    def __str__(self) -> str:
        return self.value

    @property
    def is_vector(self) -> bool:
        """Check if origin is vector-based."""
        return self == Origin.VECTOR

    @property
    def is_ocr(self) -> bool:
        """Check if origin involves OCR."""
        return self in (Origin.OCR, Origin.CLOUD, Origin.MERGED)
