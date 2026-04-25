# simplegals/tui/progress_bar.py
from __future__ import annotations

import urwid

from ..workers.progress import ProgressState


def _render_bar(done: int, failed: int, total: int, label: str, width: int = 20) -> str:
    filled = done + failed
    pct = filled / total if total else 0
    n_fill = round(pct * width)
    bar = "█" * n_fill + "░" * (width - n_fill)
    suffix = f" ({failed} err)" if failed else ""
    return f"{label} [{bar}] {done}/{total}{suffix}"


class BuildProgressWidget(urwid.Text):
    """A single text-based progress bar for one task category."""

    def __init__(self, done: int, failed: int, total: int, label: str) -> None:
        super().__init__(_render_bar(done, failed, total, label))

    def update(self, done: int, failed: int, total: int, label: str) -> None:
        self.set_text(_render_bar(done, failed, total, label))


class BuildProgressPanel(urwid.WidgetWrap):
    """Displays two progress bars (thumbs + output) and the current filename."""

    def __init__(self) -> None:
        self._thumb_bar = BuildProgressWidget(0, 0, 0, "Previews")
        self._output_bar = BuildProgressWidget(0, 0, 0, "Output ")
        self._current = urwid.Text("")
        pile = urwid.Pile([
            urwid.Text("Building...", align="center"),
            urwid.Divider(),
            self._thumb_bar,
            self._output_bar,
            urwid.Divider(),
            self._current,
        ])
        super().__init__(pile)

    def update(self, state: ProgressState) -> None:
        self._thumb_bar.update(state.thumb_done, state.thumb_failed, state.thumb_total, "Previews")
        self._output_bar.update(state.output_done, state.output_failed, state.output_total, "Output ")
        if state.current_file:
            self._current.set_text(f"  {state.current_file}")
