#!/usr/bin/env bash
# From the project root: bash build_pdf.sh [1|2|3|4|5 ...]. Without arguments: all labs.
set -euo pipefail
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
command -v xelatex >/dev/null || {
    echo 'XeLaTeX not found. Install MacTeX and reopen Terminal. See MAC_SETUP.md.' >&2
    exit 1
}
if [[ $# -eq 0 ]]; then
    set -- 1 2 3 4 5
fi
for number in "$@"; do
    case "$number" in
        1|2|3|4|5) ;;
        *) echo 'Usage: bash build_pdf.sh [1|2|3|4|5 ...]' >&2; exit 1 ;;
    esac
done
for number in "$@"; do
    (
        cd -- "$PROJECT_DIR/lab$number"
        name="lab$number"
        mkdir -p build
        # Stale auxiliary files next to the source can shadow the output files.
        for extension in aux toc out; do
            if [[ -f "$name.$extension" ]]; then
                mkdir -p build/previous-root
                mv -f -- "$name.$extension" "build/previous-root/$name.$extension"
            fi
        done
        for pass in 1 2; do
            xelatex -interaction=nonstopmode -halt-on-error -output-directory=build "$name.tex"
        done
        if [[ "$number" != 1 ]] && ! grep -q '\\contentsline' "build/$name.toc"; then
            echo "$name: table of contents is empty; final PDF was not replaced." >&2
            exit 1
        fi
        if grep -Eq 'There were undefined references|Label\(s\) may have changed|Missing character:' "build/$name.log"; then
            echo "$name: unresolved references or missing glyphs; see build/$name.log." >&2
            exit 1
        fi
        cp -- "build/$name.pdf" "$name.pdf"
        echo "Built $name/$name.pdf"
    )
done
