import json
import logging
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path

from .languages import BASE_IGNORE_PATTERNS, LanguageConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CollectOptions:
    include_tree_only_matching: bool = True
    max_file_size_bytes: int = 2 * 1024 * 1024
    include_patterns: tuple[str, ...] = field(default_factory=tuple)
    exclude_patterns: tuple[str, ...] = field(default_factory=tuple)


def _get_ignore_patterns(lang_config: LanguageConfig, options: CollectOptions | None = None) -> tuple[str, ...]:
    options = options or CollectOptions()
    return (*BASE_IGNORE_PATTERNS, *lang_config.ignore_patterns, *options.exclude_patterns)


def _matches_any(name_or_path: str, patterns: tuple[str, ...]) -> bool:
    normalized = name_or_path.replace("\\", "/")
    basename = Path(normalized).name
    return any(fnmatch(normalized, pattern) or fnmatch(basename, pattern) for pattern in patterns)


def _should_ignore(path: Path, root: Path, ignore_patterns: tuple[str, ...]) -> bool:
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        rel = path.as_posix()

    parts = Path(rel).parts
    return _matches_any(rel, ignore_patterns) or any(_matches_any(part, ignore_patterns) for part in parts)


def _is_supported_source(path: Path, lang_config: LanguageConfig) -> bool:
    return path.suffix.lower() in {ext.lower() for ext in lang_config.extensions}


def _passes_include_filters(path: Path, root: Path, options: CollectOptions) -> bool:
    if not options.include_patterns:
        return True
    rel = path.relative_to(root).as_posix()
    return _matches_any(rel, options.include_patterns)


def build_tree(
    root_path: str,
    lang_config: LanguageConfig,
    options: CollectOptions | None = None,
    prefix: str = "",
) -> list[str]:
    options = options or CollectOptions()
    root = Path(root_path)
    ignore_patterns = _get_ignore_patterns(lang_config, options)
    lines: list[str] = []

    if not prefix:
        lines.append(f"{root.name}/")

    try:
        entries = sorted(root.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
    except PermissionError:
        logger.warning("Permission denied: %s", root)
        return lines

    visible_entries: list[Path] = []
    for entry in entries:
        if _should_ignore(entry, root if not prefix else root.parent, ignore_patterns):
            continue

        if entry.is_file():
            if options.include_tree_only_matching and not _is_supported_source(entry, lang_config):
                continue
            if not _passes_include_filters(entry, Path(root_path), options):
                continue

        if entry.is_dir() and options.include_tree_only_matching:
            if not _directory_contains_supported_files(entry, lang_config, options):
                continue

        visible_entries.append(entry)

    for i, entry in enumerate(visible_entries):
        is_last = i == len(visible_entries) - 1
        connector = "└── " if is_last else "├── "
        extension = "    " if is_last else "│   "

        if entry.is_dir():
            lines.append(f"{prefix}{connector}{entry.name}/")
            lines.extend(build_tree(str(entry), lang_config, options, prefix + extension))
        else:
            lines.append(f"{prefix}{connector}{entry.name}")

    return lines


def _directory_contains_supported_files(
    directory: Path,
    lang_config: LanguageConfig,
    options: CollectOptions,
) -> bool:
    ignore_patterns = _get_ignore_patterns(lang_config, options)
    for file_path in directory.rglob("*"):
        if not file_path.is_file():
            continue
        if _should_ignore(file_path, directory, ignore_patterns):
            continue
        if _is_supported_source(file_path, lang_config) and _passes_include_filters(file_path, directory, options):
            return True
    return False


def get_tree_string(
    root_path: str,
    lang_config: LanguageConfig,
    options: CollectOptions | None = None,
) -> str:
    return "\n".join(build_tree(root_path, lang_config, options))


def _read_file_content(file_path: Path, max_file_size_bytes: int) -> str:
    try:
        size = file_path.stat().st_size
    except OSError as exc:
        logger.warning("Could not stat file %s: %s", file_path, exc)
        return "# [Could not stat file]"

    if size > max_file_size_bytes:
        logger.warning("Skipping large file: %s (%d bytes)", file_path, size)
        return f"# [Skipped: file too large ({size} bytes)]"

    for enc in ("utf-8", "utf-8-sig", "cp1251", "latin-1"):
        try:
            return file_path.read_text(encoding=enc)
        except (UnicodeDecodeError, UnicodeError):
            continue
        except OSError as exc:
            logger.warning("Could not read file %s: %s", file_path, exc)
            return "# [Could not read file]"

    logger.warning("Could not decode file: %s", file_path)
    return "# [Could not decode file]"


def _extract_notebook_code(file_path: Path, max_file_size_bytes: int) -> str:
    raw = _read_file_content(file_path, max_file_size_bytes)
    if raw.startswith("# ["):
        return raw

    try:
        notebook = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse notebook %s: %s", file_path, exc)
        return "# [Error reading notebook]"

    cells = notebook.get("cells", [])
    parts: list[str] = []

    for i, cell in enumerate(cells, 1):
        cell_type = cell.get("cell_type", "unknown")
        source = "".join(cell.get("source", []))

        if cell_type == "markdown":
            parts.append(f"# === Markdown Cell [{i}] ===")
            parts.extend(f"# {line}" for line in source.splitlines())
            parts.append("")
        elif cell_type == "code":
            parts.append(f"# === Code Cell [{i}] ===")
            parts.append(source)
            parts.append("")
        elif cell_type == "raw":
            parts.append(f"# === Raw Cell [{i}] ===")
            parts.extend(f"# {line}" for line in source.splitlines())
            parts.append("")

    return "\n".join(parts)


def collect_files(
    root_path: str,
    lang_config: LanguageConfig,
    options: CollectOptions | None = None,
) -> list[dict[str, str]]:
    options = options or CollectOptions()
    root = Path(root_path)
    ignore_patterns = _get_ignore_patterns(lang_config, options)
    files: list[dict[str, str]] = []

    for ext in lang_config.extensions:
        for file_path in sorted(root.rglob(f"*{ext}")):
            if not file_path.is_file():
                continue
            if _should_ignore(file_path, root, ignore_patterns):
                logger.debug("Skipping ignored path: %s", file_path)
                continue
            if not _passes_include_filters(file_path, root, options):
                logger.debug("Skipping non-included path: %s", file_path)
                continue

            if file_path.suffix.lower() == ".ipynb":
                content = _extract_notebook_code(file_path, options.max_file_size_bytes)
            else:
                content = _read_file_content(file_path, options.max_file_size_bytes)

            relative = file_path.relative_to(root).as_posix()
            files.append({"path": relative, "content": content})
            logger.debug("Collected: %s", relative)

    return files
