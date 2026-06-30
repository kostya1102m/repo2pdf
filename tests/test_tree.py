from pathlib import Path

from repo2pdf.languages import get_language
from repo2pdf.tree import CollectOptions, collect_files, get_tree_string


def test_collect_files_ignores_excluded_paths(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("print(1)", encoding="utf-8")
    (tmp_path / "src" / "a.min.js").write_text("console.log(1)", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("assert True", encoding="utf-8")

    files = collect_files(
        str(tmp_path),
        get_language("python"),
        CollectOptions(exclude_patterns=("tests/*",)),
    )

    assert [f["path"] for f in files] == ["src/a.py"]


def test_tree_only_matching_files_by_default(tmp_path: Path):
    (tmp_path / "a.py").write_text("print(1)", encoding="utf-8")
    (tmp_path / "README.md").write_text("# docs", encoding="utf-8")

    tree = get_tree_string(str(tmp_path), get_language("python"))

    assert "a.py" in tree
    assert "README.md" not in tree
