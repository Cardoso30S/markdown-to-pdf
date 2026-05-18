#!/usr/bin/env python3
"""Converte README.md (ou qualquer arquivo Markdown) em PDF com estilo limpo."""

import argparse
import sys
from pathlib import Path

import markdown
from weasyprint import HTML, CSS


CSS_STYLE = """
@page {
    size: A4;
    margin: 2.5cm 2cm 2.5cm 2cm;
    @bottom-center {
        content: counter(page) " / " counter(pages);
        font-size: 9pt;
        color: #9ca3af;
    }
}
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 11pt; line-height: 1.7; color: #1f2937; }
h1 { font-size: 22pt; border-bottom: 3px solid #3b82f6; padding-bottom: 0.3em; color: #1d4ed8; margin-top: 0; }
h2 { font-size: 16pt; border-bottom: 1.5px solid #e5e7eb; padding-bottom: 0.25em; color: #1e40af; }
h3 { font-size: 13pt; } h4 { font-size: 11pt; }
h1,h2,h3,h4,h5,h6 { font-weight: 700; margin-top: 1.4em; margin-bottom: 0.5em; page-break-after: avoid; }
p { margin-bottom: 0.9em; }
code { font-family: 'Courier New', monospace; font-size: 9.5pt; background: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 4px; padding: 1px 5px; color: #dc2626; }
pre { background: #1e293b; color: #e2e8f0; border-radius: 8px; padding: 1em 1.2em; font-size: 9pt; margin: 1em 0; page-break-inside: avoid; border-left: 4px solid #3b82f6; }
pre code { background: none; border: none; padding: 0; color: inherit; }
blockquote { border-left: 4px solid #3b82f6; background: #eff6ff; margin: 1em 0; padding: 0.7em 1em; border-radius: 0 6px 6px 0; color: #1e40af; font-style: italic; }
table { width: 100%; border-collapse: collapse; margin: 1em 0; font-size: 10pt; page-break-inside: avoid; }
thead tr { background: #1d4ed8; color: #fff; }
thead th { padding: 0.6em 1em; text-align: left; font-weight: 600; }
tbody tr:nth-child(even) { background: #f8fafc; }
td, th { border: 1px solid #e5e7eb; padding: 0.5em 1em; }
ul, ol { padding-left: 1.6em; margin-bottom: 0.9em; }
li { margin-bottom: 0.3em; }
hr { border: none; border-top: 2px solid #e5e7eb; margin: 1.5em 0; }
img { max-width: 100%; height: auto; border-radius: 6px; }
strong { font-weight: 700; } em { font-style: italic; }
"""


def convert(md_path: Path, pdf_path: Path) -> None:
    md_text = md_path.read_text(encoding="utf-8")
    extensions = ["tables", "fenced_code", "codehilite", "toc", "nl2br", "sane_lists", "attr_list"]
    html_body = markdown.markdown(md_text, extensions=extensions)
    html_full = f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8"><title>{md_path.stem}</title></head>
<body>{html_body}</body></html>"""
    HTML(string=html_full, base_url=str(md_path.parent)).write_pdf(str(pdf_path), stylesheets=[CSS(string=CSS_STYLE)])


def main() -> None:
    parser = argparse.ArgumentParser(description="Converte um arquivo Markdown (.md) em PDF.")
    parser.add_argument("input", nargs="?", default="README.md", help="Arquivo Markdown de entrada")
    parser.add_argument("-o", "--output", default=None, help="Arquivo PDF de saída")
    args = parser.parse_args()

    md_path = Path(args.input)
    if not md_path.exists():
        print(f"Erro: arquivo '{md_path}' não encontrado.", file=sys.stderr)
        sys.exit(1)

    pdf_path = Path(args.output) if args.output else md_path.with_suffix(".pdf")
    print(f"Convertendo '{md_path}' → '{pdf_path}' ...")
    convert(md_path, pdf_path)
    print(f"PDF gerado com sucesso: {pdf_path}")


if __name__ == "__main__":
    main()