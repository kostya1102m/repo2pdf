from repo2pdf.languages import get_language, iter_unique_languages


def test_aliases_resolve_to_same_config():
    assert get_language("py").name == "python"
    assert get_language("js").name == "javascript"


def test_unique_languages_excludes_combined_by_default():
    names = [cfg.name for cfg in iter_unique_languages()]
    assert "js_ts" not in names
    assert len(names) == len(set(names))
