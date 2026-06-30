from repo2pdf.generator import PDFSplitter


def test_splitter_splits_when_limit_exceeded():
    files = [
        {"path": "a.py", "content": "\n".join(["x"] * 200)},
        {"path": "b.py", "content": "\n".join(["x"] * 200)},
    ]

    parts = PDFSplitter(max_pages=10).split_files(files, "root/\n├── a.py\n└── b.py")

    assert len(parts) == 2
