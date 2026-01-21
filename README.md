# OCR Perfect

Production-ready OCR engine with multi-backend support, sub-pixel coordinate accuracy, and intelligent PDF type detection.

## Features

- **TransformChain Architecture**: Sub-pixel accurate coordinate transformations using 3x3 affine matrices
- **Three-Path Processing**: Automatic detection and optimal handling of TEXT, SCANNED, and MIXED PDFs
- **Multi-Backend OCR**:
  - Tesseract (local, free)
  - Google Document AI (cloud, highest accuracy)
  - Google Vision API (cloud, simpler)
- **Trusted Masking**: Prevents duplicate text in mixed PDFs
- **Multiple Output Formats**: DOCX, JSON IR, Searchable PDF, hOCR, TXT
- **ML Region Classification**: Random Forest classifier with heuristic fallback
- **Docker Ready**: Multi-stage build with Tesseract + 10 languages

## Installation

```bash
# Basic installation
pip install -e .

# With cloud support
pip install -e ".[cloud]"

# With all features
pip install -e ".[all]"
```

### System Dependencies

```bash
# macOS
brew install tesseract tesseract-lang poppler ghostscript

# Ubuntu/Debian
sudo apt install tesseract-ocr tesseract-ocr-eng poppler-utils ghostscript
```

## Quick Start

```bash
# Convert PDF to DOCX (default preset)
ocr-perfect convert document.pdf -o output.docx

# High quality mode
ocr-perfect convert document.pdf -o output.docx --preset high_quality

# Fast mode
ocr-perfect convert document.pdf -o output.docx --preset fast

# Cloud mode (requires Google Cloud setup)
ocr-perfect convert document.pdf -o output.docx --preset cloud

# Detect PDF type
ocr-perfect detect document.pdf

# Batch processing
ocr-perfect batch ./pdfs/ -o ./output/ -j 4
```

## Architecture

```
                         CLI (convert/batch/detect)
                                   |
                    +-----------------------------+
                    |    DOCUMENT PROCESSOR       |
                    |  (streaming page iterator)  |
                    +-----------------------------+
                                   |
            +----------------------+----------------------+
            |                      |                      |
     +------v------+       +------v------+       +------v------+
     |  TEXT PATH  |       |SCANNED PATH |       | MIXED PATH  |
     |  (vector)   |       | (raster+OCR)|       | (masking)   |
     +-------------+       +-------------+       +-------------+
                                   |
                    +-----------------------------+
                    |         PAGE IR             |
                    |   (Single Source of Truth)  |
                    +-----------------------------+
                                   |
     +--------+--------+--------+--------+--------+
     |        |        |        |        |        |
   DOCX     JSON   SearchPDF  hOCR     TXT
```

## Configuration

### Presets

| Preset | DPI | Preprocessing | OCR Backend | Use Case |
|--------|-----|---------------|-------------|----------|
| `default` | 300 | Moderate | Tesseract | General use |
| `high_quality` | 400 | Full | Tesseract + ML | Best accuracy |
| `fast` | 200 | Minimal | Tesseract | Speed priority |
| `cloud` | 300 | Moderate | Document AI | Cloud accuracy |

### Custom Configuration

```yaml
# custom.yaml
preset: default

three_path:
  render_dpi: 350

preprocessing:
  deskew:
    enabled: true
    method: projection

ocr:
  languages: [eng, spa]
  min_confidence: 30

output:
  formats: [docx, json, pdf]
```

```bash
ocr-perfect convert doc.pdf -o out.docx --config custom.yaml
```

## Core Concepts

### TransformChain

Maintains sub-pixel accuracy across coordinate spaces:

```python
from ocr_perfect.geometry import TransformChain, BBox, CoordinateSpace

# PDF (72 DPI) -> Raster (300 DPI)
pdf_to_raster = TransformChain.from_dpi_scale(72, 300)

# Apply deskew rotation
deskew = TransformChain.rotate(2.5, center=(width/2, height/2))

# Compose transforms
full_chain = pdf_to_raster.compose(deskew)

# Map bbox back to PDF space
pdf_bbox = full_chain.invert().apply_bbox(ocr_bbox, CoordinateSpace.PDF)
```

### PageIR (Intermediate Representation)

Single source of truth for all outputs:

```python
from ocr_perfect.ir import PageIR, TextBlock, Span, Origin

page = PageIR(
    page_number=1,
    width=612.0,
    height=792.0,
    blocks=[
        TextBlock(
            bbox=[72, 72, 540, 100],
            lines=[[
                Span(text="Hello", bbox=[72, 72, 120, 90], origin=Origin.VECTOR),
                Span(text="World", bbox=[125, 72, 180, 90], origin=Origin.OCR),
            ]]
        )
    ]
)
```

## PDF Type Detection

| Type | Description | Processing |
|------|-------------|------------|
| TEXT | Vector text (embedded fonts) | Direct extraction, no OCR |
| SCANNED | Image-only pages | Full OCR pipeline |
| MIXED | Both text and images | Trusted masking + selective OCR |

## Project Structure

```
ocr-pipeline/
├── src/ocr_perfect/
│   ├── geometry/      # TransformChain, BBox, spaces
│   ├── ir/            # PageIR, TextBlock, TableBlock
│   ├── detection/     # PDF type detector
│   ├── ingest/        # Loader, TrustedMasker
│   ├── extraction/    # Vector, raster extractors
│   ├── preprocessing/ # Deskew, denoise, contrast
│   ├── ocr/           # Tesseract, DocumentAI, VisionAPI
│   ├── layout/        # Table detection, XY-Cut
│   ├── ml/            # Region classifier
│   └── output/        # DOCX, JSON, PDF writers
├── config/            # YAML presets
├── tests/             # Unit and integration tests
└── scripts/           # Batch processing helpers
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ocr_perfect

# Run specific module tests
pytest tests/unit/test_transforms.py
```

## Docker

```bash
# Build image
docker build -t ocr-perfect .

# Convert a file
docker run -v $(pwd):/data ocr-perfect convert /data/input.pdf -o /data/output.docx

# Batch processing
docker-compose run batch ./input/ -o ./output/ -j 4
```

## API Usage

```python
from ocr_perfect import AppConfig
from ocr_perfect.pipeline import DocumentProcessor

# Load configuration
config = AppConfig.from_preset("high_quality")

# Create processor
processor = DocumentProcessor(config)

# Process document (streaming)
for page_ir in processor.process("document.pdf"):
    print(f"Page {page_ir.page_number}: {page_ir.word_count} words")

# Export to DOCX
processor.export("document.pdf", "output.docx", format="docx")
```

## License

MIT License
