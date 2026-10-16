param([string]$Python = "python")
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
& $Python scripts/collect_licenses.py
if ($LASTEXITCODE -ne 0) { throw "No se pudieron recopilar las licencias." }
& $Python -m PyInstaller --noconfirm --clean --windowed --onedir --name MarkItDown-ES --icon markitdown_es/assets/app.ico --copy-metadata markitdown --copy-metadata magika --collect-data magika --collect-data markitdown --collect-data pypdfium2 --add-data "LICENSE;." --add-data "THIRD_PARTY.md;." --add-data "build/third-party-notices;third_party_licenses" --add-data "markitdown_es/assets;markitdown_es/assets" launcher.py
if ($LASTEXITCODE -ne 0) { throw "No se pudo empaquetar el ejecutable." }
Copy-Item README.md,LICENSE,THIRD_PARTY.md -Destination dist/MarkItDown-ES
Copy-Item docs -Destination dist/MarkItDown-ES -Recurse -Force
Compress-Archive -Path dist/MarkItDown-ES -DestinationPath dist/MarkItDown-ES-Windows-x64.zip -Force
$digest = (Get-FileHash dist/MarkItDown-ES-Windows-x64.zip -Algorithm SHA256).Hash.ToLower()
"$digest  MarkItDown-ES-Windows-x64.zip" | Set-Content dist/MarkItDown-ES-Windows-x64.zip.sha256 -Encoding ascii
Write-Host "Listo: dist/MarkItDown-ES-Windows-x64.zip"
