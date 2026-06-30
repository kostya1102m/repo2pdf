import io
import logging
import os
import zipfile
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

FONTS_DIR = Path(__file__).parent / "fonts"

DEJAVU_URL = (
    "https://github.com/dejavu-fonts/dejavu-fonts"
    "/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip"
)

REQUIRED_FONTS = {
    "DejaVuSansMono.ttf": "regular",
    "DejaVuSansMono-Bold.ttf": "bold",
    "DejaVuSansMono-Oblique.ttf": "italic",
    "DejaVuSansMono-BoldOblique.ttf": "bold_italic",
    "DejaVuSans.ttf": "sans_regular",
    "DejaVuSans-Bold.ttf": "sans_bold",
}


def fonts_exist() -> bool:
    return all((FONTS_DIR / font_name).exists() for font_name in REQUIRED_FONTS)


def download_fonts() -> None:
    FONTS_DIR.mkdir(parents=True, exist_ok=True)

    if fonts_exist():
        return

    logger.info("Downloading DejaVu fonts (first run only)...")

    try:
        response = requests.get(DEJAVU_URL, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.critical(
            "Failed to download fonts: %s. "
            "Please download DejaVu fonts manually and place .ttf files in %s",
            exc,
            FONTS_DIR,
        )
        raise SystemExit(1) from exc

    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        for zip_entry in zf.namelist():
            filename = os.path.basename(zip_entry)
            if filename not in REQUIRED_FONTS:
                continue
            target = FONTS_DIR / filename
            target.write_bytes(zf.read(zip_entry))
            logger.debug("Extracted font: %s", filename)

    if not fonts_exist():
        logger.critical("Some fonts are missing after download")
        raise SystemExit(1)

    logger.info("Fonts ready")


def get_font_path(font_name: str) -> str:
    path = FONTS_DIR / font_name
    if not path.exists():
        download_fonts()
    return str(path)
