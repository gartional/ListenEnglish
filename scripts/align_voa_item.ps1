param(
  [Parameter(Mandatory = $true)][string]$ItemDir,
  [string]$MambaRoot = (Join-Path (Get-Location) ".mamba")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Refresh PATH so winget-installed ffmpeg/micromamba are visible in this shell.
$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')

$env:MAMBA_ROOT_PREFIX = (Resolve-Path $MambaRoot).Path

micromamba run -n mfa python (Join-Path $PSScriptRoot "..\\tools\\alignment\\align_voa_item.py") --itemDir $ItemDir

