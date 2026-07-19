from __future__ import annotations

import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
DEFAULT_INPUT = ASSETS_DIR / "Avatar.png"
HEADSETS_PATH = ASSETS_DIR / "Miku_Headsets.png"
OUTPUT_PATH = ASSETS_DIR / "Miku_Avatar.png"
CANVAS_SIZE = (500, 500)
PROFILE_SIZE = (400, 400)


def obtener_imagen_de_perfil() -> Path:
    """Return the user image, preferring the documented Avatar.png path."""
    configured_path = os.getenv("MIKU_PROFILE_IMAGE", "").strip()
    if configured_path:
        candidate = Path(os.path.expandvars(configured_path)).expanduser()
        if candidate.is_file():
            return candidate

    if DEFAULT_INPUT.is_file():
        return DEFAULT_INPUT

    raise FileNotFoundError(
        "Add your picture as assets/Avatar.png before opening the power menu."
    )


def _needs_rebuild(source: Path) -> bool:
    if not OUTPUT_PATH.is_file():
        return True
    output_time = OUTPUT_PATH.stat().st_mtime
    return output_time < max(source.stat().st_mtime, HEADSETS_PATH.stat().st_mtime)


def generar_avatar(force: bool = False) -> Path | None:
    """Compose the circular user photo with the Miku headset overlay."""
    try:
        source_path = obtener_imagen_de_perfil()
        if not HEADSETS_PATH.is_file():
            raise FileNotFoundError(f"Missing required asset: {HEADSETS_PATH.name}")

        if not force and not _needs_rebuild(source_path):
            return OUTPUT_PATH

        with Image.open(source_path) as source_image:
            profile = ImageOps.exif_transpose(source_image).convert("RGBA")
        with Image.open(HEADSETS_PATH) as headset_image:
            headsets = headset_image.convert("RGBA")

        profile = ImageOps.fit(
            profile,
            PROFILE_SIZE,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        mask = Image.new("L", PROFILE_SIZE, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 399, 399), fill=255)
        profile.putalpha(mask)

        final = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
        final.paste(profile, (50, 50), profile)

        headsets = headsets.resize(CANVAS_SIZE, Image.Resampling.LANCZOS)
        final.alpha_composite(headsets)
        final.save(OUTPUT_PATH, "PNG", optimize=True)
        return OUTPUT_PATH
    except (OSError, ValueError) as exc:
        print(f"Miku avatar was not generated: {exc}", file=sys.stderr)
        return None


def main() -> int:
    result = generar_avatar(force=True)
    if result is None:
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
