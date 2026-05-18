# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None

# Collect all files from tkinterweb and weasyprint
tw_datas, tw_bins, tw_hidden = collect_all('tkinterweb')
wp_datas, wp_bins, wp_hidden = collect_all('weasyprint')
md_datas, md_bins, md_hidden = collect_all('markdown')
pyg_datas, pyg_bins, pyg_hidden = collect_all('pygments')

# GTK3 DLLs – path set by CI env var or common local install
GTK_BIN = os.environ.get('GTK3_BIN', r'C:\GTK3\bin')
gtk_root = str(Path(GTK_BIN).parent)

extra_binaries = []
extra_datas = []

if os.path.isdir(GTK_BIN):
    for fname in os.listdir(GTK_BIN):
        if fname.lower().endswith('.dll'):
            extra_binaries.append((os.path.join(GTK_BIN, fname), '.'))

    for subdir in (
        'lib\\gdk-pixbuf-2.0',
        'lib\\gio',
        'share\\glib-2.0\\schemas',
        'share\\icons\\hicolor',
        'etc\\fonts',
        'etc\\gtk-3.0',
    ):
        full = os.path.join(gtk_root, subdir)
        if os.path.isdir(full):
            for root, dirs, files in os.walk(full):
                for f in files:
                    src = os.path.join(root, f)
                    rel = os.path.relpath(os.path.dirname(src), gtk_root)
                    extra_datas.append((src, rel))

icon_path = 'assets/icon.ico' if os.path.exists('assets/icon.ico') else None

a = Analysis(
    ['readme_to_pdf.py'],
    pathex=[],
    binaries=[*tw_bins, *wp_bins, *md_bins, *pyg_bins, *extra_binaries],
    datas=[*tw_datas, *wp_datas, *md_datas, *pyg_datas, *extra_datas],
    hiddenimports=[
        *tw_hidden, *wp_hidden, *md_hidden, *pyg_hidden,
        'markdown.extensions.tables',
        'markdown.extensions.fenced_code',
        'markdown.extensions.codehilite',
        'markdown.extensions.toc',
        'markdown.extensions.nl2br',
        'markdown.extensions.sane_lists',
        'markdown.extensions.attr_list',
        'pygments.styles',
        'pygments.lexers',
        'pygments.formatters',
        'weasyprint.css.properties',
        'weasyprint.text.ffi',
        'weasyprint.text.fonts',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'scipy', 'pandas', 'IPython'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe_kwargs = dict(
    name='MarkdownToPDF',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
if icon_path:
    exe_kwargs['icon'] = icon_path

exe = EXE(pyz, a.scripts, [], exclude_binaries=True, **exe_kwargs)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='MarkdownToPDF',
)
