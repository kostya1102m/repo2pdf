import logging
from fpdf import FPDF

from font_setup import get_font_path, download_fonts
from languages import LanguageConfig

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
}

DEFAULT_THEME = {
    "accent": (100, 100, 100),
    "header_bg": (50, 50, 50),
    "code_bg": (245, 245, 245),
    "title_accent": (100, 100, 100),
}


class RepoPDF(FPDF):

    def __init__(self, repo_name: str, lang_config: LanguageConfig):
        super().__init__()
        self.repo_name = repo_name
        self.lang_config = lang_config
        self.theme = THEMES.get(lang_config.name, DEFAULT_THEME)
        self._register_fonts()

    def _register_fonts(self):
        download_fonts()
        self.add_font("DejaVuMono", "", get_font_path("DejaVuSansMono.ttf"))
        self.add_font("DejaVuMono", "B", get_font_path("DejaVuSansMono-Bold.ttf"))
        self.add_font("DejaVuMono", "I", get_font_path("DejaVuSansMono-Oblique.ttf"))
        self.add_font("DejaVuSans", "", get_font_path("DejaVuSans.ttf"))
        self.add_font("DejaVuSans", "B", get_font_path("DejaVuSans-Bold.ttf"))

    def header(self):
        if self.page_no() == 1:
            return

        self.set_font("DejaVuSans", "B", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"{self.repo_name}  |  {self.lang_config.display_name}", align="L")
        self.ln(3)

        r, g, b = self.theme["accent"]
        self.set_draw_color(r, g, b)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 200, self.get_y())
        self.set_line_width(0.2)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVuSans", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"-- {self.page_no()} / {{nb}} --", align="C")

    def add_title_page(self, file_count: int):
        self.add_page()
        self.ln(50)

        self.set_font("DejaVuSans", "B", 36)
        r, g, b = self.theme["title_accent"]
        self.set_text_color(r, g, b)
        self.cell(0, 20, self.repo_name, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(8)

        self.set_font("DejaVuSans", "", 16)
        self.set_text_color(80, 80, 80)
        self.cell(0, 10, f"{self.lang_config.display_name} Documentation",
                  align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

        self.set_font("DejaVuSans", "", 12)
        self.set_text_color(120, 120, 120)
        ext_str = ", ".join(self.lang_config.extensions)
        self.cell(0, 8, f"Files: {file_count}  |  Extensions: {ext_str}",
                  align="C", new_x="LMARGIN", new_y="NEXT")

        self.ln(15)
        r, g, b = self.theme["accent"]
        self.set_draw_color(r, g, b)
        self.set_line_width(1.0)
        self.line(60, self.get_y(), 150, self.get_y())
        self.set_line_width(0.2)

    def add_section_title(self, title: str):
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

    def add_tree(self, tree_text: str):
        self.set_font("DejaVuMono", "", 9)
        self.set_text_color(30, 30, 30)

        for line in tree_text.split("\n"):
            if self.get_y() > 272:
                self.add_page()
                self.set_font("DejaVuMono", "", 9)
                self.set_text_color(30, 30, 30)
            self.cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")

    def _file_header_bar(self, text: str, bg_color: tuple):
        r, g, b = bg_color
        self.set_fill_color(r, g, b)
        self.set_text_color(255, 255, 255)
        self.set_font("DejaVuMono", "B", 10)
        self.cell(0, 9, f"  {text}", fill=True, new_x="LMARGIN", new_y="NEXT")

    def add_file_content(self, file_path: str, content: str):
        if self.get_y() > 235:
            self.add_page()

        self.ln(4)
        self._file_header_bar(file_path, self.theme["header_bg"])

        code_font_size = 7.5
        line_height = 4.2
        max_chars = 100

        self.set_font("DejaVuMono", "", code_font_size)
        self.set_text_color(30, 30, 30)
        cr, cg, cb = self.theme["code_bg"]
        self.set_fill_color(cr, cg, cb)

        lines = content.split("\n")
        line_num_width = max(len(str(len(lines))), 3)

        for i, line in enumerate(lines, 1):
            if self.get_y() > 277:
                self.add_page()
                cont_bg = tuple(min(c + 30, 255) for c in self.theme["header_bg"])
                self._file_header_bar(f"{file_path}  (continued)", cont_bg)
                self.set_font("DejaVuMono", "", code_font_size)
                self.set_text_color(30, 30, 30)
                self.set_fill_color(cr, cg, cb)

            display = line.replace("\t", "    ")
            if len(display) > max_chars:
                display = display[:max_chars] + " ..."

            line_num = str(i).rjust(line_num_width)
            text = f" {line_num} | {display}"
            self.cell(0, line_height, text, fill=True, new_x="LMARGIN", new_y="NEXT")

        self.ln(3)


def generate_pdf(
    tree_text: str,
    files: list[dict],
    output_path: str,
    repo_name: str,
    lang_config: LanguageConfig,
):
    logger.info("Generating PDF: %s", output_path)

    pdf = RepoPDF(repo_name, lang_config)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_title_page(len(files))

    pdf.add_section_title("Project Structure")
    pdf.add_tree(tree_text)

    if files:
        pdf.add_section_title(f"Source Code ({lang_config.display_name})")
        for file_info in files:
            pdf.add_file_content(file_info["path"], file_info["content"])

    pdf.output(output_path)
    logger.info("PDF saved: %s", output_path)