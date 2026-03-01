import json
import logging
from pathlib import Path

from .languages import LanguageConfig, BASE_IGNORED_DIRS

logger = logging.getLogger(__name__)


def _get_ignored_dirs(lang_config: LanguageConfig) -> set[str]:
    ignored = set(BASE_IGNORED_DIRS)
    ignored.update(lang_config.extra_ignore_dirs)
    return ignored


def _should_ignore(name: str, ignored_dirs: set[str]) -> bool:
    if name in ignored_dirs:
        return True
    for pattern in ignored_dirs:
        if pattern.startswith("*") and name.endswith(pattern[1:]):
            return True
    return False


def build_tree(root_path: str, lang_config: LanguageConfig, prefix: str = "") -> list[str]:
    root = Path(root_path)
    ignored = _get_ignored_dirs(lang_config)
    lines = []

    if not prefix:
        lines.append(f"{root.name}/")

    try:
        entries = sorted(
            root.iterdir(),
            key=lambda e: (not e.is_dir(), e.name.lower())
        )
    except PermissionError:
        logger.warning("Permission denied: %s", root)
        return lines

    entries = [
        e for e in entries
        if not (e.is_dir() and _should_ignore(e.name, ignored))
    ]

    for i, entry in enumerate(entries):
        is_last = (i == len(entries) - 1)
        connector = "└── " if is_last else "├── "
        extension = "    " if is_last else "│   "

        if entry.is_dir():
            lines.append(f"{prefix}{connector}{entry.name}/")
            lines.extend(build_tree(str(entry), lang_config, prefix + extension))
        else:
            lines.append(f"{prefix}{connector}{entry.name}")

    return lines


def get_tree_string(root_path: str, lang_config: LanguageConfig) -> str:
    return "\n".join(build_tree(root_path, lang_config))


def _read_file_content(file_path: Path) -> str:
    for enc in ["utf-8", "utf-8-sig", "cp1251", "latin-1"]:
        try:
            return file_path.read_text(encoding=enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
    logger.warning("Could not decode file: %s", file_path)
    return "# [Could not read file]"


def _extract_notebook_code(file_path: Path) -> str:
    try:
        content = file_path.read_text(encoding="utf-8")
        notebook = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.warning("Failed to parse notebook %s: %s", file_path, e)
        return "# [Error reading notebook]"

    cells = notebook.get("cells", [])
    parts = []

    for i, cell in enumerate(cells):
        cell_type = cell.get("cell_type", "unknown")
        source = "".join(cell.get("source", []))

        if cell_type == "markdown":
            parts.append(f"# === Markdown Cell [{i + 1}] ===")
            for line in source.split("\n"):
                parts.append(f"# {line}")
            parts.append("")
        elif cell_type == "code":
            parts.append(f"# === Code Cell [{i + 1}] ===")
            parts.append(source)
            parts.append("")
        elif cell_type == "raw":
            parts.append(f"# === Raw Cell [{i + 1}] ===")
            for line in source.split("\n"):
                parts.append(f"# {line}")
            parts.append("")

    return "\n".join(parts)


def collect_files(root_path: str, lang_config: LanguageConfig) -> list[dict]:
    root = Path(root_path)
    ignored = _get_ignored_dirs(lang_config)
    files = []

    for ext in lang_config.extensions:
        for file_path in sorted(root.rglob(f"*{ext}")):
            parts = file_path.relative_to(root).parts
            if any(_should_ignore(part, ignored) for part in parts):
                logger.debug("Skipping ignored path: %s", file_path)
                continue

            if ext == ".ipynb":
                content = _extract_notebook_code(file_path)
            else:
                content = _read_file_content(file_path)

            relative = str(file_path.relative_to(root))
            files.append({"path": relative, "content": content})
            logger.debug("Collected: %s", relative)

    return files