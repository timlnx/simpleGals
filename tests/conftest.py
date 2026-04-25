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
