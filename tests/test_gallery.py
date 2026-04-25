import shutil
from pathlib import Path
import pytest
from simplegals.core.config import ProjectConfig
from simplegals.core.gallery import (
    SUPPORTED_EXTENSIONS,
    build,
    clean,
    ensure_project_dirs,
    scan_sources,
    validate,
)


def test_ensure_project_dirs_creates_directories(tmp_path):
    ensure_project_dirs(tmp_path)
    assert (tmp_path / "in").is_dir()
    assert (tmp_path / "out").is_dir()
    assert (tmp_path / ".meta").is_dir()


def test_scan_sources_finds_supported_images(tmp_project):
    in_dir = tmp_project / "in"
    sources = scan_sources(in_dir)
    assert len(sources) == 2
    assert all(s.suffix.lower() in SUPPORTED_EXTENSIONS for s in sources)


def test_scan_sources_ignores_unsupported(tmp_project):
    (tmp_project / "in" / "notes.txt").write_text("ignore me")
    sources = scan_sources(tmp_project / "in")
    assert all(s.suffix.lower() in SUPPORTED_EXTENSIONS for s in sources)


def test_validate_passes_on_clean_project(tmp_project):
    config = ProjectConfig()
    errors = validate(tmp_project, config)
    assert errors == []


def test_validate_catches_missing_images_in_config(tmp_project):
    config = ProjectConfig(images={"ghost.jpg": {"include": True}})
    errors = validate(tmp_project, config)
    assert any("ghost.jpg" in e for e in errors)


def test_clean_removes_meta_contents(tmp_project):
    meta_dir = tmp_project / ".meta"
    (meta_dir / "TEST.jpg.json").write_text("{}")
    (meta_dir / "build.jsonl").write_text("{}")
    clean(tmp_project)
    assert not list(meta_dir.glob("*"))


def test_build_produces_html_output(tmp_project):
    config = ProjectConfig(title="Test Build")
    log_path, had_errors = build(tmp_project, config)
    assert (tmp_project / "out" / "index.html").exists()
    assert (tmp_project / "out" / "all.html").exists()
    assert log_path.exists()
    assert not had_errors


def test_build_writes_build_log(tmp_project):
    config = ProjectConfig()
    log_path, _ = build(tmp_project, config)
    assert log_path.suffix == ".log"
    assert log_path.parent == tmp_project / ".meta"
    content = log_path.read_text()
    assert len(content) > 0


def test_build_appends_to_jsonl(tmp_project):
    config = ProjectConfig()
    build(tmp_project, config)
    jsonl = tmp_project / ".meta" / "build.jsonl"
    assert jsonl.exists()
    lines = [l for l in jsonl.read_text().splitlines() if l.strip()]
    assert len(lines) >= 1
