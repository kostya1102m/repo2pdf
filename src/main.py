import argparse
import logging
import sys
from pathlib import Path

from languages import get_language, list_languages, LanguageConfig
from tree_builder import get_tree_string, collect_files
from pdf_generator import generate_pdf

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
  python main.py . -l python                 Python files only
  python main.py . -l js                     JavaScript only
  python main.py . -l python js jupyter      Multiple languages (separate PDFs)
  python main.py . --all                     All supported languages
  python main.py --list                      Show available languages
  python main.py . -l python -v              Info-level logging
  python main.py . -l python -vv             Debug-level logging
        """,
    )
    parser.add_argument(
        "repo_path", nargs="?", default=".",
        help="Path to repository (default: current directory)",
    )
    parser.add_argument(
        "-l", "--languages", nargs="+", default=["python"],
        help="Languages to generate (default: python)",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Generate PDF for all supported languages",
    )
    parser.add_argument(
        "-o", "--output-dir", default=".",
        help="Output directory for PDFs (default: current)",
    )
    parser.add_argument(
        "--list", action="store_true", dest="list_langs",
        help="Show available languages and exit",
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0,
        help="Increase logging verbosity (-v for INFO, -vv for DEBUG)",
    )
    return parser.parse_args()


def process_language(repo_path: Path, lang_config: LanguageConfig, output_dir: Path):
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
        return

    for f in files:
        logger.debug("  %s", f["path"])

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{repo_name}_{lang_config.name}_docs.pdf"

    generate_pdf(
        tree_text=tree_text,
        files=files,
        output_path=str(output_file),
        repo_name=repo_name,
        lang_config=lang_config,
    )


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

    if args.all:
        unique_names = ["python", "javascript", "typescript", "jupyter"]
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

    for lang_config in lang_configs:
        process_language(repo_path, lang_config, output_dir)

    logger.info("Done")


if __name__ == "__main__":
    main()