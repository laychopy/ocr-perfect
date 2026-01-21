"""Unit tests for IR models."""

import pytest
import json
from ocr_perfect.ir import (
    Origin, Span, TextBlock, TableCell, TableBlock,
    ImageBlock, PageIR, DocumentIR, sort_blocks_xy_cut
)
from ocr_perfect.geometry import BBox, CoordinateSpace


class TestOrigin:
    """Test Origin enum."""

    def test_values(self):
        """Test origin values."""
        assert Origin.VECTOR.value == "vector"
        assert Origin.OCR.value == "ocr"
        assert Origin.MERGED.value == "merged"
        assert Origin.CLOUD.value == "cloud"

    def test_is_vector(self):
        """Test is_vector property."""
        assert Origin.VECTOR.is_vector
        assert not Origin.OCR.is_vector

    def test_is_ocr(self):
        """Test is_ocr property."""
        assert Origin.OCR.is_ocr
        assert Origin.CLOUD.is_ocr
        assert Origin.MERGED.is_ocr
        assert not Origin.VECTOR.is_ocr


class TestSpan:
    """Test Span model."""

    def test_basic_creation(self):
        """Create basic span."""
        span = Span(
            text="Hello",
            bbox=[100, 200, 150, 220],
            origin=Origin.VECTOR,
        )
        assert span.text == "Hello"
        assert span.bbox == [100, 200, 150, 220]
        assert span.origin == Origin.VECTOR
        assert span.confidence == 1.0

    def test_with_styling(self):
        """Create span with styling."""
        span = Span(
            text="Bold",
            bbox=[0, 0, 50, 20],
            origin=Origin.OCR,
            confidence=0.95,
            font_name="Arial",
            font_size_pt=12.0,
            is_bold=True,
            is_italic=False,
            color="#000000",
        )
        assert span.is_bold
        assert not span.is_italic
        assert span.font_name == "Arial"

    def test_serialization(self):
        """Span should serialize to JSON."""
        span = Span(text="Test", bbox=[0, 0, 10, 10], origin=Origin.OCR)
        data = span.model_dump()
        assert data["text"] == "Test"
        assert data["origin"] == "ocr"

    def test_deserialization(self):
        """Span should deserialize from JSON."""
        data = {
            "text": "Test",
            "bbox": [0, 0, 10, 10],
            "origin": "vector",
            "confidence": 1.0,
        }
        span = Span.model_validate(data)
        assert span.text == "Test"
        assert span.origin == Origin.VECTOR


class TestTextBlock:
    """Test TextBlock model."""

    def test_empty_block(self):
        """Create empty text block."""
        block = TextBlock(bbox=[0, 0, 100, 100])
        assert block.type == "text"
        assert block.role == "body"
        assert block.lines == []

    def test_with_lines(self):
        """Create block with lines."""
        span1 = Span(text="Hello", bbox=[0, 0, 50, 20], origin=Origin.VECTOR)
        span2 = Span(text="World", bbox=[55, 0, 100, 20], origin=Origin.VECTOR)
        block = TextBlock(
            bbox=[0, 0, 100, 50],
            lines=[[span1, span2]],
        )
        assert len(block.lines) == 1
        assert len(block.lines[0]) == 2

    def test_text_property(self):
        """Test full text extraction."""
        span1 = Span(text="Hello", bbox=[0, 0, 50, 20], origin=Origin.VECTOR)
        span2 = Span(text="World", bbox=[55, 0, 100, 20], origin=Origin.VECTOR)
        span3 = Span(text="!", bbox=[0, 25, 10, 45], origin=Origin.VECTOR)

        block = TextBlock(
            bbox=[0, 0, 100, 50],
            lines=[[span1, span2], [span3]],
        )

        assert block.text == "Hello World\n!"

    def test_all_spans(self):
        """Test flattening spans."""
        span1 = Span(text="A", bbox=[0, 0, 10, 10], origin=Origin.VECTOR)
        span2 = Span(text="B", bbox=[0, 0, 10, 10], origin=Origin.OCR)
        span3 = Span(text="C", bbox=[0, 0, 10, 10], origin=Origin.VECTOR)

        block = TextBlock(
            bbox=[0, 0, 100, 50],
            lines=[[span1, span2], [span3]],
        )

        spans = block.all_spans
        assert len(spans) == 3
        assert spans[0].text == "A"
        assert spans[2].text == "C"

    def test_avg_confidence(self):
        """Test average confidence calculation."""
        span1 = Span(text="A", bbox=[0, 0, 10, 10], origin=Origin.OCR, confidence=0.9)
        span2 = Span(text="B", bbox=[0, 0, 10, 10], origin=Origin.OCR, confidence=0.8)

        block = TextBlock(bbox=[0, 0, 100, 50], lines=[[span1, span2]])

        assert block.avg_confidence == pytest.approx(0.85)


class TestTableCell:
    """Test TableCell model."""

    def test_basic_cell(self):
        """Create basic cell."""
        cell = TableCell(text="Value")
        assert cell.text == "Value"
        assert cell.row_span == 1
        assert cell.col_span == 1
        assert not cell.is_header

    def test_merged_cell(self):
        """Create merged cell."""
        cell = TableCell(text="Header", row_span=1, col_span=2, is_header=True)
        assert cell.col_span == 2
        assert cell.is_header


class TestTableBlock:
    """Test TableBlock model."""

    def test_empty_table(self):
        """Create empty table."""
        table = TableBlock(bbox=[0, 0, 200, 100])
        assert table.type == "table"
        assert table.num_rows == 0
        assert table.num_cols == 0

    def test_with_rows(self):
        """Create table with rows."""
        table = TableBlock(
            bbox=[0, 0, 200, 100],
            rows=[
                [TableCell(text="A"), TableCell(text="B")],
                [TableCell(text="C"), TableCell(text="D")],
            ],
            has_header=True,
        )
        assert table.num_rows == 2
        assert table.num_cols == 2
        assert table.has_header

    def test_text_property(self):
        """Test table text extraction."""
        table = TableBlock(
            bbox=[0, 0, 200, 100],
            rows=[
                [TableCell(text="A"), TableCell(text="B")],
                [TableCell(text="C"), TableCell(text="D")],
            ],
        )
        assert table.text == "A\tB\nC\tD"


class TestPageIR:
    """Test PageIR model."""

    def test_basic_page(self):
        """Create basic page."""
        page = PageIR(
            page_number=1,
            width=612.0,
            height=792.0,
        )
        assert page.page_number == 1
        assert page.width == 612.0
        assert page.height == 792.0
        assert page.rotation == 0
        assert page.blocks == []

    def test_with_blocks(self):
        """Create page with mixed blocks."""
        text_block = TextBlock(bbox=[0, 0, 100, 50])
        table_block = TableBlock(bbox=[0, 60, 100, 150])
        image_block = ImageBlock(bbox=[0, 160, 100, 260], width=100, height=100)

        page = PageIR(
            page_number=1,
            width=612.0,
            height=792.0,
            blocks=[text_block, table_block, image_block],
        )

        assert len(page.blocks) == 3
        assert len(page.text_blocks) == 1
        assert len(page.table_blocks) == 1
        assert len(page.image_blocks) == 1

    def test_full_text(self):
        """Test full text extraction."""
        span = Span(text="Hello", bbox=[0, 0, 50, 20], origin=Origin.VECTOR)
        text_block = TextBlock(bbox=[0, 0, 100, 50], lines=[[span]])
        table_block = TableBlock(
            bbox=[0, 60, 100, 150],
            rows=[[TableCell(text="A"), TableCell(text="B")]],
        )

        page = PageIR(
            page_number=1,
            width=612.0,
            height=792.0,
            blocks=[text_block, table_block],
        )

        text = page.full_text
        assert "Hello" in text
        assert "A\tB" in text

    def test_word_count(self):
        """Test word count."""
        span = Span(text="Hello World", bbox=[0, 0, 100, 20], origin=Origin.VECTOR)
        text_block = TextBlock(bbox=[0, 0, 100, 50], lines=[[span]])

        page = PageIR(
            page_number=1,
            width=612.0,
            height=792.0,
            blocks=[text_block],
        )

        assert page.word_count == 2

    def test_serialization(self):
        """Page should serialize to JSON."""
        span = Span(text="Test", bbox=[0, 0, 50, 20], origin=Origin.VECTOR)
        block = TextBlock(bbox=[0, 0, 100, 50], lines=[[span]])
        page = PageIR(
            page_number=1,
            width=612.0,
            height=792.0,
            blocks=[block],
        )

        json_str = page.model_dump_json()
        data = json.loads(json_str)

        assert data["page_number"] == 1
        assert len(data["blocks"]) == 1


class TestDocumentIR:
    """Test DocumentIR model."""

    def test_basic_document(self):
        """Create basic document."""
        doc = DocumentIR(
            source_path="/path/to/doc.pdf",
            total_pages=5,
        )
        assert doc.source_path == "/path/to/doc.pdf"
        assert doc.total_pages == 5
        assert doc.pages == []

    def test_with_pages(self):
        """Create document with pages."""
        page1 = PageIR(page_number=1, width=612.0, height=792.0)
        page2 = PageIR(page_number=2, width=612.0, height=792.0)

        doc = DocumentIR(
            source_path="/path/to/doc.pdf",
            total_pages=2,
            pages=[page1, page2],
        )

        assert len(doc.pages) == 2
        assert doc.get_page(1) == page1
        assert doc.get_page(2) == page2
        assert doc.get_page(3) is None


class TestReadingOrder:
    """Test reading order sorting."""

    def test_simple_vertical(self):
        """Blocks stacked vertically should sort top to bottom."""
        blocks = [
            TextBlock(bbox=[0, 200, 100, 250]),  # Bottom
            TextBlock(bbox=[0, 0, 100, 50]),    # Top
            TextBlock(bbox=[0, 100, 100, 150]), # Middle
        ]

        sorted_blocks = sort_blocks_xy_cut(blocks)

        assert sorted_blocks[0].bbox[1] == 0    # Top
        assert sorted_blocks[1].bbox[1] == 100  # Middle
        assert sorted_blocks[2].bbox[1] == 200  # Bottom

    def test_simple_horizontal(self):
        """Blocks on same row should sort left to right."""
        blocks = [
            TextBlock(bbox=[200, 0, 300, 50]),  # Right
            TextBlock(bbox=[0, 0, 100, 50]),    # Left
            TextBlock(bbox=[100, 0, 200, 50]),  # Middle
        ]

        sorted_blocks = sort_blocks_xy_cut(blocks)

        assert sorted_blocks[0].bbox[0] == 0    # Left
        assert sorted_blocks[1].bbox[0] == 100  # Middle
        assert sorted_blocks[2].bbox[0] == 200  # Right

    def test_two_columns(self):
        """Two column layout should read column by column."""
        blocks = [
            TextBlock(bbox=[300, 0, 400, 50]),   # Right column, top
            TextBlock(bbox=[0, 0, 100, 50]),     # Left column, top
            TextBlock(bbox=[0, 60, 100, 110]),   # Left column, bottom
            TextBlock(bbox=[300, 60, 400, 110]), # Right column, bottom
        ]

        sorted_blocks = sort_blocks_xy_cut(blocks, min_col_gap=50)

        # Should read: left-top, left-bottom, right-top, right-bottom
        assert sorted_blocks[0].bbox[0] == 0 and sorted_blocks[0].bbox[1] == 0
        assert sorted_blocks[1].bbox[0] == 0 and sorted_blocks[1].bbox[1] == 60
        assert sorted_blocks[2].bbox[0] == 300 and sorted_blocks[2].bbox[1] == 0
        assert sorted_blocks[3].bbox[0] == 300 and sorted_blocks[3].bbox[1] == 60
