param(
  [Parameter(Mandatory = $true)][string]$ItemDir,
  [string]$Model = "base.en",
  [string]$ComputeType = "int8"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')

python (Join-Path $PSScriptRoot "..\\tools\\alignment\\align_voa_item_asr.py") --itemDir $ItemDir --model $Model --computeType $ComputeType --cacheAsr

