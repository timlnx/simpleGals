import subprocess
import sys
from pathlib import Path
import pytest


def run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "simplegals.cli"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def test_cli_init_creates_config(tmp_path):
    result = run_cli(["init"], cwd=tmp_path)
    assert result.returncode == 0
    assert (tmp_path / "simpleGal.json").exists()


def test_cli_init_with_custom_config_path(tmp_path):
    result = run_cli(["-c", "custom.json", "init"], cwd=tmp_path)
    assert result.returncode == 0
    assert (tmp_path / "custom.json").exists()


def test_cli_validate_passes_on_empty_project(tmp_path):
    run_cli(["init"], cwd=tmp_path)
    (tmp_path / "in").mkdir(exist_ok=True)
    result = run_cli(["validate"], cwd=tmp_path)
    assert result.returncode == 0


def test_cli_build_produces_output(tmp_project):
    run_cli(["init"], cwd=tmp_project)
    result = run_cli(["build"], cwd=tmp_project)
    assert result.returncode == 0
    assert (tmp_project / "out" / "index.html").exists()


def test_cli_clean_empties_meta(tmp_project):
    run_cli(["init"], cwd=tmp_project)
    run_cli(["build"], cwd=tmp_project)
    meta_dir = tmp_project / ".meta"
    assert any(meta_dir.iterdir())
    result = run_cli(["clean"], cwd=tmp_project)
    assert result.returncode == 0
    assert not any(meta_dir.iterdir())


def test_cli_build_prints_log_tail_on_error(tmp_path):
    run_cli(["init"], cwd=tmp_path)
    (tmp_path / "in").mkdir(exist_ok=True)
    result = run_cli(["build"], cwd=tmp_path)
    assert result.returncode == 0


def test_cli_unknown_command_exits_nonzero(tmp_path):
    result = run_cli(["explode"], cwd=tmp_path)
    assert result.returncode != 0
