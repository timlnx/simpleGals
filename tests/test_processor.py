from pathlib import Path
import pytest
from PIL import Image
from simplegals.core.config import ProjectConfig
from simplegals.core.processor import (
    SGUI_THUMB_MAX,
    HTML_THUMB_MAX,
    generate_output,
    generate_sgui_thumb,
)


def test_sgui_thumb_jpg_is_created(tmp_path, test_jpg):
    meta_dir = tmp_path / ".meta"
    meta_dir.mkdir()
    result = generate_sgui_thumb(test_jpg, meta_dir)
    assert result.exists()
    assert result.name == "TEST_thumb.jpg"


def test_sgui_thumb_jpg_fits_in_max_bounds(tmp_path, test_jpg):
    meta_dir = tmp_path / ".meta"
    meta_dir.mkdir()
    result = generate_sgui_thumb(test_jpg, meta_dir)
    with Image.open(result) as img:
        assert img.size[0] <= SGUI_THUMB_MAX[0]
        assert img.size[1] <= SGUI_THUMB_MAX[1]


def test_sgui_thumb_png_produces_png(tmp_path, test_png):
    meta_dir = tmp_path / ".meta"
    meta_dir.mkdir()
    result = generate_sgui_thumb(test_png, meta_dir)
    assert result.suffix == ".png"
    assert result.exists()


def test_generate_output_jpg_creates_both_files(tmp_path, test_jpg):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    config = ProjectConfig(quality=85, copyright="© 2026 timlnx")
    output_path, thumb_path, _ = generate_output(test_jpg, out_dir, config)
    assert output_path.exists()
    assert thumb_path.exists()
    assert thumb_path.name == "TEST_thumb.jpg"


def test_generate_output_thumb_fits_html_bounds(tmp_path, test_jpg):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    config = ProjectConfig(quality=85)
    _, thumb_path, _ = generate_output(test_jpg, out_dir, config)
    with Image.open(thumb_path) as img:
        assert img.size[0] <= HTML_THUMB_MAX[0]
        assert img.size[1] <= HTML_THUMB_MAX[1]


def test_generate_output_png(tmp_path, test_png):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    config = ProjectConfig(quality=85)
    output_path, thumb_path, _ = generate_output(test_png, out_dir, config)
    assert output_path.suffix == ".png"
    assert thumb_path.suffix == ".png"


def test_generate_output_with_copyright_does_not_raise(tmp_path, test_jpg):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    config = ProjectConfig(quality=90, copyright="© 2026 timlnx")
    output_path, _, _ = generate_output(test_jpg, out_dir, config)
    assert output_path.exists()
