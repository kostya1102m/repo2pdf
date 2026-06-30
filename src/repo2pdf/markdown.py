import logging
from dataclasses import dataclass
from pathlib import Path

from .languages import LanguageConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MarkdownRenderOptions:
    include_line_numbers: bool = False
    include_title: bool = True
    include_tree: bool = True


def _markdown_code_fence(lang_config: LanguageConfig) -> str:
    mapping = {
        "python": "python",
        "javascript": "javascript",
        "typescript": "typescript",
        "jupyter": "python",
        "js_ts": "javascript",
        "java": "java",
        "xml": "xml",
        "yaml": "yaml",
        "sql": "sql",
        "html": "html",
    }
    return mapping.get(lang_config.name, "")

def _code_fence_for_content(content: str) -> str:
    max_run = 0
    current = 0

    for char in content:
        if char == "`":
            current += 1
            max_run = max(max_run, current)
        else:
            current = 0

    return "`" * max(3, max_run + 1)

def _with_line_numbers(content: str) -> str:
    lines = content.splitlines()
    width = max(len(str(len(lines))), 3)

    return "\n".join(
        f"{str(index).rjust(width)} | {line}"
        for index, line in enumerate(lines, 1)
    )


def generate_markdown(
    tree_text: str,
    files: list[dict[str, str]],
    output_path: str,
    repo_name: str,
    lang_config: LanguageConfig,
    render_options: MarkdownRenderOptions | None = None,
) -> str:
    options = render_options or MarkdownRenderOptions()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Generating Markdown: %s", output)

    fence = _markdown_code_fence(lang_config)
    parts: list[str] = []

    if options.include_title:
        parts.extend(
            [
                f"# {repo_name}",
                "",
                f"**{lang_config.display_name} Documentation**",
                "",
                f"Files: {len(files)}",
                f"Extensions: `{', '.join(lang_config.extensions)}`",
                "",
            ]
        )

    if options.include_tree:
        parts.extend(
            [
                "## Project Structure",
                "",
                "```text",
                tree_text,
                "```",
                "",
            ]
        )

    if files:
        parts.extend(
            [
                f"## Source Code ({lang_config.display_name})",
                "",
            ]
        )

    for file_info in files:
        file_path = file_info["path"]
        content = file_info["content"]

        if options.include_line_numbers:
            content = _with_line_numbers(content)
            file_fence = "text"
        else:
            file_fence = fence

        
        fence_marks = _code_fence_for_content(content)

        parts.extend(
            [
                f"### `{file_path}`",
                "",
                f"{fence_marks}{file_fence}",
                content,
                fence_marks,
                "",
            ]
        )

    output.write_text("\n".join(parts), encoding="utf-8")
    logger.info("Markdown saved: %s", output)

    return str(output)