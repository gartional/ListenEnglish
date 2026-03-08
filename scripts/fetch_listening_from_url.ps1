# Fetch listening page from URL, download audio, transcribe to get 原文.
# Usage: .\fetch_listening_from_url.ps1 -PageUrl "https://..." [-OutputDir "content\mock17"]
param(
    [Parameter(Mandatory=$true)]
    [string]$PageUrl,
    [string]$OutputDir = "content\mock17"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not (Split-Path -IsAbsolute $OutputDir)) {
    $OutputDir = Join-Path $root $OutputDir
}
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

$py = Join-Path $root "tools\fetch_listening_from_url.py"
if (-not (Test-Path $py)) {
    Write-Error "Python script not found: $py"
}
& python $py --url $PageUrl --out-dir $OutputDir
