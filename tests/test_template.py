import shutil
from pathlib import Path
import pytest
from simplegals.core.config import Layout, ProjectConfig
from simplegals.core.template import build_image_records, render_gallery


def _make_output_images(out_dir: Path, names: list[str]) -> list[Path]:
    """Create stub output image files for template tests."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in names:
        p = out_dir / name
        p.write_bytes(b"FAKE")
        thumb = out_dir / f"{Path(name).stem}_thumb{Path(name).suffix}"
        thumb.write_bytes(b"FAKE")
        paths.append(p)
    return paths


def _make_records(out_dir: Path, names: list[str]) -> list[dict]:
    return [
        {
            "filename": n,
            "output_path": str(out_dir / n),
            "thumb_path": str(out_dir / f"{Path(n).stem}_thumb{Path(n).suffix}"),
            "caption": "",
            "alt": "",
            "include": True,
            "date": "2026-04-25",
            "size": "723.00 KiB",
            "item_page": f"{Path(n).stem}_item.html",
        }
        for n in names
    ]


def test_render_gallery_creates_index(tmp_path):
    out_dir = tmp_path / "out"
    names = ["a.jpg", "b.jpg", "c.jpg"]
    _make_output_images(out_dir, names)
    config = ProjectConfig(title="Test Gallery", layout=Layout(columns=2, rows=10))
    records = _make_records(out_dir, names)
    render_gallery(out_dir, config, records)
    assert (out_dir / "index.html").exists()


def test_render_gallery_creates_all_html(tmp_path):
    out_dir = tmp_path / "out"
    names = ["a.jpg", "b.jpg"]
    _make_output_images(out_dir, names)
    config = ProjectConfig(title="Gallery", layout=Layout(columns=2, rows=10))
    records = _make_records(out_dir, names)
    render_gallery(out_dir, config, records)
    assert (out_dir / "all.html").exists()


def test_render_gallery_creates_item_pages(tmp_path):
    out_dir = tmp_path / "out"
    names = ["a.jpg", "b.jpg"]
    _make_output_images(out_dir, names)
    config = ProjectConfig(layout=Layout(columns=2, rows=10))
    records = _make_records(out_dir, names)
    render_gallery(out_dir, config, records)
    assert (out_dir / "a_item.html").exists()
    assert (out_dir / "b_item.html").exists()


def test_render_gallery_paginates_correctly(tmp_path):
    out_dir = tmp_path / "out"
    # 6 images, 2 cols x 2 rows = 4 per page → 2 pages
    names = [f"img{i}.jpg" for i in range(6)]
    _make_output_images(out_dir, names)
    config = ProjectConfig(layout=Layout(columns=2, rows=2))
    records = _make_records(out_dir, names)
    render_gallery(out_dir, config, records)
    assert (out_dir / "index.html").exists()
    assert (out_dir / "page-2.html").exists()
    assert not (out_dir / "page-3.html").exists()


def test_render_gallery_excludes_flagged_images(tmp_path):
    out_dir = tmp_path / "out"
    names = ["a.jpg", "b.jpg"]
    _make_output_images(out_dir, names)
    config = ProjectConfig(layout=Layout(columns=2, rows=10))
    records = _make_records(out_dir, names)
    records[1]["include"] = False
    render_gallery(out_dir, config, records)
    index_html = (out_dir / "index.html").read_text(encoding="utf-8")
    assert "a_item.html" in index_html
    assert "b_item.html" not in index_html


def test_page2_prev_link_points_to_index(tmp_path):
    out_dir = tmp_path / "out"
    names = [f"img{i}.jpg" for i in range(6)]
    _make_output_images(out_dir, names)
    config = ProjectConfig(layout=Layout(columns=2, rows=2))
    records = _make_records(out_dir, names)
    render_gallery(out_dir, config, records)
    page2_html = (out_dir / "page-2.html").read_text(encoding="utf-8")
    assert 'href="index.html"' in page2_html
    assert 'href="page-1.html"' not in page2_html


def test_item_page_image_is_hyperlink(tmp_path):
    out_dir = tmp_path / "out"
    names = ["a.jpg"]
    _make_output_images(out_dir, names)
    config = ProjectConfig(layout=Layout(columns=2, rows=10))
    records = _make_records(out_dir, names)
    render_gallery(out_dir, config, records)
    item_html = (out_dir / "a_item.html").read_text(encoding="utf-8")
    assert '<a href=' in item_html
    assert 'a.jpg' in item_html


def test_item_page_has_download_link(tmp_path):
    out_dir = tmp_path / "out"
    names = ["a.jpg"]
    _make_output_images(out_dir, names)
    config = ProjectConfig(layout=Layout(columns=2, rows=10))
    records = _make_records(out_dir, names)
    render_gallery(out_dir, config, records)
    item_html = (out_dir / "a_item.html").read_text(encoding="utf-8")
    assert 'download' in item_html
    assert '💾' in item_html


def test_render_gallery_copies_css(tmp_path):
    out_dir = tmp_path / "out"
    names = ["a.jpg"]
    _make_output_images(out_dir, names)
    config = ProjectConfig()
    records = _make_records(out_dir, names)
    render_gallery(out_dir, config, records)
    assert (out_dir / "style.css").exists()
