import os
import zipfile
import io
import logging
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
    for font_name in REQUIRED_FONTS:
        if not (FONTS_DIR / font_name).exists():
            return False
    return True


def download_fonts():
    FONTS_DIR.mkdir(parents=True, exist_ok=True)

    if fonts_exist():
        return

    logger.info("Downloading DejaVu fonts (first run only)...")

    try:
        response = requests.get(DEJAVU_URL, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.critical(
            "Failed to download fonts: %s. "
            "Please download DejaVu fonts manually and place .ttf files in ./fonts/",
            e,
        )
        raise SystemExit(1)

    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        for zip_entry in zf.namelist():
            filename = os.path.basename(zip_entry)
            if filename in REQUIRED_FONTS:
                data = zf.read(zip_entry)
                target = FONTS_DIR / filename
                target.write_bytes(data)
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