#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
command -v xelatex >/dev/null || { echo 'XeLaTeX not found in PATH. Install MacTeX or TeX Live.' >&2; exit 1; }
mkdir -p build
for extension in aux toc out; do
    if [[ -f "lab3.$extension" ]]; then
        mkdir -p build/previous-root
        mv -f -- "lab3.$extension" "build/previous-root/lab3.$extension"
    fi
done
for pass in 1 2; do
    xelatex -interaction=nonstopmode -halt-on-error -output-directory=build lab3.tex
done
if ! grep -q '\\contentsline' build/lab3.toc; then
    echo 'The table of contents is empty. The final PDF was not replaced.' >&2
    exit 1
fi
if grep -Eq 'There were undefined references|Label\(s\) may have changed' build/lab3.log; then
    echo 'Cross-references are not resolved. The final PDF was not replaced.' >&2
    exit 1
fi
cp -- build/lab3.pdf lab3.pdf
echo 'Built lab3.pdf with a nonempty table of contents and resolved references.'
