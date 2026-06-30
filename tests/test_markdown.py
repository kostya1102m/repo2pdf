from pathlib import Path

from repo2pdf.languages import PYTHON
from repo2pdf.markdown import MarkdownRenderOptions, generate_markdown


def test_generate_markdown_creates_file(tmp_path: Path):
    output = tmp_path / "docs.md"

    result = generate_markdown(
        tree_text="repo/\n└── main.py",
        files=[{"path": "main.py", "content": "print('hello')"}],
        output_path=str(output),
        repo_name="repo",
        lang_config=PYTHON,
    )

    assert result == str(output)
    assert output.exists()

    content = output.read_text(encoding="utf-8")
    assert "# repo" in content
    assert "## Project Structure" in content
    assert "### `main.py`" in content
    assert "```python" in content
    assert "print('hello')" in content


def test_generate_markdown_with_line_numbers(tmp_path: Path):
    output = tmp_path / "docs.md"

    generate_markdown(
        tree_text="repo/",
        files=[{"path": "main.py", "content": "a = 1\nb = 2"}],
        output_path=str(output),
        repo_name="repo",
        lang_config=PYTHON,
        render_options=MarkdownRenderOptions(include_line_numbers=True),
    )

    content = output.read_text(encoding="utf-8")
    assert "  1 | a = 1" in content
    assert "  2 | b = 2" in content
    assert "```text" in content