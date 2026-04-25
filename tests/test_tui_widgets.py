# tests/test_tui_widgets.py
import pytest
from pathlib import Path


def test_selectable_image_row_shows_filename():
    from simplegals.tui.file_panel import SelectableImageRow
    row = SelectableImageRow("IMG_1234.jpg", dirty=False)
    assert "IMG_1234.jpg" in row.label


def test_selectable_image_row_shows_dirty_indicator():
    from simplegals.tui.file_panel import SelectableImageRow
    row = SelectableImageRow("IMG_1234.jpg", dirty=True)
    assert "*" in row.label


def test_selectable_image_row_not_dirty_no_star():
    from simplegals.tui.file_panel import SelectableImageRow
    row = SelectableImageRow("IMG_1234.jpg", dirty=False)
    assert "* " not in row.label


def test_selectable_image_row_update_dirty():
    from simplegals.tui.file_panel import SelectableImageRow
    row = SelectableImageRow("IMG_1234.jpg", dirty=False)
    row.update_dirty(True)
    assert "*" in row.label


def test_file_panel_source_count():
    from simplegals.tui.file_panel import FilePanel
    sources = [Path("a.jpg"), Path("b.jpg"), Path("c.jpg")]
    panel = FilePanel(sources, dirty_filenames=set())
    assert panel.source_count == 3


def test_file_panel_selected_index_starts_at_zero():
    from simplegals.tui.file_panel import FilePanel
    sources = [Path("a.jpg"), Path("b.jpg")]
    panel = FilePanel(sources, dirty_filenames=set())
    assert panel.selected_index == 0


def test_file_panel_selected_filename():
    from simplegals.tui.file_panel import FilePanel
    sources = [Path("a.jpg"), Path("b.jpg")]
    panel = FilePanel(sources, dirty_filenames=set())
    assert panel.selected_filename == "a.jpg"


def test_file_panel_empty_sources():
    from simplegals.tui.file_panel import FilePanel
    panel = FilePanel([], dirty_filenames=set())
    assert panel.source_count == 0
    assert panel.selected_filename is None


def test_truncate_short_text():
    from simplegals.tui.file_panel import _truncate
    assert _truncate("short", 20) == "short"


def test_truncate_long_text():
    from simplegals.tui.file_panel import _truncate
    result = _truncate("IMG_very_long_filename.jpg", 12)
    assert len(result) <= 12
    assert result.endswith("…")


def test_preview_widget_instantiates():
    from simplegals.tui.preview_panel import PreviewWidget
    widget = PreviewWidget()
    assert widget is not None


def test_image_settings_panel_caption_field(tmp_path):
    from simplegals.core.config import ProjectConfig
    from simplegals.tui.preview_panel import ImageSettingsPanel
    from simplegals.tui.state import StagedChangesModel
    config = ProjectConfig(images={"a.jpg": {"caption": "hello", "alt": "", "include": True}})
    staged = StagedChangesModel()
    panel = ImageSettingsPanel(
        "a.jpg", config, staged, on_save=lambda: None, on_revert=lambda: None
    )
    assert panel.caption_field.edit_text == "hello"


def test_image_settings_panel_include_state(tmp_path):
    from simplegals.core.config import ProjectConfig
    from simplegals.tui.preview_panel import ImageSettingsPanel
    from simplegals.tui.state import StagedChangesModel
    config = ProjectConfig(images={"a.jpg": {"caption": "", "alt": "", "include": False}})
    staged = StagedChangesModel()
    panel = ImageSettingsPanel(
        "a.jpg", config, staged, on_save=lambda: None, on_revert=lambda: None
    )
    assert panel.include_check.state is False


def test_gallery_settings_panel_title_field():
    from simplegals.core.config import ProjectConfig
    from simplegals.tui.preview_panel import GallerySettingsPanel
    from simplegals.tui.state import StagedChangesModel
    config = ProjectConfig(title="My Gallery")
    staged = StagedChangesModel()
    panel = GallerySettingsPanel(
        config, staged, on_save=lambda: None, on_revert=lambda: None
    )
    assert panel.title_field.edit_text == "My Gallery"


def test_gallery_settings_panel_columns_field():
    from simplegals.core.config import Layout, ProjectConfig
    from simplegals.tui.preview_panel import GallerySettingsPanel
    from simplegals.tui.state import StagedChangesModel
    config = ProjectConfig(layout=Layout(columns=3, rows=4))
    staged = StagedChangesModel()
    panel = GallerySettingsPanel(
        config, staged, on_save=lambda: None, on_revert=lambda: None
    )
    assert panel.columns_field.edit_text == "3"


def test_right_panel_instantiates():
    from simplegals.tui.preview_panel import PreviewWidget, RightPanel
    import urwid
    preview = PreviewWidget()
    content = urwid.Text("placeholder")
    panel = RightPanel(preview, content)
    assert panel is not None
