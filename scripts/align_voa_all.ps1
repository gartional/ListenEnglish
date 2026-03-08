param(
  [string]$VoaDir = (Join-Path $PSScriptRoot "..\\content\\voa"),
  [int]$Limit = 3,
  [string]$MambaRoot = (Join-Path (Get-Location) ".mamba")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$itemsDir = Join-Path $VoaDir "items"
if (-not (Test-Path -LiteralPath $itemsDir)) {
  throw "Items directory not found: $itemsDir"
}

$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
$env:MAMBA_ROOT_PREFIX = (Resolve-Path $MambaRoot).Path

$count = 0
Get-ChildItem -LiteralPath $itemsDir -Directory | ForEach-Object {
  if ($Limit -gt 0 -and $count -ge $Limit) { return }
  $dir = $_.FullName
  $audio = Join-Path $dir "audio.mp3"
  $text = Join-Path $dir "transcript.txt"
  if (-not (Test-Path -LiteralPath $audio)) { return }
  if (-not (Test-Path -LiteralPath $text)) { return }
  $vtt = Join-Path $dir "captions.vtt"
  if (Test-Path -LiteralPath $vtt) { return }

  Write-Host ("Aligning: {0}" -f $dir)
  micromamba run -n mfa python (Join-Path $PSScriptRoot "..\\tools\\alignment\\align_voa_item.py") --itemDir $dir
  $count++
}

Write-Host ("Done. Aligned {0} items." -f $count)

