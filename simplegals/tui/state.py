# simplegals/tui/state.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core.config import Layout, ProjectConfig, save_project_config


@dataclass
class StagedValue:
    original: Any
    new: Any

    @property
    def dirty(self) -> bool:
        return self.original != self.new


class StagedChangesModel:
    """Holds in-memory staged edits. Nothing hits disk until commit() is called."""

    def __init__(self) -> None:
        self._staged: dict[str, dict[str, StagedValue]] = {}

    def stage(self, key: str, field: str, original: Any, new_value: Any) -> None:
        """Stage a change. key is image filename or 'gallery'."""
        if key not in self._staged:
            self._staged[key] = {}
        if field not in self._staged[key]:
            self._staged[key][field] = StagedValue(original=original, new=new_value)
        else:
            self._staged[key][field].new = new_value

    def revert(self, key: str) -> None:
        """Remove all staged changes for key."""
        self._staged.pop(key, None)

    def is_dirty(self, key: str) -> bool:
        if key not in self._staged:
            return False
        return any(v.dirty for v in self._staged[key].values())

    def has_any_dirty(self) -> bool:
        return any(self.is_dirty(k) for k in self._staged)

    def get_current(self, key: str, field: str, default: Any = None) -> Any:
        """Return the staged new value, or default if not staged."""
        if key in self._staged and field in self._staged[key]:
            return self._staged[key][field].new
        return default

    def dirty_keys(self) -> list[str]:
        return [k for k in self._staged if self.is_dirty(k)]

    def _apply_to_config(self, key: str, config: ProjectConfig) -> ProjectConfig:
        if key not in self._staged:
            return config
        staged = {f: v.new for f, v in self._staged[key].items() if v.dirty}
        if not staged:
            return config
        if key == "gallery":
            layout_cols = staged.pop("layout_columns", None)
            layout_rows = staged.pop("layout_rows", None)
            for field, value in staged.items():
                if hasattr(config, field):
                    setattr(config, field, value)
            if layout_cols is not None or layout_rows is not None:
                config.layout = Layout(
                    columns=layout_cols if layout_cols is not None else config.layout.columns,
                    rows=layout_rows if layout_rows is not None else config.layout.rows,
                )
        else:
            images = dict(config.images)
            img = dict(images.get(key, {}))
            for field, value in staged.items():
                img[field] = value
            images[key] = img
            config.images = images
        return config

    def commit_key(self, key: str, config: ProjectConfig, config_path: Path) -> ProjectConfig:
        """Apply and save staged changes for key. Returns updated config."""
        config = self._apply_to_config(key, config)
        save_project_config(config, config_path)
        self._staged.pop(key, None)
        return config

    def commit_all(self, config: ProjectConfig, config_path: Path) -> ProjectConfig:
        """Apply and save all staged changes."""
        for key in list(self._staged.keys()):
            config = self.commit_key(key, config, config_path)
        return config
