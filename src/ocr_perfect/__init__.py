"""
OCR Perfect - Production-ready OCR engine with multi-backend support.

Features:
- TransformChain for sub-pixel coordinate accuracy
- Three-path processing: TEXT, SCANNED, MIXED
- Multiple OCR backends: Tesseract, Document AI, Vision API
- Multiple output formats: DOCX, JSON, Searchable PDF, hOCR, TXT
"""

__version__ = "1.0.0"

from ocr_perfect.geometry.spaces import CoordinateSpace
from ocr_perfect.geometry.bboxes import BBox
from ocr_perfect.geometry.transforms import TransformChain
from ocr_perfect.ir.models import PageIR, TextBlock, TableBlock, ImageBlock, Span
from ocr_perfect.ir.provenance import Origin
from ocr_perfect.config import AppConfig

__all__ = [
    "CoordinateSpace",
    "BBox",
    "TransformChain",
    "PageIR",
    "TextBlock",
    "TableBlock",
    "ImageBlock",
    "Span",
    "Origin",
    "AppConfig",
]
