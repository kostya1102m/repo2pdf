import argparse
import logging
import sys
from pathlib import Path

from .languages import get_language, list_languages, LanguageConfig
from .tree import get_tree_string, collect_files
from .generator import generate_pdf

logger = logging.getLogger(__name__)


def _configure_logging(verbosity: int):
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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate PDF documentation from a repository.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  repo2pdf . -l python                     Python files only
  repo2pdf . -l js                         JavaScript only
  repo2pdf . -l python js jupyter          Multiple languages (separate PDFs)
  repo2pdf . --all                         All supported languages
  repo2pdf --list                          Show available languages
  repo2pdf . -l python -v                  Info-level logging
  repo2pdf . -l python -vv                 Debug-level logging
  
Splitting large PDFs:
  repo2pdf . -l python --max-pages 50      Split into 50-page parts
  repo2pdf . -l python --max-pages 100     Split into 100-page parts
  repo2pdf . -l python --split             Auto-split (default: 50 pages)
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
        help="Generate PDF for all supported languages",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        help="Output directory for PDFs (default: current)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_langs",
        help="Show available languages and exit",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase logging verbosity (-v for INFO, -vv for DEBUG)",
    )

    # Новые аргументы для разбиения
    split_group = parser.add_argument_group("PDF splitting options")
    split_group.add_argument(
        "--max-pages",
        type=int,
        default=None,
        metavar="N",
        help="Maximum pages per PDF file. Splits into parts if exceeded.",
    )
    split_exclusive = split_group.add_mutually_exclusive_group()
    split_exclusive.add_argument(
        "--split", action="store_true",
        help="Enable auto-splitting with default limit (50 pages)",
    )
    split_exclusive.add_argument(
        "--no-split", action="store_true",
        help="Disable splitting (generate single PDF regardless of size)",
    )

    return parser.parse_args()


def process_language(
    repo_path: Path,
    lang_config: LanguageConfig,
    output_dir: Path,
    max_pages: int = None,
) -> list[str]:
    """
    Обрабатывает один язык и возвращает список созданных PDF файлов.
    """
    repo_name = repo_path.name

    logger.info(
        "Processing language: %s (extensions: %s)",
        lang_config.display_name,
        ", ".join(lang_config.extensions),
    )

    logger.info("Building file tree...")
    tree_text = get_tree_string(str(repo_path), lang_config)

    logger.info("Collecting files...")
    files = collect_files(str(repo_path), lang_config)
    logger.info("Found %d file(s)", len(files))

    if not files:
        logger.warning(
            "No files with extensions %s found — skipping",
            lang_config.extensions,
        )
        return []

    for f in files:
        logger.debug("  %s", f["path"])

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{repo_name}_{lang_config.name}_docs.pdf"

    generated_files = generate_pdf(
        tree_text=tree_text,
        files=files,
        output_path=str(output_file),
        repo_name=repo_name,
        lang_config=lang_config,
        max_pages=max_pages,
    )

    return generated_files


def main():
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

    logger.info("Repository: %s", repo_path)

    # Определяем лимит страниц
    if args.split and args.max_pages is not None:
        logger.warning(
            "Both --split and --max-pages specified; using --max-pages %d",
            args.max_pages,
        )
    if args.no_split:
        max_pages = None
    elif args.max_pages is not None:
        max_pages = args.max_pages
        if max_pages < 10:
            logger.warning("--max-pages should be at least 10, using 10")
            max_pages = 10
    elif args.split:
        max_pages = 50  # Значение по умолчанию при --split
    else:
        max_pages = None  # Без разбиения по умолчанию

    if max_pages:
        logger.info("PDF splitting enabled: max %d pages per file", max_pages)

    if args.all:
        unique_names = [
            "python",
            "javascript",
            "typescript",
            "jupyter",
            "java",
            "xml",
            "yaml",
            "sql",
            "html",
        ]
        lang_configs = [get_language(name) for name in unique_names]
    else:
        lang_configs = []
        seen = set()
        for name in args.languages:
            try:
                cfg = get_language(name)
                if cfg.name not in seen:
                    seen.add(cfg.name)
                    lang_configs.append(cfg)
            except ValueError as e:
                logger.critical("%s", e)
                sys.exit(1)

    all_generated = []

    for lang_config in lang_configs:
        generated = process_language(repo_path, lang_config, output_dir, max_pages)
        all_generated.extend(generated)

    # Итоговая статистика
    if all_generated:
        logger.info("=" * 50)
        logger.info("Generated %d PDF file(s):", len(all_generated))
        for f in all_generated:
            logger.info("  • %s", f)

    logger.info("Done")


if __name__ == "__main__":
    main()
