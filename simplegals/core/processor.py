from __future__ import annotations

from pathlib import Path

import piexif
from PIL import Image, ImageOps

from .config import ProjectConfig

SGUI_THUMB_MAX: tuple[int, int] = (800, 800)
HTML_THUMB_MAX: tuple[int, int] = (600, 450)


def _thumb_name(source: Path) -> str:
    return f"{source.stem}_thumb{source.suffix}"


def generate_sgui_thumb(source: Path, meta_dir: Path) -> Path:
    """Generate .meta/<stem>_thumb<ext> for sgui preview. Not subject to publishing settings."""
    dest = meta_dir / _thumb_name(source)
    with Image.open(source) as img:
        img = ImageOps.exif_transpose(img)
        img.thumbnail(SGUI_THUMB_MAX, Image.LANCZOS)
        img.save(dest)
    return dest


def generate_output(
    source: Path,
    out_dir: Path,
    config: ProjectConfig,
) -> tuple[Path, Path]:
    """Generate out/<filename>.<ext> and out/<stem>_thumb<ext>. Returns (output_path, thumb_path)."""
    output_path = out_dir / source.name
    thumb_path = out_dir / _thumb_name(source)

    with Image.open(source) as img:
        img = ImageOps.exif_transpose(img)
        icc = img.info.get("icc_profile")

        if config.copyright:
            img = _inject_copyright(img, config.copyright, source)

        save_kwargs: dict = {"quality": config.quality}
        if icc:
            save_kwargs["icc_profile"] = icc
        img.save(output_path, **_format_save_kwargs(source, save_kwargs))

        img.thumbnail(HTML_THUMB_MAX, Image.LANCZOS)
        img.save(thumb_path, **_format_save_kwargs(source, save_kwargs))

    return output_path, thumb_path


def _format_save_kwargs(source: Path, kwargs: dict) -> dict:
    ext = source.suffix.lower()
    if ext in (".jpg", ".jpeg"):
        return kwargs
    if ext == ".png":
        # Pillow maps quality 0-100 → compress_level 0-9
        compress = max(0, min(9, round((100 - kwargs.get("quality", 90)) / 11)))
        result = {k: v for k, v in kwargs.items() if k != "quality"}
        result["compress_level"] = compress
        return result
    return {}


def _inject_copyright(img: Image.Image, copyright: str, source: Path) -> Image.Image:
    ext = source.suffix.lower()
    if ext not in (".jpg", ".jpeg"):
        return img
    try:
        exif_bytes = img.info.get("exif", b"")
        if exif_bytes:
            exif_dict = piexif.load(exif_bytes)
        else:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}
        exif_dict["0th"][piexif.ImageIFD.Copyright] = copyright.encode("utf-8")
        img.info["exif"] = piexif.dump(exif_dict)
    except Exception:
        pass
    return img
