param([string]$SourceDirectory = (Split-Path $PSScriptRoot -Parent), [switch]$NoCopy)
$ErrorActionPreference = 'Stop'
$source = (Resolve-Path -LiteralPath $SourceDirectory).Path
$destination = Join-Path $env:LOCALAPPDATA 'Programs\MarkItDownES'
if ($NoCopy) { $destination = $source }
elseif ($source -ne $destination) {
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    Get-ChildItem -LiteralPath $source | Copy-Item -Destination $destination -Recurse -Force
}
$executable = Join-Path $destination 'MarkItDown-ES.exe'
if (-not (Test-Path -LiteralPath $executable)) { throw 'No se encontró el ejecutable. Extrae toda la carpeta del ZIP antes de instalar.' }
$programId = 'MarkItDownES.Document'
$classKey = "HKCU:\Software\Classes\$programId"
New-Item -Path "$classKey\shell\open\command" -Force | Out-Null
Set-Item -Path $classKey -Value 'Documento Markdown'
Set-Item -Path "$classKey\shell\open\command" -Value ('"' + $executable + '" "%1"')
New-Item -Path "$classKey\DefaultIcon" -Force | Out-Null
Set-Item -Path "$classKey\DefaultIcon" -Value ('"' + $executable + '",0')
New-Item -Path 'HKCU:\Software\Classes\.md\OpenWithProgids' -Force | Out-Null
New-ItemProperty -Path 'HKCU:\Software\Classes\.md\OpenWithProgids' -Name $programId -Value '' -PropertyType String -Force | Out-Null
$currentChoice = Get-ItemPropertyValue -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.md\UserChoice' -Name ProgId -ErrorAction SilentlyContinue
$oldDefault = (Get-Item 'Registry::HKEY_CLASSES_ROOT\.md' -ErrorAction SilentlyContinue).GetValue('')
if (-not $currentChoice -and -not $oldDefault) { Set-Item -Path 'HKCU:\Software\Classes\.md' -Value $programId }
$capabilities = 'HKCU:\Software\MarkItDownES\Capabilities'
New-Item -Path "$capabilities\FileAssociations" -Force | Out-Null
New-ItemProperty -Path $capabilities -Name ApplicationName -Value 'MarkItDown ES' -Force | Out-Null
New-ItemProperty -Path $capabilities -Name ApplicationDescription -Value 'Leer y buscar documentos Markdown' -Force | Out-Null
New-ItemProperty -Path "$capabilities\FileAssociations" -Name '.md' -Value $programId -Force | Out-Null
New-Item -Path 'HKCU:\Software\RegisteredApplications' -Force | Out-Null
New-ItemProperty -Path 'HKCU:\Software\RegisteredApplications' -Name 'MarkItDown ES' -Value 'Software\MarkItDownES\Capabilities' -Force | Out-Null
$desktop = [Environment]::GetFolderPath('Desktop')
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path $desktop 'MarkItDown ES.lnk'))
$shortcut.TargetPath = $executable
$shortcut.WorkingDirectory = $destination
$shortcut.Save()
Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class MarkItDownShell { [DllImport("shell32.dll")] public static extern void SHChangeNotify(int e, uint f, IntPtr a, IntPtr b); }'
[MarkItDownShell]::SHChangeNotify(0x08000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)
Write-Host "Visor instalado en $destination"
if ($currentChoice -and $currentChoice -ne $programId) {
    Write-Host 'Hay otra aplicación predeterminada. En un archivo .md, usa Abrir con > Elegir otra aplicación > MarkItDown ES > Siempre.'
}
Write-Host 'Para la vista previa, instala PowerToys y activa únicamente Markdown en Complementos del Explorador. Ver docs/EXPLORADOR.md.'
