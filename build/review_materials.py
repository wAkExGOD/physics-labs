from pathlib import Path
import ast
import json
import sys
from pypdf import PdfReader

sys.stdout.reconfigure(encoding="utf-8")
root = Path(__file__).resolve().parents[1]
snapshots = {}
for lab in ("lab1", "lab2", "lab3"):
    code = (root / lab / f"{lab}.py").read_text(encoding="utf-8")
    snapshots[lab] = ast.dump(ast.parse(code), include_attributes=False)
    for pdf in ("instructions.pdf", "theory.pdf"):
        source = root / lab / pdf
        if not source.exists():
            continue
        text = "\n".join(f"PAGE {i}\n{page.extract_text()}" for i, page in enumerate(PdfReader(source).pages, 1))
        (root / "build" / f"{lab}_{pdf}.txt").write_text(text, encoding="utf-8")
        print(f"\nFILE {lab}/{pdf}\n{text}")
(root / "build" / "code_before.json").write_text(json.dumps(snapshots), encoding="utf-8")
