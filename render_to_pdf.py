import sqlite3
import re
import os
import math
import argparse
import subprocess
from pathlib import Path

# Configuration
DB_PATH = "KJV-PCE.sqlite"
LATEX_OUTPUT_DIR = "latex_output"
PDF_OUTPUT_DIR = "pdf_output"
FONT_DIR = "fonts"
os.makedirs(LATEX_OUTPUT_DIR, exist_ok=True)
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)

# Layout constants
LINE_HEIGHT_PT = 1.6 * 12
PAGE_HEIGHT_CM = 21.0 - 2 * 0.8
PAGE_HEIGHT_PT = PAGE_HEIGHT_CM * 28.3465
LINES_PER_COLUMN = math.floor(PAGE_HEIGHT_PT / LINE_HEIGHT_PT)
MIN_LINES_FOR_PARAGRAPH = 7

def format_supplied_words(text):
    return re.sub(r"\[(.+?)\]", r"\\textit{\1}", text)

def estimate_lines(text):
    avg_chars_per_line = 95
    return math.ceil(len(text) / avg_chars_per_line) +1

def fetch_verses(book_name, chapter):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT BookID FROM Books WHERE BookName = ?", (book_name,))
    book_id_row = c.fetchone()
    if not book_id_row:
        raise ValueError(f"Book '{book_name}' not found.")
    book_id = book_id_row[0]
    c.execute("""
        SELECT V.Verse, V.VText,
               CASE WHEN S.BookID IS NOT NULL THEN 1 ELSE 0 END AS HasPilcrow
        FROM Verses V
        LEFT JOIN Scrivener S ON V.BookID = S.BookID AND V.Chapter = S.Chapter AND V.Verse = S.Verse
        WHERE V.BookID = ? AND V.Chapter = ?
        ORDER BY V.Verse
    """, (book_id, chapter))
    rows = c.fetchall()
    conn.close()
    return rows

def fetch_all_chapters(book_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT BookID FROM Books WHERE BookName = ?", (book_name,))
    book_id_row = c.fetchone()
    if not book_id_row:
        raise ValueError(f"Book '{book_name}' not found.")
    book_id = book_id_row[0]
    c.execute("SELECT Chapter FROM Chapters WHERE BookID = ? ORDER BY Chapter", (book_id,))
    chapters = [row[0] for row in c.fetchall()]
    conn.close()
    return chapters

def group_paragraphs(verses):
    paragraphs = []
    current = ""
    for verse, text, has_pilcrow in verses:
        text = format_supplied_words(text)
        if has_pilcrow:
            if current:
                paragraphs.append(current.strip())
            current = f"\\pilcrow {text}"
        else:
            current += f" {text}"
    if current:
        paragraphs.append(current.strip())
    return paragraphs

def generate_latex(paragraphs, book, chapter):
    lines_used = 0
    body = ""
    for p in paragraphs:
        para_lines = estimate_lines(p) + 2
        lines_remaining = LINES_PER_COLUMN - (lines_used % LINES_PER_COLUMN)
        if para_lines > lines_remaining and lines_remaining < MIN_LINES_FOR_PARAGRAPH:
            body += "\n\\vfill\\null\\columnbreak\n"
            lines_used = (lines_used // LINES_PER_COLUMN + 1) * LINES_PER_COLUMN
        body += p + "\n\\par\\vspace{0.6em}\n"
        lines_used += para_lines + 1
    return f"""
\\documentclass[landscape, a4paper, 12pt]{{article}}
\\usepackage[margin=0.8cm]{{geometry}}
\\usepackage{{parskip}}
\\usepackage{{fontspec}}
\\usepackage{{titlesec}}
\\usepackage{{setspace}}
\\usepackage{{multicol}}

\\setmainfont{{IBMPlexSerif-Medium.ttf}}[Path={FONT_DIR}/, ItalicFont=IBMPlexSerif-MediumItalic.ttf, BoldFont=IBMPlexSerif-Bold.ttf]
\\newfontfamily\\plexsans{{IBMPlexSans-Regular.ttf}}[Path={FONT_DIR}/]
\\newfontfamily\\kjvblackletter{{kjv1611-regular.otf}}[Path={FONT_DIR}/]

\\newcommand{{\\pilcrow}}{{\\textbf{{\\P}}\\hspace{{0.3em}}}}

\\titleformat{{\\section}}{{\\kjvblackletter\\centering\\Huge}}{{}}{{0pt}}{{}}
\\pagestyle{{empty}}
\\setlength{{\\columnsep}}{{1.2em}}
\\setlength{{\\columnseprule}}{{0.5pt}}

\\begin{{document}}

\\section*{{{book} {chapter}}}

\\vspace{{0.5em}}

\\begin{{multicols}}{{2}}
{body}
\\end{{multicols}}

\\end{{document}}
""".strip()

def render_latex_chapter(book, chapter):
    verses = fetch_verses(book, chapter)
    if not verses:
        raise ValueError("No verses found.")
    grouped = group_paragraphs(verses)
    tex = generate_latex(grouped, book, chapter)
    tex_filename = f"{book.replace(' ', '_')}_{chapter}_formatted.tex"
    tex_path = os.path.join(LATEX_OUTPUT_DIR, tex_filename)
    Path(tex_path).write_text(tex, encoding="utf-8")
    print(f"✅ LaTeX saved to {tex_path}")
    subprocess.run(["xelatex", "-output-directory", PDF_OUTPUT_DIR, tex_path], check=True)

def render_all_chapters(book):
    chapters = fetch_all_chapters(book)
    for chapter in chapters:
        render_latex_chapter(book, chapter)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("book", type=str, help="Book name (e.g., Acts)")
    parser.add_argument("chapter", type=int, nargs="?", help="Chapter number (optional)")
    args = parser.parse_args()

    if args.chapter:
        render_latex_chapter(args.book, args.chapter)
    else:
        render_all_chapters(args.book)
