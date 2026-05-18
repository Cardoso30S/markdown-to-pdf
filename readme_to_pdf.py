#!/usr/bin/env python3
"""Markdown → PDF converter with a full Tkinter GUI and live HTML preview."""

import re
import sys
import threading
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

# Strip @page { ... } block — it is PDF-only and not valid in browsers / tkinterweb
_PAGE_RULE_RE = re.compile(r"@page\s*\{[^}]*\}", re.DOTALL)
CSS_PREVIEW = _PAGE_RULE_RE.sub("", CSS_STYLE).strip()

# Patterns for Gemini/AI citation annotations that should not appear in output
_CITE_RE = re.compile(r"\[cite_start\]|\[cite_end\]|\[cite:\s*[\d,\s]+\]", re.IGNORECASE)


def _strip_citations(text: str) -> str:
    """Remove [cite_start], [cite_end] and [cite: N, M] annotations."""
    return _CITE_RE.sub("", text)


_MD_EXTENSIONS = [
    "tables",
    "fenced_code",
    "codehilite",
    "toc",
    "nl2br",
    "sane_lists",
    "attr_list",
]


# ---------------------------------------------------------------------------
# Core conversion helpers (shared between CLI and GUI)
# ---------------------------------------------------------------------------

def _md_to_html_body(md_path: Path) -> str:
    md_text = _strip_citations(md_path.read_text(encoding="utf-8"))
    return markdown.markdown(md_text, extensions=_MD_EXTENSIONS)


def convert(md_path: Path, pdf_path: Path) -> None:
    """Convert *md_path* to a PDF file saved at *pdf_path*."""
    html_body = _md_to_html_body(md_path)
    html_full = (
        f'<!DOCTYPE html>\n'
        f'<html lang="pt-BR"><head><meta charset="UTF-8">'
        f'<title>{md_path.stem}</title></head>\n'
        f'<body>{html_body}</body></html>'
    )
    HTML(string=html_full, base_url=str(md_path.parent)).write_pdf(
        str(pdf_path), stylesheets=[CSS(string=CSS_STYLE)]
    )


def build_preview_html(md_path: Path) -> str:
    """Return a self-contained HTML string suitable for the GUI preview."""
    html_body = _md_to_html_body(md_path)
    return (
        f'<!DOCTYPE html>\n'
        f'<html lang="pt-BR">\n'
        f'<head>\n'
        f'<meta charset="UTF-8">\n'
        f'<style>\n{CSS_PREVIEW}\n'
        f'body {{ max-width: 860px; margin: 0 auto; padding: 24px 32px; }}\n'
        f'</style>\n'
        f'</head>\n'
        f'<body>{html_body}</body>\n'
        f'</html>'
    )


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

def run_gui() -> None:
    import tkinter as tk
    from tkinter import filedialog

    try:
        from tkinterweb import HtmlFrame
        HAVE_HTMLFRAME = True
    except ImportError:
        HAVE_HTMLFRAME = False

    # ── root window ──────────────────────────────────────────────────────────
    root = tk.Tk()
    root.title("Markdown → PDF Converter")
    root.geometry("950x720")
    root.resizable(True, True)
    root.configure(bg="#f1f5f9")

    # ── shared variables ─────────────────────────────────────────────────────
    md_path_var = tk.StringVar()
    pdf_path_var = tk.StringVar()
    status_var = tk.StringVar(value="Aguardando...")
    preview_label_var = tk.StringVar(value="Prévia do PDF:")

    # ── header ───────────────────────────────────────────────────────────────
    header = tk.Frame(root, bg="#1d4ed8", pady=14)
    header.pack(fill="x")
    tk.Label(
        header,
        text="Markdown → PDF Converter",
        bg="#1d4ed8",
        fg="white",
        font=("Segoe UI", 16, "bold"),
    ).pack()

    # ── input row ────────────────────────────────────────────────────────────
    input_frame = tk.Frame(root, bg="#f1f5f9", pady=8, padx=12)
    input_frame.pack(fill="x")

    tk.Label(
        input_frame,
        text="Arquivo:",
        bg="#f1f5f9",
        font=("Segoe UI", 10),
    ).grid(row=0, column=0, sticky="w", padx=(0, 6))

    md_entry = tk.Entry(
        input_frame,
        textvariable=md_path_var,
        font=("Segoe UI", 10),
        relief="flat",
        bd=1,
        highlightthickness=1,
        highlightbackground="#cbd5e1",
        highlightcolor="#3b82f6",
    )
    md_entry.grid(row=0, column=1, sticky="ew", ipady=4)

    def _refresh_preview(p: Path) -> None:
        """Render the markdown in a background thread then push HTML to the widget."""
        def _worker() -> None:
            try:
                html = build_preview_html(p)
            except Exception as exc:
                html = f"<p style='color:red;font-family:sans-serif'>Erro ao renderizar prévia: {exc}</p>"

            def _update() -> None:
                if HAVE_HTMLFRAME:
                    html_frame.load_html(html)
                else:
                    html_frame.configure(state="normal")
                    html_frame.delete("1.0", "end")
                    html_frame.insert("end", html)
                    html_frame.configure(state="disabled")

            root.after(0, _update)

        threading.Thread(target=_worker, daemon=True).start()

    def _browse_md() -> None:
        path = filedialog.askopenfilename(
            title="Selecionar arquivo Markdown",
            filetypes=[
                ("Markdown files", "*.md *.markdown"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        md_path_var.set(path)
        p = Path(path)
        # Auto-fill PDF output path when not yet set
        if not pdf_path_var.get():
            pdf_path_var.set(str(p.with_suffix(".pdf")))
        preview_label_var.set(f"Prévia do PDF:  ({p.name})")
        status_var.set(f"Arquivo selecionado: {p.name}")
        _refresh_preview(p)

    browse_md_btn = tk.Button(
        input_frame,
        text="Procurar",
        command=_browse_md,
        bg="#3b82f6",
        fg="white",
        relief="flat",
        padx=10,
        pady=4,
        font=("Segoe UI", 10),
        cursor="hand2",
        activebackground="#2563eb",
        activeforeground="white",
    )
    browse_md_btn.grid(row=0, column=2, padx=(6, 0))

    input_frame.columnconfigure(1, weight=1)

    # ── preview area ─────────────────────────────────────────────────────────
    preview_outer = tk.Frame(root, bg="#f1f5f9", padx=12)
    preview_outer.pack(fill="both", expand=True)

    tk.Label(
        preview_outer,
        textvariable=preview_label_var,
        bg="#f1f5f9",
        font=("Segoe UI", 10, "bold"),
        anchor="w",
    ).pack(fill="x", pady=(4, 2))

    preview_border = tk.Frame(preview_outer, bg="#cbd5e1", bd=1, relief="flat")
    preview_border.pack(fill="both", expand=True, pady=(0, 6))

    if HAVE_HTMLFRAME:
        html_frame = HtmlFrame(preview_border, messages_enabled=False)
        html_frame.pack(fill="both", expand=True, padx=1, pady=1)
    else:
        # Graceful fallback when tkinterweb is unavailable
        html_frame = tk.Text(
            preview_border,
            wrap="word",
            font=("Segoe UI", 10),
            relief="flat",
            state="disabled",
        )
        html_frame.pack(fill="both", expand=True, padx=1, pady=1)

    # ── bottom section ───────────────────────────────────────────────────────
    bottom = tk.Frame(root, bg="#e2e8f0", pady=10, padx=12)
    bottom.pack(fill="x", side="bottom")

    # Status bar
    tk.Label(
        bottom,
        textvariable=status_var,
        bg="#e2e8f0",
        fg="#374151",
        font=("Segoe UI", 9),
        anchor="w",
        padx=4,
    ).grid(row=2, column=0, columnspan=4, sticky="ew", pady=(4, 0))

    # Output path row
    tk.Label(
        bottom,
        text="Salvar como:",
        bg="#e2e8f0",
        font=("Segoe UI", 10),
    ).grid(row=0, column=0, sticky="w", padx=(0, 6))

    pdf_entry = tk.Entry(
        bottom,
        textvariable=pdf_path_var,
        font=("Segoe UI", 10),
        relief="flat",
        bd=1,
        highlightthickness=1,
        highlightbackground="#cbd5e1",
        highlightcolor="#3b82f6",
    )
    pdf_entry.grid(row=0, column=1, sticky="ew", ipady=4)

    def _browse_pdf() -> None:
        initial = pdf_path_var.get() or "output.pdf"
        path = filedialog.asksaveasfilename(
            title="Salvar PDF como",
            initialfile=Path(initial).name,
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if path:
            pdf_path_var.set(path)

    browse_pdf_btn = tk.Button(
        bottom,
        text="Procurar",
        command=_browse_pdf,
        bg="#64748b",
        fg="white",
        relief="flat",
        padx=10,
        pady=4,
        font=("Segoe UI", 10),
        cursor="hand2",
        activebackground="#475569",
        activeforeground="white",
    )
    browse_pdf_btn.grid(row=0, column=2, padx=(6, 6))

    last_pdf: list[Path] = []

    def _open_pdf() -> None:
        if not last_pdf:
            return
        p = last_pdf[0]
        if not p.exists():
            status_var.set(f"Arquivo não encontrado: {p}")
            return
        import subprocess, os
        try:
            if sys.platform == "win32":
                os.startfile(str(p))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(p)])
            else:
                subprocess.Popen(["xdg-open", str(p)])
        except Exception as exc:
            status_var.set(f"Não foi possível abrir: {exc}")

    open_btn = tk.Button(
        bottom,
        text="⬇ Baixar PDF",
        command=_open_pdf,
        bg="#0369a1",
        fg="white",
        relief="flat",
        padx=14,
        pady=6,
        font=("Segoe UI", 10, "bold"),
        cursor="hand2",
        state="disabled",
        activebackground="#075985",
        activeforeground="white",
    )
    open_btn.grid(row=0, column=3, padx=(0, 0))

    bottom.columnconfigure(1, weight=1)

    # Convert button — full width, prominent
    convert_btn = tk.Button(
        bottom,
        text="⚙  Converter para PDF",
        bg="#16a34a",
        fg="white",
        relief="flat",
        padx=14,
        pady=10,
        font=("Segoe UI", 12, "bold"),
        cursor="hand2",
        activebackground="#15803d",
        activeforeground="white",
    )
    convert_btn.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(8, 4))

    def _do_convert() -> None:
        md_str = md_path_var.get().strip()
        pdf_str = pdf_path_var.get().strip()

        if not md_str:
            status_var.set("Erro: nenhum arquivo Markdown selecionado.")
            return
        md_p = Path(md_str)
        if not md_p.exists():
            status_var.set(f"Erro: arquivo '{md_p}' não encontrado.")
            return
        pdf_p = Path(pdf_str) if pdf_str else md_p.with_suffix(".pdf")

        convert_btn.configure(state="disabled", bg="#6b7280")
        open_btn.configure(state="disabled")
        status_var.set("Convertendo, aguarde...")

        def _worker() -> None:
            try:
                convert(md_p, pdf_p)
                msg = f"✓ PDF gerado com sucesso: {pdf_p}"
                def _done() -> None:
                    status_var.set(msg)
                    convert_btn.configure(state="normal", bg="#16a34a")
                    last_pdf.clear()
                    last_pdf.append(pdf_p)
                    open_btn.configure(state="normal")
            except Exception as exc:
                msg = f"✗ Erro na conversão: {exc}"
                def _done() -> None:
                    status_var.set(msg)
                    convert_btn.configure(state="normal", bg="#dc2626")

            root.after(0, _done)

        threading.Thread(target=_worker, daemon=True).start()

    convert_btn.configure(command=_do_convert)

    root.mainloop()


# ---------------------------------------------------------------------------
# CLI entry-point (kept for backward compatibility)
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Converte um arquivo Markdown (.md) em PDF."
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Abrir interface gráfica",
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="Arquivo Markdown de entrada (omitir abre a GUI)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Arquivo PDF de saída",
    )
    args = parser.parse_args()

    if args.gui or args.input is None:
        run_gui()
        return

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
