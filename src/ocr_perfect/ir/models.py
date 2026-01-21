"""
Intermediate Representation models for document structure.

PageIR is the single source of truth - all extraction paths produce it,
all output writers consume it.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, Field

from ocr_perfect.ir.provenance import Origin


class Span(BaseModel):
    """
    Smallest text unit with styling and provenance.

    A span represents a contiguous piece of text with consistent styling,
    along with its bounding box and extraction origin.
    """

    text: str
    """The text content."""

    bbox: List[float]
    """Bounding box [x1, y1, x2, y2] in PDF coordinate space."""

    origin: Origin = Origin.VECTOR
    """How this text was extracted."""

    confidence: float = 1.0
    """Confidence score (0.0-1.0). 1.0 for vector, variable for OCR."""

    # Optional styling (available for vector extraction)
    font_name: Optional[str] = None
    """Font name if known."""

    font_size_pt: Optional[float] = None
    """Font size in points if known."""

    is_bold: bool = False
    """Whether text is bold."""

    is_italic: bool = False
    """Whether text is italic."""

    color: Optional[str] = None
    """Text color as hex string (#RRGGBB) if known."""

    class Config:
        use_enum_values = True


class TextBlock(BaseModel):
    """
    A block of text content (paragraph, heading, etc.).

    Contains hierarchical structure: block > lines > spans.
    """

    type: Literal["text"] = "text"
    """Block type identifier."""

    role: str = "body"
    """Semantic role: body, header, footer, title, heading."""

    bbox: List[float]
    """Bounding box [x1, y1, x2, y2] in PDF coordinate space."""

    lines: List[List[Span]] = Field(default_factory=list)
    """Lines of spans. Each line is a list of spans."""

    @property
    def text(self) -> str:
        """Full text content of the block."""
        line_texts = []
        for line in self.lines:
            line_text = " ".join(span.text for span in line)
            line_texts.append(line_text)
        return "\n".join(line_texts)

    @property
    def all_spans(self) -> List[Span]:
        """Flatten all spans in the block."""
        return [span for line in self.lines for span in line]

    @property
    def avg_confidence(self) -> float:
        """Average confidence across all spans."""
        spans = self.all_spans
        if not spans:
            return 1.0
        return sum(s.confidence for s in spans) / len(spans)


class TableCell(BaseModel):
    """A cell in a table."""

    text: str
    """Cell text content."""

    row_span: int = 1
    """Number of rows this cell spans."""

    col_span: int = 1
    """Number of columns this cell spans."""

    is_header: bool = False
    """Whether this is a header cell."""

    bbox: Optional[List[float]] = None
    """Optional bounding box for the cell."""


class TableBlock(BaseModel):
    """
    A table structure with rows and cells.

    Supports merged cells via row_span and col_span.
    """

    type: Literal["table"] = "table"
    """Block type identifier."""

    bbox: List[float]
    """Bounding box [x1, y1, x2, y2] in PDF coordinate space."""

    rows: List[List[TableCell]] = Field(default_factory=list)
    """Table rows, each containing cells."""

    has_header: bool = False
    """Whether first row is a header."""

    detection_method: str = ""
    """How the table was detected: vector, raster, img2table, cloud."""

    @property
    def num_rows(self) -> int:
        """Number of rows in the table."""
        return len(self.rows)

    @property
    def num_cols(self) -> int:
        """Number of columns (from first row)."""
        if not self.rows:
            return 0
        return len(self.rows[0])

    @property
    def text(self) -> str:
        """Plain text representation of the table."""
        lines = []
        for row in self.rows:
            cells = [cell.text for cell in row]
            lines.append("\t".join(cells))
        return "\n".join(lines)


class ImageBlock(BaseModel):
    """
    An embedded image or figure.

    The actual image data is stored separately (not serialized to JSON).
    """

    type: Literal["image"] = "image"
    """Block type identifier."""

    role: str = "figure"
    """Role: figure, background, logo, signature."""

    bbox: List[float]
    """Bounding box [x1, y1, x2, y2] in PDF coordinate space."""

    image_format: str = "png"
    """Image format: png, jpeg, etc."""

    width: int = 0
    """Image width in pixels."""

    height: int = 0
    """Image height in pixels."""

    alt_text: Optional[str] = None
    """Alternative text description if available."""

    # Note: image_data is stored separately, not in the model
    # to keep JSON serialization efficient


# Union type for all block types
Block = Union[TextBlock, TableBlock, ImageBlock]


class PageIR(BaseModel):
    """
    Page Intermediate Representation - Single Source of Truth.

    All extraction paths produce PageIR, all output writers consume PageIR.
    This ensures consistent handling regardless of PDF type or OCR backend.
    """

    page_number: int
    """1-indexed page number."""

    width: float
    """Page width in PDF points (72 DPI)."""

    height: float
    """Page height in PDF points (72 DPI)."""

    rotation: int = 0
    """Page rotation in degrees (0, 90, 180, 270)."""

    blocks: List[Block] = Field(default_factory=list)
    """Ordered list of content blocks (text, table, image)."""

    metadata: Dict[str, Any] = Field(default_factory=dict)
    """
    Processing metadata including:
    - detection: Page type detection results
    - preprocessing: Steps applied
    - ocr_stats: OCR statistics if applicable
    - transforms: Coordinate transforms used
    """

    @property
    def text_blocks(self) -> List[TextBlock]:
        """Get only text blocks."""
        return [b for b in self.blocks if isinstance(b, TextBlock)]

    @property
    def table_blocks(self) -> List[TableBlock]:
        """Get only table blocks."""
        return [b for b in self.blocks if isinstance(b, TableBlock)]

    @property
    def image_blocks(self) -> List[ImageBlock]:
        """Get only image blocks."""
        return [b for b in self.blocks if isinstance(b, ImageBlock)]

    @property
    def full_text(self) -> str:
        """Extract all text from the page."""
        texts = []
        for block in self.blocks:
            if hasattr(block, "text"):
                texts.append(block.text)
        return "\n\n".join(texts)

    @property
    def word_count(self) -> int:
        """Approximate word count."""
        return len(self.full_text.split())

    class Config:
        arbitrary_types_allowed = True


class DocumentIR(BaseModel):
    """
    Document-level Intermediate Representation.

    Contains metadata and all pages for a complete document.
    """

    source_path: str
    """Path to the source PDF."""

    total_pages: int
    """Total number of pages in the document."""

    pages: List[PageIR] = Field(default_factory=list)
    """All page IRs."""

    metadata: Dict[str, Any] = Field(default_factory=dict)
    """
    Document-level metadata including:
    - title, author, creation_date
    - overall_type: TEXT, SCANNED, MIXED
    - processing_time
    - ocr_backend_used
    """

    @property
    def full_text(self) -> str:
        """Extract all text from the document."""
        return "\n\n---\n\n".join(page.full_text for page in self.pages)

    @property
    def total_word_count(self) -> int:
        """Total word count across all pages."""
        return sum(page.word_count for page in self.pages)

    def get_page(self, page_number: int) -> Optional[PageIR]:
        """Get page by 1-indexed page number."""
        for page in self.pages:
            if page.page_number == page_number:
                return page
        return None
