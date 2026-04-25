import shutil
import pytest
from pathlib import Path

ASSETS_DIR = Path(__file__).parent / "assets"
TEST_JPG = ASSETS_DIR / "TEST.jpg"
TEST_PNG = ASSETS_DIR / "TEST.png"


@pytest.fixture
def test_jpg():
    return TEST_JPG


@pytest.fixture
def test_png():
    return TEST_PNG


@pytest.fixture
def assets_dir():
    return ASSETS_DIR


@pytest.fixture
def tmp_project(tmp_path, test_jpg, test_png):
    """Minimal project dir: in/, out/, .meta/ with both test images copied in."""
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    meta_dir = tmp_path / ".meta"
    for d in (in_dir, out_dir, meta_dir):
        d.mkdir()
    shutil.copy(test_jpg, in_dir / test_jpg.name)
    shutil.copy(test_png, in_dir / test_png.name)
    return tmp_path
