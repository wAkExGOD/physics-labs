from pathlib import Path
import ast
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
root = Path(__file__).resolve().parents[1]
# Расшифровываем старые \uXXXX-подписи в lab1: значения строк те же,
# но в исходнике теперь видно русский текст вместо кодов символов.
source = root / "lab1/lab1.py"
text = source.read_text(encoding="utf-8")
text = re.sub(r"\\u([0-9a-fA-F]{4})", lambda match: chr(int(match[1], 16)), text)
source.write_text(text, encoding="utf-8")

before = json.loads((root / "build/code_before.json").read_text(encoding="utf-8"))
for lab in ("lab1", "lab2", "lab3"):
    filename = root / lab / f"{lab}.py"
    code = filename.read_text(encoding="utf-8")
    tree = ast.parse(code)
    assert ast.dump(tree, include_attributes=False) == before[lab], f"Changed calculations in {lab}"
    compile(code, str(filename), "exec")
    faq = (root / lab / "FAQ.md").read_text(encoding="utf-8")
    assert not re.search(r"^\\[\[\]]$", faq, re.M)
    display = False
    for line in faq.splitlines():
        if line == "$$":
            display = not display
        elif not display:
            assert line.count("$") % 2 == 0, line
    assert not display, f"Unclosed display in {lab}"
    for expression in re.findall(r"\$\$[\s\S]*?\$\$|\$[^$\n]*\$", faq):
        assert expression.count("{") == expression.count("}"), expression
    comments = sum(line.lstrip().startswith("#") for line in code.splitlines())
    print(f"{lab}: AST unchanged; syntax OK; {comments} comment lines; FAQ math delimiters OK")
