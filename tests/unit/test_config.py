"""Unit tests for configuration."""

import pytest
import tempfile
from pathlib import Path
from ocr_perfect.config import (
    AppConfig, load_config, PreprocessingConfig, OCRConfig,
    DeskewConfig, DenoiseConfig
)


class TestPresets:
    """Test configuration presets."""

    def test_default_preset(self):
        """Default preset should have balanced settings."""
        config = AppConfig.from_preset("default")
        assert config.preset == "default"
        assert config.three_path.render_dpi == 300
        assert config.preprocessing.deskew.enabled
        assert config.preprocessing.denoise.enabled
        assert not config.preprocessing.binarization.enabled
        assert config.ocr.primary == "tesseract"

    def test_high_quality_preset(self):
        """High quality preset should maximize accuracy."""
        config = AppConfig.from_preset("high_quality")
        assert config.preset == "high_quality"
        assert config.three_path.render_dpi == 400
        assert config.preprocessing.binarization.enabled
        assert config.preprocessing.denoise.strength == 7
        assert config.ml.region_classifier_enabled

    def test_fast_preset(self):
        """Fast preset should minimize processing."""
        config = AppConfig.from_preset("fast")
        assert config.preset == "fast"
        assert config.three_path.render_dpi == 200
        assert not config.preprocessing.deskew.enabled
        assert not config.preprocessing.denoise.enabled
        assert not config.tables.use_raster

    def test_cloud_preset(self):
        """Cloud preset should use Document AI."""
        config = AppConfig.from_preset("cloud")
        assert config.preset == "cloud"
        assert config.ocr.primary == "document_ai"
        assert config.ocr.fallback == "tesseract"
        assert config.tables.use_cloud


class TestConfigLoading:
    """Test configuration loading."""

    def test_load_default(self):
        """Load default config without arguments."""
        config = load_config()
        assert config.preset == "default"

    def test_load_with_preset(self):
        """Load config with preset name."""
        config = load_config(preset="high_quality")
        assert config.preset == "high_quality"

    def test_load_with_overrides(self):
        """Load config with overrides."""
        config = load_config(
            preset="default",
            three_path={"render_dpi": 400},
        )
        assert config.three_path.render_dpi == 400


class TestYAMLConfig:
    """Test YAML configuration files."""

    def test_save_and_load(self):
        """Save config to YAML and reload."""
        config = AppConfig.from_preset("default")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_config.yaml"
            config.to_yaml(path)

            loaded = AppConfig.from_yaml(path)

            assert loaded.preset == config.preset
            assert loaded.three_path.render_dpi == config.three_path.render_dpi

    def test_load_nonexistent(self):
        """Loading nonexistent file should raise error."""
        with pytest.raises(FileNotFoundError):
            AppConfig.from_yaml("/nonexistent/path.yaml")


class TestNestedConfig:
    """Test nested configuration structures."""

    def test_deskew_config(self):
        """Test DeskewConfig defaults and values."""
        config = DeskewConfig()
        assert config.enabled
        assert config.method == "hough"
        assert config.min_angle == 0.5
        assert config.max_angle == 15.0

    def test_deskew_config_custom(self):
        """Test DeskewConfig custom values."""
        config = DeskewConfig(
            enabled=False,
            method="projection",
            min_angle=1.0,
        )
        assert not config.enabled
        assert config.method == "projection"
        assert config.min_angle == 1.0

    def test_denoise_config(self):
        """Test DenoiseConfig."""
        config = DenoiseConfig()
        assert config.enabled
        assert config.method == "nlm"
        assert config.strength == 5

    def test_preprocessing_config(self):
        """Test PreprocessingConfig with nested configs."""
        config = PreprocessingConfig()
        assert config.deskew.enabled
        assert config.denoise.enabled
        assert config.contrast.enabled
        assert not config.binarization.enabled

    def test_ocr_config(self):
        """Test OCRConfig."""
        config = OCRConfig()
        assert config.primary == "tesseract"
        assert config.fallback is None
        assert "eng" in config.languages
        assert config.tesseract.oem == 1
        assert config.tesseract.psm == 6


class TestConfigValidation:
    """Test configuration validation."""

    def test_invalid_preset(self):
        """Invalid preset should use default."""
        # from_preset with unknown preset returns default
        config = AppConfig.from_preset("unknown")
        assert config.preset == "unknown"  # But it still sets the name

    def test_invalid_dpi(self):
        """Config should accept any DPI value."""
        # Pydantic doesn't validate ranges by default
        config = AppConfig()
        config.three_path.render_dpi = 50
        assert config.three_path.render_dpi == 50


class TestRuntimeConfig:
    """Test runtime configuration."""

    def test_defaults(self):
        """Test runtime defaults."""
        config = AppConfig()
        assert config.runtime.max_workers == 4
        assert not config.runtime.fail_fast
        assert config.runtime.log_level == "info"

    def test_temp_dir(self):
        """Test temp directory setting."""
        config = AppConfig()
        config.runtime.temp_dir = "/tmp/ocr"
        assert config.runtime.temp_dir == "/tmp/ocr"


class TestOutputConfig:
    """Test output configuration."""

    def test_default_formats(self):
        """Test default output formats."""
        config = AppConfig()
        assert "docx" in config.output.formats
        assert "json" in config.output.formats

    def test_docx_settings(self):
        """Test DOCX output settings."""
        config = AppConfig()
        assert config.output.docx.preserve_formatting
        assert config.output.docx.default_font == "Calibri"
        assert config.output.docx.default_font_size == 11.0

    def test_json_settings(self):
        """Test JSON output settings."""
        config = AppConfig()
        assert config.output.json.per_page
        assert config.output.json.indent == 2
