from __future__ import annotations

import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from ..core.processor import generate_sgui_thumb, generate_output
from ..core.config import ProjectConfig
from .progress import post_status


def _run_thumb_task(args: tuple) -> dict:
    source_str, meta_dir_str, _ = args
    source = Path(source_str)
    meta_dir = Path(meta_dir_str)
    try:
        generate_sgui_thumb(source, meta_dir)
        return {"type": "thumb", "file": source.name, "status": "done"}
    except Exception as e:
        return {"type": "thumb", "file": source.name, "status": "error", "error": str(e)}


def _run_output_task(args: tuple) -> dict:
    source_str, out_dir_str, config_dict = args
    source = Path(source_str)
    out_dir = Path(out_dir_str)
    config = ProjectConfig(**config_dict) if config_dict else ProjectConfig()
    try:
        generate_output(source, out_dir, config)
        return {"type": "output", "file": source.name, "status": "done"}
    except Exception as e:
        return {"type": "output", "file": source.name, "status": "error", "error": str(e)}


def dispatch(
    thumb_tasks: list[tuple],
    output_tasks: list[tuple],
    progress_queue: multiprocessing.Queue,
) -> None:
    """Submit all tasks to the pool and post status to progress_queue as each completes."""
    all_tasks = [(t, "thumb") for t in thumb_tasks] + [(t, "output") for t in output_tasks]

    with ProcessPoolExecutor() as executor:
        futures = {}
        for task, kind in all_tasks:
            if kind == "thumb":
                f = executor.submit(_run_thumb_task, task)
            else:
                f = executor.submit(_run_output_task, task)
            futures[f] = kind

        for future in as_completed(futures):
            try:
                result = future.result()
                progress_queue.put(result)
            except Exception as e:
                kind = futures[future]
                progress_queue.put({"type": kind, "file": "unknown", "status": "error", "error": str(e)})
