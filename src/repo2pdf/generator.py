import logging
import textwrap
from dataclasses import dataclass
from pathlib import Path

from fpdf import FPDF

from .fonts import download_fonts, get_font_path
from .languages import LanguageConfig

logger = logging.getLogger(__name__)


THEMES = {
    "python": {
        "accent": (55, 118, 171),
        "header_bg": (45, 55, 72),
        "code_bg": (245, 245, 250),
        "title_accent": (55, 118, 171),
    },
    "javascript": {
        "accent": (240, 219, 79),
        "header_bg": (50, 50, 50),
        "code_bg": (255, 252, 240),
        "title_accent": (200, 180, 50),
    },
    "typescript": {
        "accent": (49, 120, 198),
        "header_bg": (40, 50, 65),
        "code_bg": (242, 246, 252),
        "title_accent": (49, 120, 198),
    },
    "jupyter": {
        "accent": (230, 126, 34),
        "header_bg": (60, 45, 30),
        "code_bg": (255, 248, 240),
        "title_accent": (230, 126, 34),
    },
    "js_ts": {
        "accent": (240, 219, 79),
        "header_bg": (50, 50, 50),
        "code_bg": (255, 252, 240),
        "title_accent": (200, 180, 50),
    },
    "java": {
        "accent": (176, 114, 25),
        "header_bg": (60, 40, 20),
        "code_bg": (255, 250, 240),
        "title_accent": (176, 114, 25),
    },
    "xml": {
        "accent": (0, 128, 0),
        "header_bg": (30, 60, 30),
        "code_bg": (240, 255, 240),
        "title_accent": (0, 128, 0),
    },
    "yaml": {
        "accent": (203, 56, 55),
        "header_bg": (65, 30, 30),
        "code_bg": (255, 245, 245),
        "title_accent": (203, 56, 55),
    },
    "sql": {
        "accent": (0, 102, 153),
        "header_bg": (20, 50, 65),
        "code_bg": (240, 248, 255),
        "title_accent": (0, 102, 153),
    },
    "html": {
        "accent": (227, 76, 38),
        "header_bg": (65, 35, 20),
        "code_bg": (255, 245, 238),
        "title_accent": (227, 76, 38),
    },
}

DEFAULT_THEME = {
    "accent": (100, 100, 100),
    "header_bg": (50, 50, 50),
    "code_bg": (245, 245, 245),
    "title_accent": (100, 100, 100),
}


@dataclass(frozen=True)
class PDFRenderOptions:
    wrap_long_lines: bool = True
    max_chars_per_line: int = 100
    code_font_size: float = 7.5
    line_height: float = 4.2


class RepoPDF(FPDF):
    def __init__(
        self,
        repo_name: str,
        lang_config: LanguageConfig,
        part_number: int | None = None,
        total_parts: int | None = None,
        render_options: PDFRenderOptions | None = None,
    ):
        super().__init__()
        self.repo_name = repo_name
        self.lang_config = lang_config
        self.theme = THEMES.get(lang_config.name, DEFAULT_THEME)
        self.part_number = part_number
        self.total_parts = total_parts
        self.render_options = render_options or PDFRenderOptions()
        self._register_fonts()

    def _register_fonts(self) -> None:
        download_fonts()
        self.add_font("DejaVuMono", "", get_font_path("DejaVuSansMono.ttf"))
        self.add_font("DejaVuMono", "B", get_font_path("DejaVuSansMono-Bold.ttf"))
        self.add_font("DejaVuMono", "I", get_font_path("DejaVuSansMono-Oblique.ttf"))
        self.add_font("DejaVuSans", "", get_font_path("DejaVuSans.ttf"))
        self.add_font("DejaVuSans", "B", get_font_path("DejaVuSans-Bold.ttf"))

    def header(self) -> None:
        if self.page_no() == 1:
            return

        self.set_font("DejaVuSans", "B", 9)
        self.set_text_color(120, 120, 120)

        header_text = f"{self.repo_name} | {self.lang_config.display_name}"
        if self.part_number is not None:
            header_text += f" | Part {self.part_number}/{self.total_parts}"

        self.cell(0, 8, header_text, align="L")
        self.ln(3)

        r, g, b = self.theme["accent"]
        self.set_draw_color(r, g, b)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_line_width(0.2)
        self.ln(6)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("DejaVuSans", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"-- {self.page_no()} / {{nb}} --", align="C")

    def add_title_page(self, file_count: int, files_range: tuple[int, int] | None = None) -> None:
        self.add_page()
        self.ln(50)

        self.set_font("DejaVuSans", "B", 36)
        r, g, b = self.theme["title_accent"]
        self.set_text_color(r, g, b)
        self.cell(0, 20, self.repo_name, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(8)

        self.set_font("DejaVuSans", "", 16)
        self.set_text_color(80, 80, 80)
        self.cell(
            0,
            10,
            f"{self.lang_config.display_name} Documentation",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        if self.part_number is not None:
            self.ln(3)
            self.set_font("DejaVuSans", "B", 14)
            self.set_text_color(100, 100, 100)
            self.cell(
                0,
                10,
                f"Part {self.part_number} of {self.total_parts}",
                align="C",
                new_x="LMARGIN",
                new_y="NEXT",
            )

        if files_range:
            self.set_font("DejaVuSans", "", 11)
            self.cell(
                0,
                8,
                f"Files {files_range[0]} — {files_range[1]} of {file_count}",
                align="C",
                new_x="LMARGIN",
                new_y="NEXT",
            )

        self.ln(5)
        self.set_font("DejaVuSans", "", 12)
        self.set_text_color(120, 120, 120)

        ext_str = ", ".join(self.lang_config.extensions)
        files_text = f"Files: {file_count}" if self.part_number is None else f"Total Files: {file_count}"
        self.cell(
            0,
            8,
            f"{files_text} | Extensions: {ext_str}",
            align="C",
            new_x="LMARGIN",
            new_y="NEXT",
        )

        self.ln(15)
        r, g, b = self.theme["accent"]
        self.set_draw_color(r, g, b)
        self.set_line_width(1.0)
        self.line(60, self.get_y(), 150, self.get_y())
        self.set_line_width(0.2)

    def add_section_title(self, title: str) -> None:
        self.add_page()
        self.set_font("DejaVuSans", "B", 22)
        self.set_text_color(30, 30, 30)
        self.cell(0, 15, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

        r, g, b = self.theme["accent"]
        self.set_draw_color(r, g, b)
        self.set_line_width(1.0)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_line_width(0.2)
        self.ln(8)

    def add_tree(self, tree_text: str) -> None:
        self.set_font("DejaVuMono", "", 9)
        self.set_text_color(30, 30, 30)

        for line in tree_text.splitlines():
            if self.get_y() > 272:
                self.add_page()
                self.set_font("DejaVuMono", "", 9)
                self.set_text_color(30, 30, 30)
            self.cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")

    def _file_header_bar(self, text: str, bg_color: tuple[int, int, int]) -> None:
        r, g, b = bg_color
        self.set_fill_color(r, g, b)
        self.set_text_color(255, 255, 255)
        self.set_font("DejaVuMono", "B", 10)
        self.cell(0, 9, f" {text}", fill=True, new_x="LMARGIN", new_y="NEXT")

    def add_file_content(self, file_path: str, content: str) -> None:
        if self.get_y() > 235:
            self.add_page()

        self.ln(4)
        self._file_header_bar(file_path, self.theme["header_bg"])

        options = self.render_options
        self.set_font("DejaVuMono", "", options.code_font_size)
        self.set_text_color(30, 30, 30)

        cr, cg, cb = self.theme["code_bg"]
        self.set_fill_color(cr, cg, cb)

        lines = content.splitlines() or [""]
        line_num_width = max(len(str(len(lines))), 3)

        for line_no, line in enumerate(lines, 1):
            for visual_line_no, display in enumerate(self._format_code_line(line)):
                if self.get_y() > 277:
                    self.add_page()
                    cont_bg = tuple(min(c + 30, 255) for c in self.theme["header_bg"])
                    self._file_header_bar(f"{file_path} (continued)", cont_bg)
                    self.set_font("DejaVuMono", "", options.code_font_size)
                    self.set_text_color(30, 30, 30)
                    self.set_fill_color(cr, cg, cb)

                prefix = str(line_no).rjust(line_num_width) if visual_line_no == 0 else " " * line_num_width
                text = f" {prefix} | {display}"
                self.cell(0, options.line_height, text, fill=True, new_x="LMARGIN", new_y="NEXT")

        self.ln(3)

    def _format_code_line(self, line: str) -> list[str]:
        options = self.render_options
        display = line.replace("\t", "    ")

        if not options.wrap_long_lines:
            if len(display) > options.max_chars_per_line:
                return [display[: options.max_chars_per_line] + " ..."]
            return [display]

        return textwrap.wrap(
            display,
            width=options.max_chars_per_line,
            replace_whitespace=False,
            drop_whitespace=False,
        ) or [""]


class PDFSplitter:
    """Approximate content splitter for large generated PDFs."""

    LINES_PER_PAGE = 55
    TREE_LINES_PER_PAGE = 50
    TITLE_PAGES = 2

    def __init__(self, max_pages: int = 50):
        self.max_pages = max_pages

    def estimate_file_pages(self, content: str) -> int:
        lines = content.count("\n") + 1
        pages = (lines + self.LINES_PER_PAGE - 1) // self.LINES_PER_PAGE
        return max(1, pages)

    def estimate_tree_pages(self, tree_text: str | None) -> int:
        if not tree_text:
            return 0
        lines = tree_text.count("\n") + 1
        return max(1, (lines + self.TREE_LINES_PER_PAGE - 1) // self.TREE_LINES_PER_PAGE)

    def split_files(self, files: list[dict[str, str]], tree_text: str) -> list[list[dict[str, str]]]:
        if not files:
            return [files]

        tree_pages = self.estimate_tree_pages(tree_text)
        parts: list[list[dict[str, str]]] = []
        current_part: list[dict[str, str]] = []
        current_pages = self.TITLE_PAGES + tree_pages + 1

        for file_info in files:
            file_pages = self.estimate_file_pages(file_info["content"])

            if current_pages + file_pages > self.max_pages and current_part:
                parts.append(current_part)
                current_part = []
                current_pages = self.TITLE_PAGES + 1

            current_part.append(file_info)
            current_pages += file_pages

        if current_part:
            parts.append(current_part)

        return parts


def generate_pdf(
    tree_text: str,
    files: list[dict[str, str]],
    output_path: str,
    repo_name: str,
    lang_config: LanguageConfig,
    max_pages: int | None = None,
    render_options: PDFRenderOptions | None = None,
) -> list[str]:
    if max_pages is None:
        return [_generate_single_pdf(tree_text, files, output_path, repo_name, lang_config, render_options)]

    splitter = PDFSplitter(max_pages)
    parts = splitter.split_files(files, tree_text)

    if len(parts) <= 1:
        return [_generate_single_pdf(tree_text, files, output_path, repo_name, lang_config, render_options)]

    output_base = Path(output_path)
    generated_files: list[str] = []
    total_files = len(files)
    file_counter = 0

    for part_num, part_files in enumerate(parts, 1):
        part_output = output_base.parent / f"{output_base.stem}_part{part_num}_of_{len(parts)}{output_base.suffix}"

        files_start = file_counter + 1
        files_end = file_counter + len(part_files)
        file_counter = files_end

        _generate_part_pdf(
            tree_text=tree_text if part_num == 1 else None,
            files=part_files,
            output_path=str(part_output),
            repo_name=repo_name,
            lang_config=lang_config,
            part_number=part_num,
            total_parts=len(parts),
            total_files=total_files,
            files_range=(files_start, files_end),
            render_options=render_options,
        )

        generated_files.append(str(part_output))

    return generated_files


def _new_pdf(
    repo_name: str,
    lang_config: LanguageConfig,
    render_options: PDFRenderOptions | None = None,
    part_number: int | None = None,
    total_parts: int | None = None,
) -> RepoPDF:
    pdf = RepoPDF(repo_name, lang_config, part_number, total_parts, render_options)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    return pdf


def _generate_single_pdf(
    tree_text: str,
    files: list[dict[str, str]],
    output_path: str,
    repo_name: str,
    lang_config: LanguageConfig,
    render_options: PDFRenderOptions | None = None,
) -> str:
    logger.info("Generating PDF: %s", output_path)

    pdf = _new_pdf(repo_name, lang_config, render_options)
    pdf.add_title_page(len(files))

    pdf.add_section_title("Project Structure")
    pdf.add_tree(tree_text)

    if files:
        pdf.add_section_title(f"Source Code ({lang_config.display_name})")
        for file_info in files:
            pdf.add_file_content(file_info["path"], file_info["content"])

    pdf.output(output_path)
    logger.info("PDF saved: %s", output_path)

    return output_path


def _generate_part_pdf(
    tree_text: str | None,
    files: list[dict[str, str]],
    output_path: str,
    repo_name: str,
    lang_config: LanguageConfig,
    part_number: int,
    total_parts: int,
    total_files: int,
    files_range: tuple[int, int],
    render_options: PDFRenderOptions | None = None,
) -> str:
    logger.info("Generating PDF part %d/%d: %s", part_number, total_parts, output_path)

    pdf = _new_pdf(repo_name, lang_config, render_options, part_number, total_parts)
    pdf.add_title_page(total_files, files_range)

    if tree_text is not None:
        pdf.add_section_title("Project Structure")
        pdf.add_tree(tree_text)

    if files:
        section_title = f"Source Code ({lang_config.display_name})"
        if total_parts > 1:
            section_title += f" — Part {part_number}"
        pdf.add_section_title(section_title)

    for file_info in files:
        pdf.add_file_content(file_info["path"], file_info["content"])

    pdf.output(output_path)
    logger.info("PDF part saved: %s (%d files)", output_path, len(files))

    return output_path
