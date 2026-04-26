# simplegals/tui/file_panel.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import urwid


def _truncate(text: str, width: int) -> str:
    """Truncate text to width, appending ellipsis if needed."""
    if len(text) <= width:
        return text
    return text[: max(0, width - 1)] + "…"


class SelectableImageRow(urwid.WidgetWrap):
    """One selectable row in the file list."""

    def __init__(self, filename: str, dirty: bool = False, excluded: bool = False) -> None:
        self.filename = filename
        self.dirty = dirty
        self.excluded = excluded
        self._icon = urwid.SelectableIcon(self._make_label(), cursor_position=0, wrap="clip")
        super().__init__(self._make_attrmap())

    def _make_attrmap(self) -> urwid.AttrMap:
        if self.dirty:
            attr = "dirty"
        elif self.excluded:
            attr = "excluded"
        else:
            attr = None
        return urwid.AttrMap(self._icon, attr, "selected")

    @property
    def label(self) -> str:
        return self._icon.text

    def _make_label(self) -> str:
        return ("* " if self.dirty else "  ") + self.filename

    def update_marks(self, dirty: bool, excluded: bool) -> None:
        self.dirty = dirty
        self.excluded = excluded
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
        excluded_filenames: set[str] = set(),
        on_selection_change: Callable[[str], None] | None = None,
        on_enter: Callable[[str | None], None] | None = None,
        on_open: Callable[[str | None], None] | None = None,
        loop: Any | None = None,
        scroll_rate: float = 2.0,
    ) -> None:
        self._sources = sources
        self._on_selection_change = on_selection_change
        self._on_enter = on_enter
        self._on_open = on_open
        self._loop = loop
        self._scroll_rate = scroll_rate
        self._scroll_offset = 0
        self._scroll_alarm: Any | None = None
        self._last_col = 0
        self._rows: list[SelectableImageRow] = [
            SelectableImageRow(s.name, dirty=s.name in dirty_filenames, excluded=s.name in excluded_filenames)
            for s in sources
        ]
        self._walker = urwid.SimpleFocusListWalker(self._rows)
        urwid.connect_signal(self._walker, "modified", self._on_focus_changed)
        listbox = urwid.ListBox(self._walker)
        super().__init__(listbox)

    def render(self, size: tuple, focus: bool = False):
        self._last_col = size[0]
        return super().render(size, focus)

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
        self._cancel_scroll()
        if self._on_selection_change and self._rows:
            idx = self._walker.focus or 0
            self._on_selection_change(self._rows[idx].filename)
        self._start_scroll()

    def _start_scroll(self) -> None:
        if not self._loop or not self._rows or self._last_col <= 0:
            return
        idx = self._walker.focus or 0
        full_label = self._rows[idx]._make_label()
        if len(full_label) <= self._last_col:
            return
        delay = 1.0 / self._scroll_rate if self._scroll_rate > 0 else 0.5
        self._scroll_alarm = self._loop.set_alarm_in(delay, self._tick_scroll)

    def _cancel_scroll(self) -> None:
        if self._loop and self._scroll_alarm is not None:
            self._loop.remove_alarm(self._scroll_alarm)
            self._scroll_alarm = None
        self._scroll_offset = 0
        if self._rows:
            idx = self._walker.focus or 0
            self._rows[idx]._icon.set_text(self._rows[idx]._make_label())

    def _tick_scroll(self, loop: Any, _data: Any) -> None:
        if not self._rows:
            return
        idx = self._walker.focus or 0
        row = self._rows[idx]
        full_label = row._make_label()
        self._scroll_offset = (self._scroll_offset + 1) % max(1, len(full_label))
        row._icon.set_text(full_label[self._scroll_offset:])
        loop.draw_screen()
        delay = 1.0 / self._scroll_rate if self._scroll_rate > 0 else 0.5
        self._scroll_alarm = loop.set_alarm_in(delay, self._tick_scroll)

    def reload(self, sources: list[Path], dirty_filenames: set[str], excluded_filenames: set[str] = set()) -> None:
        self._cancel_scroll()
        self._sources = sources
        self._rows = [
            SelectableImageRow(s.name, dirty=s.name in dirty_filenames, excluded=s.name in excluded_filenames)
            for s in sources
        ]
        focus = min(self._walker.focus or 0, max(0, len(self._rows) - 1))
        self._walker[:] = self._rows
        if self._rows:
            self._walker.set_focus(focus)

    def update_marks(self, dirty_filenames: set[str], excluded_filenames: set[str]) -> None:
        for row in self._rows:
            row.update_marks(row.filename in dirty_filenames, row.filename in excluded_filenames)

    def keypress(self, size, key: str) -> str | None:
        if key in ("up", "ctrl p"):
            return self._w.keypress(size, "up")
        if key in ("down", "ctrl n"):
            return self._w.keypress(size, "down")
        if key == "enter":
            if self._on_enter:
                self._on_enter(self.selected_filename)
            return None
        if key == "ctrl o":
            if self._on_open:
                self._on_open(self.selected_filename)
            return None
        return self._w.keypress(size, key)
