param(
  [string]$VoaDir = (Join-Path $PSScriptRoot "..\\content\\voa")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$itemsDir = Join-Path $VoaDir "items"
if (-not (Test-Path -LiteralPath $itemsDir)) {
  throw "Items directory not found: $itemsDir"
}

$transcripts = Get-ChildItem -LiteralPath $itemsDir -Recurse -Filter "transcript.txt" -ErrorAction Stop
$changed = 0

foreach ($t in $transcripts) {
  $raw = Get-Content -LiteralPath $t.FullName -Raw -ErrorAction Stop
  if (-not $raw) { continue }

  # Normalize newlines
  $raw = $raw -replace "`r`n", "`n"
  $lines = $raw -split "`n"

  $filtered = New-Object System.Collections.Generic.List[string]
  foreach ($line in $lines) {
    $trim = $line.Trim()
    if ($trim -match '^No media source currently available$') { continue }
    $filtered.Add($line)
  }

  # Drop leading empty lines
  while ($filtered.Count -gt 0 -and $filtered[0].Trim().Length -eq 0) {
    $filtered.RemoveAt(0)
  }

  $out = ($filtered -join "`r`n").TrimEnd() + "`r`n"
  if ($out -ne ((Get-Content -LiteralPath $t.FullName -Raw) )) {
    Set-Content -LiteralPath $t.FullName -Value $out -Encoding UTF8
    $changed++
  }
}

Write-Host ("Cleaned transcripts: {0}" -f $changed)

