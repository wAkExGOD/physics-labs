$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $compiler = Get-Command xelatex -ErrorAction SilentlyContinue
    if ($compiler) {
        $xelatex = $compiler.Source
    } elseif ($env:LOCALAPPDATA) {
        $xelatex = Join-Path $env:LOCALAPPDATA 'Programs\MiKTeX\miktex\bin\x64\xelatex.exe'
        if (-not (Test-Path -LiteralPath $xelatex)) {
            throw 'XeLaTeX was not found. Install MiKTeX or TeX Live and add it to PATH.'
        }
    } else {
        throw 'XeLaTeX was not found in PATH. Install MacTeX or TeX Live.'
    }
    New-Item -ItemType Directory -Force build | Out-Null
    foreach ($extension in @('aux', 'toc', 'out')) {
        $stale = "lab3.$extension"
        if (Test-Path -LiteralPath $stale) {
            New-Item -ItemType Directory -Force build/previous-root | Out-Null
            Move-Item -LiteralPath $stale -Destination "build/previous-root/$stale" -Force
        }
    }
    foreach ($pass in 1..2) {
        & $xelatex -interaction=nonstopmode -halt-on-error -output-directory=build lab3.tex
        if ($LASTEXITCODE -ne 0) {
            throw "XeLaTeX failed on pass $pass. See build/lab3.log."
        }
    }
    $toc = Get-Content -LiteralPath build/lab3.toc -Raw
    $log = Get-Content -LiteralPath build/lab3.log -Raw
    if (-not $toc -or $toc -notmatch '\\contentsline') {
        throw 'The table of contents is empty. The final PDF was not replaced.'
    }
    if ($log -match 'There were undefined references|Label\(s\) may have changed') {
        throw 'Cross-references are not resolved. The final PDF was not replaced.'
    }
    Copy-Item -LiteralPath build/lab3.pdf -Destination lab3.pdf -Force
    Write-Host 'Built lab3.pdf with a nonempty table of contents and resolved references.'
} finally {
    Pop-Location
}
