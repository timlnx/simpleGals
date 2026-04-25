# simplegals/tui/file_panel.py
from __future__ import annotations

from pathlib import Path
from typing import Callable

import urwid


def _truncate(text: str, width: int) -> str:
    """Truncate text to width, appending ellipsis if needed."""
    if len(text) <= width:
        return text
    return text[: max(0, width - 1)] + "…"


class SelectableImageRow(urwid.WidgetWrap):
    """One selectable row in the file list."""

    def __init__(self, filename: str, dirty: bool = False) -> None:
        self.filename = filename
        self.dirty = dirty
        self._icon = urwid.SelectableIcon(self._make_label(), cursor_position=0)
        super().__init__(self._make_attrmap())

    def _make_attrmap(self) -> urwid.AttrMap:
        return urwid.AttrMap(self._icon, "dirty" if self.dirty else None, "selected")

    @property
    def label(self) -> str:
        return self._icon.text

    def _make_label(self) -> str:
        return ("* " if self.dirty else "  ") + self.filename

    def update_dirty(self, dirty: bool) -> None:
        self.dirty = dirty
        self._icon.set_text(self._make_label())
        self._w = self._make_attrmap()

    def selectable(self) -> bool:
        return True

    def keypress(self, size, key: str) -> str:
        return key


class FilePanel(urwid.WidgetWrap):
    """Scrollable list of source images with dirty indicators and nav callbacks."""

    def __init__(
        self,
        sources: list[Path],
        dirty_filenames: set[str],
        on_selection_change: Callable[[str], None] | None = None,
        on_enter: Callable[[str | None], None] | None = None,
    ) -> None:
        self._sources = sources
        self._on_selection_change = on_selection_change
        self._on_enter = on_enter
        self._rows: list[SelectableImageRow] = [
            SelectableImageRow(s.name, dirty=s.name in dirty_filenames)
            for s in sources
        ]
        self._walker = urwid.SimpleFocusListWalker(self._rows)
        urwid.connect_signal(self._walker, "modified", self._on_focus_changed)
        listbox = urwid.ListBox(self._walker)
        super().__init__(listbox)

    @property
    def source_count(self) -> int:
        return len(self._sources)

    @property
    def selected_index(self) -> int:
        return self._walker.focus or 0

    @property
    def selected_filename(self) -> str | None:
        if not self._rows:
            return None
        idx = self._walker.focus or 0
        return self._rows[idx].filename

    def _on_focus_changed(self) -> None:
        if self._on_selection_change and self._rows:
            idx = self._walker.focus or 0
            self._on_selection_change(self._rows[idx].filename)

    def update_dirty(self, dirty_filenames: set[str]) -> None:
        for row in self._rows:
            row.update_dirty(row.filename in dirty_filenames)

    def keypress(self, size, key: str) -> str | None:
        if key in ("up", "ctrl p"):
            return self._w.keypress(size, "up")
        if key in ("down", "ctrl n"):
            return self._w.keypress(size, "down")
        if key == "enter":
            if self._on_enter:
                self._on_enter(self.selected_filename)
            return None
        return self._w.keypress(size, key)
