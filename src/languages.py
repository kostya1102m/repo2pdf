from dataclasses import dataclass, field


@dataclass
class LanguageConfig:
    name: str
    display_name: str
    extensions: list[str]
    extra_ignore_dirs: list[str] = field(default_factory=list)
    description: str = ""

    @property
    def glob_patterns(self) -> list[str]:
        return [f"*{ext}" for ext in self.extensions]


BASE_IGNORED_DIRS = {
    '.venv', 'venv', 'env', '.env',
    '__pycache__', '.git', '.hg', '.svn',
    '.idea', '.vscode',
    '.mypy_cache', '.pytest_cache', '.ruff_cache',
    'dist', 'build',
    '.tox', '.nox',
    '.eggs',
}

PYTHON = LanguageConfig(
    name="python",
    display_name="Python",
    extensions=[".py"],
    extra_ignore_dirs=["__pycache__", "*.egg-info", "migrations"],
    description="Python source files (.py)",
)

JAVASCRIPT = LanguageConfig(
    name="javascript",
    display_name="JavaScript",
    extensions=[".js", ".jsx", ".mjs"],
    extra_ignore_dirs=["node_modules", "bower_components", ".next", ".nuxt", "coverage"],
    description="JavaScript source files (.js, .jsx, .mjs)",
)

TYPESCRIPT = LanguageConfig(
    name="typescript",
    display_name="TypeScript",
    extensions=[".ts", ".tsx"],
    extra_ignore_dirs=["node_modules", "bower_components", ".next", ".nuxt", "coverage"],
    description="TypeScript source files (.ts, .tsx)",
)

JUPYTER = LanguageConfig(
    name="jupyter",
    display_name="Jupyter Notebook",
    extensions=[".ipynb"],
    extra_ignore_dirs=[".ipynb_checkpoints"],
    description="Jupyter Notebook files (.ipynb)",
)

JS_TS = LanguageConfig(
    name="js_ts",
    display_name="JavaScript + TypeScript",
    extensions=[".js", ".jsx", ".mjs", ".ts", ".tsx"],
    extra_ignore_dirs=["node_modules", "bower_components", ".next", ".nuxt", "coverage"],
    description="JS & TS source files",
)

LANGUAGES: dict[str, LanguageConfig] = {
    "python": PYTHON, "py": PYTHON,
    "javascript": JAVASCRIPT, "js": JAVASCRIPT,
    "typescript": TYPESCRIPT, "ts": TYPESCRIPT,
    "jupyter": JUPYTER, "ipynb": JUPYTER, "notebook": JUPYTER,
    "js_ts": JS_TS, "jsts": JS_TS,
}


def get_language(name: str) -> LanguageConfig:
    key = name.lower().strip()
    if key not in LANGUAGES:
        available = sorted(set(cfg.name for cfg in LANGUAGES.values()))
        raise ValueError(
            f"Unknown language: '{name}'. Available: {', '.join(available)}"
        )
    return LANGUAGES[key]


def list_languages() -> list[str]:
    seen = set()
    result = []
    for cfg in LANGUAGES.values():
        if cfg.name not in seen:
            seen.add(cfg.name)
            result.append(f"  {cfg.name:15s} — {cfg.description}")
    return result