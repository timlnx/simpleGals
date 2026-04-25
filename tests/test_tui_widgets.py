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


def test_render_bar_zero_progress():
    from simplegals.tui.progress_bar import _render_bar
    result = _render_bar(0, 0, 4, "Previews")
    assert "0/4" in result
    assert "░" * 20 in result


def test_render_bar_full_progress():
    from simplegals.tui.progress_bar import _render_bar
    result = _render_bar(4, 0, 4, "Output ")
    assert "4/4" in result
    assert "█" * 20 in result


def test_render_bar_with_errors():
    from simplegals.tui.progress_bar import _render_bar
    result = _render_bar(3, 1, 4, "Output ")
    assert "1 err" in result


def test_build_progress_widget_shows_counts():
    from simplegals.tui.progress_bar import BuildProgressWidget
    widget = BuildProgressWidget(2, 0, 4, "Previews")
    assert "2/4" in widget.text


def test_build_progress_panel_instantiates():
    from simplegals.tui.progress_bar import BuildProgressPanel
    from simplegals.workers.progress import ProgressState
    panel = BuildProgressPanel()
    state = ProgressState(thumb_total=2, thumb_done=1, output_total=2, output_done=0)
    panel.update(state)  # should not raise


def test_sgui_app_instantiates(tmp_project):
    from simplegals.core.config import GlobalConfig, ProjectConfig
    from simplegals.tui.app import SGUIApp
    config = ProjectConfig()
    global_config = GlobalConfig()
    config_path = tmp_project / "simpleGal.json"
    app = SGUIApp(tmp_project, config, global_config, config_path)
    assert app is not None


def test_sgui_app_mode_starts_as_file(tmp_project):
    from simplegals.core.config import GlobalConfig, ProjectConfig
    from simplegals.tui.app import SGUIApp
    config = ProjectConfig()
    global_config = GlobalConfig()
    config_path = tmp_project / "simpleGal.json"
    app = SGUIApp(tmp_project, config, global_config, config_path)
    assert app._mode == "file"


def test_sgui_app_no_dirty_on_start(tmp_project):
    from simplegals.core.config import GlobalConfig, ProjectConfig
    from simplegals.tui.app import SGUIApp
    config = ProjectConfig()
    global_config = GlobalConfig()
    config_path = tmp_project / "simpleGal.json"
    app = SGUIApp(tmp_project, config, global_config, config_path)
    assert not app._staged.has_any_dirty()


def test_sgui_help_exits_zero():
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "-m", "simplegals.tui", "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "sgui" in result.stdout


def test_image_settings_panel_caption_change_stages():
    from simplegals.core.config import ProjectConfig
    from simplegals.tui.preview_panel import ImageSettingsPanel
    from simplegals.tui.state import StagedChangesModel
    config = ProjectConfig(images={"a.jpg": {"caption": "old", "alt": "", "include": True}})
    staged = StagedChangesModel()
    panel = ImageSettingsPanel(
        "a.jpg", config, staged, on_save=lambda: None, on_revert=lambda: None
    )
    panel.caption_field.set_edit_text("new caption")
    assert staged.get_current("a.jpg", "caption", None) == "new caption"
    assert staged.is_dirty("a.jpg")


def test_image_settings_panel_alt_change_stages():
    from simplegals.core.config import ProjectConfig
    from simplegals.tui.preview_panel import ImageSettingsPanel
    from simplegals.tui.state import StagedChangesModel
    config = ProjectConfig(images={"a.jpg": {"caption": "", "alt": "old alt", "include": True}})
    staged = StagedChangesModel()
    panel = ImageSettingsPanel(
        "a.jpg", config, staged, on_save=lambda: None, on_revert=lambda: None
    )
    panel.alt_field.set_edit_text("new alt")
    assert staged.get_current("a.jpg", "alt", None) == "new alt"


def test_image_settings_panel_include_toggle_stages():
    from simplegals.core.config import ProjectConfig
    from simplegals.tui.preview_panel import ImageSettingsPanel
    from simplegals.tui.state import StagedChangesModel
    config = ProjectConfig(images={"a.jpg": {"caption": "", "alt": "", "include": True}})
    staged = StagedChangesModel()
    panel = ImageSettingsPanel(
        "a.jpg", config, staged, on_save=lambda: None, on_revert=lambda: None
    )
    panel.include_check.set_state(False)
    assert staged.get_current("a.jpg", "include", None) is False
    assert staged.is_dirty("a.jpg")


def test_image_settings_panel_on_change_callback_fires():
    from simplegals.core.config import ProjectConfig
    from simplegals.tui.preview_panel import ImageSettingsPanel
    from simplegals.tui.state import StagedChangesModel
    config = ProjectConfig(images={"a.jpg": {"caption": "", "alt": "", "include": True}})
    staged = StagedChangesModel()
    fired = []
    panel = ImageSettingsPanel(
        "a.jpg",
        config,
        staged,
        on_save=lambda: None,
        on_revert=lambda: None,
        on_change=lambda: fired.append(True),
    )
    panel.caption_field.set_edit_text("hi")
    assert fired, "on_change should fire when caption widget changes"


def test_gallery_settings_panel_title_change_stages():
    from simplegals.core.config import ProjectConfig
    from simplegals.tui.preview_panel import GallerySettingsPanel
    from simplegals.tui.state import StagedChangesModel
    config = ProjectConfig(title="Old Title")
    staged = StagedChangesModel()
    panel = GallerySettingsPanel(
        config, staged, on_save=lambda: None, on_revert=lambda: None
    )
    panel.title_field.set_edit_text("New Title")
    assert staged.get_current("gallery", "title", None) == "New Title"
    assert staged.is_dirty("gallery")


def test_gallery_settings_panel_columns_change_stages_int():
    from simplegals.core.config import Layout, ProjectConfig
    from simplegals.tui.preview_panel import GallerySettingsPanel
    from simplegals.tui.state import StagedChangesModel
    config = ProjectConfig(layout=Layout(columns=3, rows=4))
    staged = StagedChangesModel()
    panel = GallerySettingsPanel(
        config, staged, on_save=lambda: None, on_revert=lambda: None
    )
    panel.columns_field.set_edit_text("7")
    assert staged.get_current("gallery", "layout_columns", None) == 7


def test_gallery_settings_panel_quality_invalid_int_ignored():
    from simplegals.core.config import ProjectConfig
    from simplegals.tui.preview_panel import GallerySettingsPanel
    from simplegals.tui.state import StagedChangesModel
    config = ProjectConfig(quality=90)
    staged = StagedChangesModel()
    panel = GallerySettingsPanel(
        config, staged, on_save=lambda: None, on_revert=lambda: None
    )
    panel.quality_field.set_edit_text("abc")
    assert staged.get_current("gallery", "quality", None) is None


def test_sgui_app_handles_percent_panel_width(tmp_project):
    from simplegals.core.config import GlobalConfig, ProjectConfig
    from simplegals.tui.app import SGUIApp
    config = ProjectConfig()
    global_config = GlobalConfig(file_panel_width="30%")
    config_path = tmp_project / "simpleGal.json"
    app = SGUIApp(tmp_project, config, global_config, config_path)
    assert app is not None


def test_sgui_app_handles_invalid_panel_width(tmp_project):
    from simplegals.core.config import GlobalConfig, ProjectConfig
    from simplegals.tui.app import SGUIApp
    config = ProjectConfig()
    global_config = GlobalConfig(file_panel_width="garbage")
    config_path = tmp_project / "simpleGal.json"
    app = SGUIApp(tmp_project, config, global_config, config_path)
    assert app is not None
