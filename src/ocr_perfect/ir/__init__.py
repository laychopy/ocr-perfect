"""Intermediate Representation module for document structure."""

from ocr_perfect.ir.provenance import Origin
from ocr_perfect.ir.models import (
    Span,
    TextBlock,
    TableCell,
    TableBlock,
    ImageBlock,
    PageIR,
    DocumentIR,
)
from ocr_perfect.ir.ordering import sort_blocks_xy_cut

__all__ = [
    "Origin",
    "Span",
    "TextBlock",
    "TableCell",
    "TableBlock",
    "ImageBlock",
    "PageIR",
    "DocumentIR",
    "sort_blocks_xy_cut",
]
