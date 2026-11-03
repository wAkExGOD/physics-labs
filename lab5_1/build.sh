#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
command -v xelatex >/dev/null || { echo 'Install MacTeX or TeX Live (XeLaTeX).' >&2; exit 1; }
mkdir -p build
for extension in aux toc out; do
    if [[ -f "lab5.$extension" ]]; then
        mkdir -p build/previous-root
        mv -f -- "lab5.$extension" "build/previous-root/lab5.$extension"
    fi
done
for pass in 1 2; do
    xelatex -interaction=nonstopmode -halt-on-error -output-directory=build lab5.tex
done
grep -q '\\contentsline' build/lab5.toc || { echo 'The table of contents is empty.' >&2; exit 1; }
if grep -Eq 'There were undefined references|Label\(s\) may have changed|Missing character:' build/lab5.log; then
    echo 'Unresolved references or missing glyphs. See build/lab5.log.' >&2
    exit 1
fi
cp -- build/lab5.pdf lab5.pdf
echo 'Built lab5_1/lab5.pdf'
