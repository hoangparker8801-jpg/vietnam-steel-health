"""
Build the code-free report from the notebook.

Usage (from this folder):
    .venv\\Scripts\\python build_report.py

It runs every cell of analysis.ipynb, hides the code, applies report_style.css
and writes vietnam_steel_report.html.
"""

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTEBOOK = HERE / "analysis.ipynb"
OUTPUT = HERE / "vietnam_steel_report.html"
STYLE = HERE / "report_style.css"

subprocess.run(
    [
        sys.executable, "-m", "jupyter", "nbconvert",
        "--to", "html", "--execute", "--no-input", "--no-prompt",
        str(NOTEBOOK), "--output", OUTPUT.stem,
    ],
    check=True,
    cwd=HERE,
)

html = OUTPUT.read_text(encoding="utf-8")
css = STYLE.read_text(encoding="utf-8")
html = html.replace("</head>", f"<style>\n{css}\n</style>\n</head>", 1)
OUTPUT.write_text(html, encoding="utf-8")
print(f"Report written to {OUTPUT}")

# PDF version, printed by Microsoft Edge in the background (no header or footer)
import os
import tempfile

PDF = OUTPUT.with_suffix(".pdf")
edge_paths = [
    Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft/Edge/Application/msedge.exe",
    Path(os.environ.get("ProgramFiles", "")) / "Microsoft/Edge/Application/msedge.exe",
]
edge = next((p for p in edge_paths if p.is_file()), None)
if edge is None:
    print("Microsoft Edge not found: open the HTML report and use Ctrl + P > Save as PDF instead.")
else:
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run(
            [
                str(edge), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--user-data-dir={profile}", f"--print-to-pdf={PDF}", OUTPUT.as_uri(),
            ],
            check=True,
            timeout=180,
        )
    print(f"PDF written to {PDF}")
