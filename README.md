# repo2pdf

A Python library and CLI tool to convert Git repositories into formatted PDF documentation. It supports syntax highlighting, directory trees, and full Unicode (Cyrillic/Emoji) via auto-downloaded DejaVu fonts.

## Installation

### As a Library / Tool (User)
```bash
pip install git+https://github.com/kostya1102m/repo2pdf.git
```
### For Development
```bash
git clone https://github.com/kostya1102m/repo2pdf.git
cd repo2pdf
poetry install
```
### CLI Usage

The package installs the repo2pdf command.

```bash

# Basic usage (current directory, Python files)
repo2pdf . -l python

# Specific path and languages
repo2pdf /path/to/project -l js typescript

# Generate PDFs for all supported languages
repo2pdf . --all

# Custom output directory and verbose logging
repo2pdf . -l python -o ./documentation -vv

# List available languages
repo2pdf --list

```

### Python API
You can use repo2pdf directly in your scripts to generate documentation programmatically.

```python
from repo2pdf import generate_pdf, get_language, collect_files, get_tree_string

# 1. Setup
repo_path = "."
# Options: python, js, ts, jupyter, js_ts
config = get_language("python")

# 2. Collect Data
tree_text = get_tree_string(repo_path, config)
files = collect_files(repo_path, config)

# 3. Generate PDF
generate_pdf(
    tree_text=tree_text,
    files=files,
    output_path="project_docs.pdf",
    repo_name="My Project",
    lang_config=config
)

```

### Features
1.Supported Formats: Python (.py), JavaScript (.js, .jsx, .mjs), TypeScript (.ts, .tsx), Jupyter (.ipynb).

2.Smart Filtering: Automatically ignores node_modules, __pycache__, .git, venv, and other system directories.

3.Jupyter Notebooks: Extracts code and markdown cells into a readable format.

4.Unicode Ready: Handles Cyrillic and special characters out of the box using embedded DejaVu fonts.

### Requirements:
Python 3.10+

fpdf2

requests