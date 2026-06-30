from dataclasses import dataclass, field


@dataclass(frozen=True)
class LanguageConfig:
    name: str
    display_name: str
    extensions: tuple[str, ...]
    ignore_patterns: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""

    @property
    def glob_patterns(self) -> tuple[str, ...]:
        return tuple(f"*{ext}" for ext in self.extensions)


BASE_IGNORE_PATTERNS: tuple[str, ...] = (
    ".venv",
    "venv",
    "env",
    ".env",
    ".env.*",
    "__pycache__",
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".tox",
    ".nox",
    ".eggs",
    "node_modules",
    ".mvn",
    ".gradle",
    "target",
    "*.pem",
    "*.key",
    "id_rsa",
    "id_ed25519",
)

PYTHON = LanguageConfig(
    name="python",
    display_name="Python",
    extensions=(".py",),
    ignore_patterns=("__pycache__", "*.egg-info", "migrations"),
    description="Python source files (.py)",
)

JAVASCRIPT = LanguageConfig(
    name="javascript",
    display_name="JavaScript",
    extensions=(".js", ".jsx", ".mjs"),
    ignore_patterns=(
        "node_modules",
        "bower_components",
        ".next",
        ".nuxt",
        "coverage",
        "*.min.js",
        "*.bundle.js",
    ),
    description="JavaScript source files (.js, .jsx, .mjs)",
)

TYPESCRIPT = LanguageConfig(
    name="typescript",
    display_name="TypeScript",
    extensions=(".ts", ".tsx"),
    ignore_patterns=(
        "node_modules",
        "bower_components",
        ".next",
        ".nuxt",
        "coverage",
        "*.min.js",
        "*.bundle.js",
    ),
    description="TypeScript source files (.ts, .tsx)",
)

JUPYTER = LanguageConfig(
    name="jupyter",
    display_name="Jupyter Notebook",
    extensions=(".ipynb",),
    ignore_patterns=(".ipynb_checkpoints",),
    description="Jupyter Notebook files (.ipynb)",
)

JS_TS = LanguageConfig(
    name="js_ts",
    display_name="JavaScript + TypeScript",
    extensions=(".js", ".jsx", ".mjs", ".ts", ".tsx"),
    ignore_patterns=(
        "node_modules",
        "bower_components",
        ".next",
        ".nuxt",
        "coverage",
        "*.min.js",
        "*.bundle.js",
    ),
    description="JS & TS source files",
)

JAVA = LanguageConfig(
    name="java",
    display_name="Java",
    extensions=(".java",),
    ignore_patterns=(
        "target",
        "bin",
        "out",
        ".gradle",
        "gradle",
        ".settings",
        ".classpath",
        ".project",
        ".mvn",
    ),
    description="Java source files (.java)",
)

XML = LanguageConfig(
    name="xml",
    display_name="XML",
    extensions=(".xml", ".xsd", ".xsl", ".xslt", ".wsdl", ".pom"),
    ignore_patterns=("target", "bin", "out", ".gradle"),
    description="XML files (.xml, .xsd, .xsl, .xslt, .wsdl, .pom)",
)

YAML = LanguageConfig(
    name="yaml",
    display_name="YAML",
    extensions=(".yml", ".yaml"),
    description="YAML files (.yml, .yaml)",
)

SQL = LanguageConfig(
    name="sql",
    display_name="SQL",
    extensions=(".sql",),
    ignore_patterns=("migrations",),
    description="SQL files (.sql)",
)

HTML = LanguageConfig(
    name="html",
    display_name="HTML",
    extensions=(".html", ".htm"),
    description="HTML files (.html, .htm)",
)

LANGUAGES: dict[str, LanguageConfig] = {
    "python": PYTHON,
    "py": PYTHON,
    "javascript": JAVASCRIPT,
    "js": JAVASCRIPT,
    "typescript": TYPESCRIPT,
    "ts": TYPESCRIPT,
    "jupyter": JUPYTER,
    "ipynb": JUPYTER,
    "notebook": JUPYTER,
    "js_ts": JS_TS,
    "jsts": JS_TS,
    "java": JAVA,
    "xml": XML,
    "yaml": YAML,
    "yml": YAML,
    "sql": SQL,
    "html": HTML,
    "htm": HTML,
}


def get_language(name: str) -> LanguageConfig:
    key = name.lower().strip()
    if key not in LANGUAGES:
        available = sorted({cfg.name for cfg in LANGUAGES.values()})
        raise ValueError(f"Unknown language: '{name}'. Available: {', '.join(available)}")
    return LANGUAGES[key]


def iter_unique_languages(include_combined: bool = False) -> list[LanguageConfig]:
    seen: set[str] = set()
    result: list[LanguageConfig] = []

    for cfg in LANGUAGES.values():
        if cfg.name == "js_ts" and not include_combined:
            continue
        if cfg.name in seen:
            continue
        seen.add(cfg.name)
        result.append(cfg)

    return result


def list_languages() -> list[str]:
    return [f"  {cfg.name:15s} — {cfg.description}" for cfg in iter_unique_languages(include_combined=True)]
