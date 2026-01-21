"""
Configuration management for OCR Perfect.

Provides a hierarchical Pydantic-based configuration system with
preset support (default, high_quality, fast, cloud).
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Literal, Optional, Dict, Any

import yaml
from pydantic import BaseModel, Field


# Type aliases for clarity
PresetName = Literal["default", "high_quality", "fast", "cloud"]
OCRBackendName = Literal["tesseract", "document_ai", "vision_api"]
OutputFormat = Literal["docx", "json", "txt", "hocr", "pdf"]


class DeskewConfig(BaseModel):
    """Deskew preprocessing configuration."""

    enabled: bool = True
    """Whether to enable deskew correction."""

    method: Literal["hough", "projection", "tesseract"] = "hough"
    """Deskew detection method."""

    min_angle: float = 0.5
    """Minimum angle (degrees) to trigger correction."""

    max_angle: float = 15.0
    """Maximum angle (degrees) to attempt correction."""

    angle_resolution: float = 0.1
    """Angle detection resolution in degrees."""


class DenoiseConfig(BaseModel):
    """Denoise preprocessing configuration."""

    enabled: bool = True
    """Whether to enable denoising."""

    method: Literal["nlm", "bilateral", "morphological"] = "nlm"
    """Denoising method: Non-Local Means, Bilateral, or Morphological."""

    strength: int = 5
    """Denoising strength (higher = more aggressive)."""

    nlm_h: int = 10
    """NLM filter strength parameter."""

    nlm_template_window: int = 7
    """NLM template window size."""

    nlm_search_window: int = 21
    """NLM search window size."""


class ContrastConfig(BaseModel):
    """Contrast enhancement configuration."""

    enabled: bool = True
    """Whether to enable contrast enhancement."""

    method: Literal["clahe", "histogram", "gamma"] = "clahe"
    """Enhancement method."""

    clahe_clip_limit: float = 2.0
    """CLAHE clip limit."""

    clahe_tile_grid_size: int = 8
    """CLAHE tile grid size."""

    gamma: float = 1.0
    """Gamma correction value."""


class BinarizationConfig(BaseModel):
    """Binarization configuration."""

    enabled: bool = False
    """Whether to enable binarization (disabled by default, Tesseract handles it)."""

    method: Literal["otsu", "adaptive", "sauvola"] = "sauvola"
    """Binarization method."""

    block_size: int = 11
    """Adaptive threshold block size."""

    c: float = 2.0
    """Adaptive threshold constant."""

    sauvola_k: float = 0.5
    """Sauvola method k parameter."""

    sauvola_window_size: int = 25
    """Sauvola window size."""


class PreprocessingConfig(BaseModel):
    """Complete preprocessing pipeline configuration."""

    deskew: DeskewConfig = Field(default_factory=DeskewConfig)
    denoise: DenoiseConfig = Field(default_factory=DenoiseConfig)
    contrast: ContrastConfig = Field(default_factory=ContrastConfig)
    binarization: BinarizationConfig = Field(default_factory=BinarizationConfig)


class TesseractConfig(BaseModel):
    """Tesseract-specific configuration."""

    oem: int = 1
    """OCR Engine Mode: 0=Legacy, 1=LSTM, 2=Legacy+LSTM, 3=Default."""

    psm: int = 6
    """Page Segmentation Mode: 6=Uniform block of text."""

    timeout_s: int = 60
    """Timeout in seconds per page."""

    preserve_interword_spaces: bool = True
    """Whether to preserve spaces between words."""


class DocumentAIConfig(BaseModel):
    """Google Document AI configuration."""

    project_id: Optional[str] = None
    """GCP project ID."""

    location: str = "us"
    """Processor location."""

    processor_id: Optional[str] = None
    """Document OCR processor ID."""

    layout_parser_id: Optional[str] = None
    """Layout Parser processor ID (optional, for semantic analysis)."""


class VisionAPIConfig(BaseModel):
    """Google Cloud Vision API configuration."""

    project_id: Optional[str] = None
    """GCP project ID."""


class OCRConfig(BaseModel):
    """OCR backend configuration."""

    primary: OCRBackendName = "tesseract"
    """Primary OCR backend to use."""

    fallback: Optional[OCRBackendName] = None
    """Fallback backend if primary fails."""

    languages: List[str] = Field(default_factory=lambda: ["eng"])
    """Languages for OCR (ISO 639-3 codes)."""

    min_confidence: int = 40
    """Minimum confidence threshold (0-100)."""

    tesseract: TesseractConfig = Field(default_factory=TesseractConfig)
    """Tesseract-specific settings."""

    document_ai: DocumentAIConfig = Field(default_factory=DocumentAIConfig)
    """Document AI settings."""

    vision_api: VisionAPIConfig = Field(default_factory=VisionAPIConfig)
    """Vision API settings."""


class DetectionConfig(BaseModel):
    """PDF type detection configuration."""

    text_coverage_threshold: float = 0.02
    """Minimum text area ratio to consider as TEXT type."""

    image_coverage_threshold: float = 0.3
    """Minimum image area ratio to consider as SCANNED type."""

    quality_score_threshold: float = 0.6
    """Minimum text quality score (printable ratio, word sanity)."""

    min_text_length: int = 100
    """Minimum text length to consider for quality scoring."""


class MaskingConfig(BaseModel):
    """Trusted masking configuration for MIXED PDFs."""

    enabled: bool = True
    """Whether to enable trusted masking."""

    trust_threshold: float = 0.75
    """Minimum trust score to enable masking."""

    expansion_px: int = 2
    """Pixels to expand mask around vector text."""


class ThreePathConfig(BaseModel):
    """Three-path processing configuration."""

    render_dpi: int = 300
    """DPI for raster rendering."""

    max_pixels: int = 100_000_000
    """Maximum pixels per rendered page (memory limit)."""

    detection: DetectionConfig = Field(default_factory=DetectionConfig)
    """PDF type detection settings."""

    masking: MaskingConfig = Field(default_factory=MaskingConfig)
    """Trusted masking settings for MIXED mode."""


class TableDetectionConfig(BaseModel):
    """Table detection configuration."""

    enabled: bool = True
    """Whether to enable table detection."""

    use_vector: bool = True
    """Use vector line-based detection."""

    use_raster: bool = True
    """Use morphological raster detection."""

    use_img2table: bool = False
    """Use img2table ML detection (requires optional dependency)."""

    use_cloud: bool = False
    """Use cloud backend native table detection."""

    min_rows: int = 2
    """Minimum rows to consider as table."""

    min_cols: int = 2
    """Minimum columns to consider as table."""

    line_threshold: float = 0.5
    """Threshold for line detection confidence."""


class LayoutConfig(BaseModel):
    """Layout analysis configuration."""

    reading_order: Literal["xy_cut", "simple", "none"] = "xy_cut"
    """Reading order algorithm."""

    detect_headers: bool = True
    """Detect page headers."""

    detect_footers: bool = True
    """Detect page footers."""

    detect_columns: bool = True
    """Detect multi-column layouts."""

    header_region_ratio: float = 0.1
    """Top portion of page considered header region."""

    footer_region_ratio: float = 0.1
    """Bottom portion of page considered footer region."""


class MLConfig(BaseModel):
    """Machine learning configuration."""

    region_classifier_enabled: bool = False
    """Whether to use ML region classifier."""

    region_classifier_model: Optional[str] = None
    """Path to region classifier model file."""

    table_classifier_model: Optional[str] = None
    """Path to table classifier model file."""

    use_heuristic_fallback: bool = True
    """Use heuristic rules when ML model unavailable."""


class DocxOutputConfig(BaseModel):
    """DOCX output configuration."""

    preserve_formatting: bool = True
    """Preserve font styling (bold, italic, size)."""

    default_font: str = "Calibri"
    """Default font family."""

    default_font_size: float = 11.0
    """Default font size in points."""

    table_style: str = "Table Grid"
    """Table style name."""


class JsonOutputConfig(BaseModel):
    """JSON output configuration."""

    per_page: bool = True
    """Write one JSON file per page."""

    include_metadata: bool = True
    """Include processing metadata."""

    indent: int = 2
    """JSON indentation."""


class OutputConfig(BaseModel):
    """Output format configuration."""

    formats: List[OutputFormat] = Field(default_factory=lambda: ["docx", "json"])
    """Output formats to generate."""

    searchable_pdf_mode: Literal["native", "raster"] = "native"
    """Searchable PDF creation mode."""

    docx: DocxOutputConfig = Field(default_factory=DocxOutputConfig)
    """DOCX-specific settings."""

    json: JsonOutputConfig = Field(default_factory=JsonOutputConfig)
    """JSON-specific settings."""


class RuntimeConfig(BaseModel):
    """Runtime configuration."""

    max_workers: int = 4
    """Maximum parallel workers for batch processing."""

    fail_fast: bool = False
    """Stop on first error in batch processing."""

    log_level: Literal["debug", "info", "warning", "error"] = "info"
    """Logging level."""

    temp_dir: Optional[str] = None
    """Temporary directory for intermediate files."""


class AppConfig(BaseModel):
    """
    Root application configuration.

    Supports loading from YAML files and presets.
    """

    preset: PresetName = "default"
    """Active preset name."""

    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    """Runtime settings."""

    three_path: ThreePathConfig = Field(default_factory=ThreePathConfig)
    """Three-path processing settings."""

    preprocessing: PreprocessingConfig = Field(default_factory=PreprocessingConfig)
    """Image preprocessing settings."""

    ocr: OCRConfig = Field(default_factory=OCRConfig)
    """OCR backend settings."""

    tables: TableDetectionConfig = Field(default_factory=TableDetectionConfig)
    """Table detection settings."""

    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    """Layout analysis settings."""

    ml: MLConfig = Field(default_factory=MLConfig)
    """ML model settings."""

    output: OutputConfig = Field(default_factory=OutputConfig)
    """Output format settings."""

    @classmethod
    def from_preset(cls, preset: PresetName) -> AppConfig:
        """Create configuration from a preset."""
        if preset == "default":
            return cls(preset="default")

        elif preset == "high_quality":
            return cls(
                preset="high_quality",
                three_path=ThreePathConfig(render_dpi=400),
                preprocessing=PreprocessingConfig(
                    deskew=DeskewConfig(method="projection", angle_resolution=0.05),
                    denoise=DenoiseConfig(strength=7),
                    contrast=ContrastConfig(clahe_clip_limit=3.0),
                    binarization=BinarizationConfig(enabled=True),
                ),
                ocr=OCRConfig(min_confidence=20),
                ml=MLConfig(region_classifier_enabled=True),
            )

        elif preset == "fast":
            return cls(
                preset="fast",
                three_path=ThreePathConfig(render_dpi=200),
                preprocessing=PreprocessingConfig(
                    deskew=DeskewConfig(enabled=False),
                    denoise=DenoiseConfig(enabled=False),
                    contrast=ContrastConfig(enabled=False),
                ),
                ocr=OCRConfig(min_confidence=50),
                tables=TableDetectionConfig(use_img2table=False, use_raster=False),
            )

        elif preset == "cloud":
            return cls(
                preset="cloud",
                ocr=OCRConfig(
                    primary="document_ai",
                    fallback="tesseract",
                ),
                tables=TableDetectionConfig(use_cloud=True),
            )

        return cls(preset=preset)

    @classmethod
    def from_yaml(cls, path: Path | str) -> AppConfig:
        """Load configuration from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path) as f:
            data = yaml.safe_load(f)

        return cls.model_validate(data)

    @classmethod
    def load(
        cls,
        preset: Optional[PresetName] = None,
        config_path: Optional[Path | str] = None,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> AppConfig:
        """
        Load configuration with optional file and overrides.

        Priority: overrides > config_file > preset > default

        Args:
            preset: Preset name to start from
            config_path: Path to YAML config file
            overrides: Dictionary of override values

        Returns:
            Merged AppConfig
        """
        # Start with preset or default
        if preset:
            config = cls.from_preset(preset)
        else:
            config = cls()

        # Merge with file if provided
        if config_path:
            file_config = cls.from_yaml(config_path)
            config = cls.model_validate({
                **config.model_dump(),
                **file_config.model_dump(exclude_unset=True),
            })

        # Apply overrides
        if overrides:
            config = cls.model_validate({
                **config.model_dump(),
                **overrides,
            })

        return config

    def to_yaml(self, path: Path | str) -> None:
        """Save configuration to a YAML file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, sort_keys=False)


# Convenience function
def load_config(
    preset: Optional[PresetName] = None,
    config_path: Optional[Path | str] = None,
    **overrides: Any,
) -> AppConfig:
    """
    Load application configuration.

    Args:
        preset: Preset name (default, high_quality, fast, cloud)
        config_path: Path to YAML config file
        **overrides: Additional overrides as keyword arguments

    Returns:
        Configured AppConfig instance
    """
    return AppConfig.load(
        preset=preset,
        config_path=config_path,
        overrides=overrides if overrides else None,
    )
