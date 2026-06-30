import argparse
import logging
import sys
from pathlib import Path

from .generator import PDFRenderOptions, generate_pdf
from .languages import LanguageConfig, get_language, iter_unique_languages, list_languages
from .tree import CollectOptions, collect_files, get_tree_string
from .markdown import MarkdownRenderOptions, generate_markdown

logger = logging.getLogger(__name__)


def _configure_logging(verbosity: int) -> None:
    levels = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
    }
    level = levels.get(min(verbosity, 2), logging.DEBUG)

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate documentation from repository source files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  repo2pdf . -l python
  repo2pdf . -l js
  repo2pdf . -l python js jupyter
  repo2pdf . --all
  repo2pdf . -l python --max-pages 50
  repo2pdf . -l python --exclude "tests/*" --max-file-size 1
  repo2pdf --list

  repo2pdf . -l python --format md
  repo2pdf . -l python --format both
  repo2pdf . -l python --format md --md-line-numbers
""",
    )
    parser.add_argument(
        "repo_path",
        nargs="?",
        default=".",
        help="Path to repository (default: current directory)",
    )
    parser.add_argument(
        "-l",
        "--languages",
        nargs="+",
        default=["python"],
        help="Languages to generate (default: python)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate documentation for all supported languages",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        help="Output directory for generated documentation files (default: current)",
    )
    parser.add_argument(
        "--format",
        choices=("pdf", "md", "both"),
        default="pdf",
        help="Output format: pdf, md, or both (default: pdf)",
    )

    parser.add_argument(
        "--md-line-numbers",
        action="store_true",
        help="Include line numbers in Markdown code blocks.",
    )

    parser.add_argument(
        "--no-md-tree",
        action="store_true",
        help="Do not include project tree in Markdown output.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_langs",
        help="Show available languages and exit",
    )
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help="Include only paths matching this glob. Can be used multiple times.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Exclude paths matching this glob. Can be used multiple times.",
    )
    parser.add_argument(
        "--full-tree",
        action="store_true",
        help="Show full project tree instead of only matching source files.",
    )
    parser.add_argument(
        "--max-file-size",
        type=float,
        default=2.0,
        metavar="MB",
        help="Maximum source file size in MB before skipping (default: 2)",
    )
    parser.add_argument(
        "--truncate-lines",
        action="store_true",
        help="Truncate long code lines instead of wrapping them.",
    )
    parser.add_argument(
        "--max-line-chars",
        type=int,
        default=100,
        help="Maximum characters per visual code line (default: 100)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase logging verbosity (-v for INFO, -vv for DEBUG)",
    )

    split_group = parser.add_argument_group("PDF splitting options")
    split_group.add_argument(
        "--max-pages",
        type=int,
        default=None,
        metavar="N",
        help="Approximate maximum pages per PDF file. Splits into parts if exceeded.",
    )
    split_exclusive = split_group.add_mutually_exclusive_group()
    split_exclusive.add_argument(
        "--split",
        action="store_true",
        help="Enable auto-splitting with default approximate limit (50 pages)",
    )
    split_exclusive.add_argument(
        "--no-split",
        action="store_true",
        help="Disable splitting (generate single PDF regardless of size)",
    )

    return parser.parse_args()


def _resolve_max_pages(args: argparse.Namespace) -> int | None:
    if args.split and args.max_pages is not None:
        logger.warning("Both --split and --max-pages specified; using --max-pages %d", args.max_pages)

    if args.no_split:
        return None

    if args.max_pages is not None:
        if args.max_pages < 10:
            logger.warning("--max-pages should be at least 10, using 10")
            return 10
        return args.max_pages

    if args.split:
        return 50

    return None


def _resolve_languages(args: argparse.Namespace) -> list[LanguageConfig]:
    if args.all:
        return iter_unique_languages(include_combined=False)

    lang_configs: list[LanguageConfig] = []
    seen: set[str] = set()

    for name in args.languages:
        try:
            cfg = get_language(name)
        except ValueError as exc:
            logger.critical("%s", exc)
            sys.exit(1)

        if cfg.name not in seen:
            seen.add(cfg.name)
            lang_configs.append(cfg)

    return lang_configs


def process_language(
    repo_path: Path,
    lang_config: LanguageConfig,
    output_dir: Path,
    collect_options: CollectOptions,
    render_options: PDFRenderOptions,
    markdown_options: MarkdownRenderOptions,
    output_format: str,
    max_pages: int | None = None,
) -> list[str]:
    repo_name = repo_path.name

    logger.info(
        "Processing language: %s (extensions: %s)",
        lang_config.display_name,
        ", ".join(lang_config.extensions),
    )

    logger.info("Building file tree...")
    tree_text = get_tree_string(str(repo_path), lang_config, collect_options)

    logger.info("Collecting files...")
    files = collect_files(str(repo_path), lang_config, collect_options)
    logger.info("Found %d file(s)", len(files))

    if not files:
        logger.warning("No files with extensions %s found — skipping", lang_config.extensions)
        return []

    for file_info in files:
        logger.debug(" %s", file_info["path"])

    output_dir.mkdir(parents=True, exist_ok=True)

    generated: list[str] = []
    output_base = output_dir / f"{repo_name}_{lang_config.name}_docs"

    if output_format in ("pdf", "both"):
        generated.extend(
            generate_pdf(
                tree_text=tree_text,
                files=files,
                output_path=str(output_base.with_suffix(".pdf")),
                repo_name=repo_name,
                lang_config=lang_config,
                max_pages=max_pages,
                render_options=render_options,
            )
        )

    if output_format in ("md", "both"):
        generated.append(
            generate_markdown(
                tree_text=tree_text,
                files=files,
                output_path=str(output_base.with_suffix(".md")),
                repo_name=repo_name,
                lang_config=lang_config,
                render_options=markdown_options,
            )
        )

    return generated


def main() -> None:
    args = parse_args()
    _configure_logging(args.verbose)

    if args.list_langs:
        print("\nAvailable languages:\n")
        for line in list_languages():
            print(line)
        print()
        return

    repo_path = Path(args.repo_path).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not repo_path.is_dir():
        logger.critical("'%s' is not a directory", repo_path)
        sys.exit(1)

    if args.max_file_size <= 0:
        logger.critical("--max-file-size must be positive")
        sys.exit(1)

    max_pages = _resolve_max_pages(args)
    if max_pages:
        logger.info("PDF splitting enabled: approximate max %d pages per file", max_pages)

    collect_options = CollectOptions(
        include_tree_only_matching=not args.full_tree,
        max_file_size_bytes=int(args.max_file_size * 1024 * 1024),
        include_patterns=tuple(args.include),
        exclude_patterns=tuple(args.exclude),
    )
    render_options = PDFRenderOptions(
        wrap_long_lines=not args.truncate_lines,
        max_chars_per_line=args.max_line_chars,
    )
    markdown_options = MarkdownRenderOptions(
        include_line_numbers=args.md_line_numbers,
        include_tree=not args.no_md_tree,
    )

    lang_configs = _resolve_languages(args)
    all_generated: list[str] = []

    logger.info("Repository: %s", repo_path)

    for lang_config in lang_configs:
        generated = process_language(
            repo_path=repo_path,
            lang_config=lang_config,
            output_dir=output_dir,
            collect_options=collect_options,
            render_options=render_options,
            markdown_options=markdown_options,
            output_format=args.format,
            max_pages=max_pages,
        )
        all_generated.extend(generated)

    if all_generated:
        logger.info("=" * 50)
        logger.info("Generated %d file(s):", len(all_generated))
        for file_path in all_generated:
            logger.info(" • %s", file_path)

    logger.info("Done")


if __name__ == "__main__":
    main()
