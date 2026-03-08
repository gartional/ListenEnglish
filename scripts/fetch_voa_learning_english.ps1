param(
  [string]$OutDir = (Join-Path $PSScriptRoot "..\\content\\voa"),
  [int]$MaxItemsPerFeed = 50,
  [int]$DelayMs = 500,
  [switch]$AllowAgencyContent,
  [switch]$RequireTranscript = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$UserAgent = "ListenEnglishContentFetcher/0.1 (+local dev)"

$Feeds = @(
  @{ Name = "Words and Their Stories"; Rss = "http://m.learningenglish.voanews.com/api/zmypyl-vomx-tpeyry_" },
  @{ Name = "Everyday Grammar"; Rss = "http://m.learningenglish.voanews.com/api/zoroqql-vomx-tpeptpqq" },
  @{ Name = "American Stories"; Rss = "http://m.learningenglish.voanews.com/api/zyg__l-vomx-tpetmty" },
  @{ Name = "Science & Technology"; Rss = "http://m.learningenglish.voanews.com/api/zmg_pl-vomx-tpeymtm" }
)

$AudioSeen = @{}

function Ensure-Dir([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}

function HtmlDecode([string]$s) {
  return [System.Net.WebUtility]::HtmlDecode($s)
}

function Get-StableIdFromUrl([string]$url) {
  $m = [regex]::Match($url, "/(?<id>\\d+)\\.html(?:\\?|$)")
  if ($m.Success) { return $m.Groups["id"].Value }

  # Fallback: short SHA-1 prefix of URL
  $sha1 = [System.Security.Cryptography.SHA1]::Create()
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($url)
  $hash = $sha1.ComputeHash($bytes)
  $hex = ($hash | ForEach-Object { $_.ToString("x2") }) -join ""
  return $hex.Substring(0, 12)
}

function Invoke-HttpGet([string]$url) {
  Start-Sleep -Milliseconds $DelayMs
  return Invoke-WebRequest -Uri $url -Headers @{ "User-Agent" = $UserAgent } -UseBasicParsing
}

function Extract-AudioUrl([string]$html) {
  $hq = [regex]::Match($html, 'https://voa-audio\.voanews\.eu/[^"''<>\s]+?_hq\.mp3(?:\?download=1)?', 'IgnoreCase')
  if ($hq.Success) { return $hq.Value }
  $lo = [regex]::Match($html, 'https://voa-audio\.voanews\.eu/[^"''<>\s]+?\.mp3(?:\?download=1)?', 'IgnoreCase')
  if ($lo.Success) { return $lo.Value }
  return $null
}

function Has-AgencyContent([string]$html) {
  $patterns = @(
    "Associated Press",
    "\\bAP Photo\\b",
    "\\bReuters\\b",
    "\\bAFP\\b",
    "Agence France-Press",
    "reported on this story for the Associated Press",
    "via AP"
  )
  foreach ($p in $patterns) {
    if ([regex]::IsMatch($html, $p, "IgnoreCase")) { return $true }
  }
  return $false
}

function Extract-ArticleInnerHtml([string]$html) {
  $m = [regex]::Match($html, '<div\s+id="article-content"[^>]*>(?<inner>[\s\S]*?)<div\s+class="footer-toolbar"', 'IgnoreCase')
  if (-not $m.Success) { return $null }
  return $m.Groups["inner"].Value
}

function Extract-Paragraphs([string]$innerHtml) {
  $paras = New-Object System.Collections.Generic.List[string]
  $matches = [regex]::Matches($innerHtml, '<p[^>]*>(?<p>[\s\S]*?)</p>', 'IgnoreCase')
  foreach ($m in $matches) {
    $p = $m.Groups["p"].Value
    $p = [regex]::Replace($p, '<br\s*/?>', "`n", 'IgnoreCase')
    $p = [regex]::Replace($p, '<[^>]+>', '')
    $p = HtmlDecode($p).Trim()
    if ($p.Length -eq 0) { continue }

    # Filter out player UI/fallback noise that is not part of the transcript/article text
    if ($p -match '^\s*No media source currently available\s*$') { continue }
    if ($p -eq 'Your browser doesn’t support HTML5') { continue }
    if ($p -eq 'Your browser doesn''t support HTML5') { continue }

    $paras.Add($p)
  }
  return $paras
}

Ensure-Dir $OutDir
$itemsDir = Join-Path $OutDir "items"
Ensure-Dir $itemsDir

$allItems = New-Object System.Collections.Generic.List[object]
$skipped = New-Object System.Collections.Generic.List[object]

# Load existing items so index.json always reflects what's on disk.
$existingMetaFiles = Get-ChildItem -LiteralPath $itemsDir -Recurse -Filter "meta.json" -ErrorAction SilentlyContinue
foreach ($f in $existingMetaFiles) {
  try {
    $raw = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction Stop
    if (-not $raw) { continue }
    $m = $raw | ConvertFrom-Json -ErrorAction Stop
    $allItems.Add($m)
    if ($m.audioUrl -and (-not $AudioSeen.ContainsKey([string]$m.audioUrl))) {
      $AudioSeen[[string]$m.audioUrl] = [string]$m.id
    }
  } catch {
    # ignore bad/partial meta files
  }
}

foreach ($feed in $Feeds) {
  Write-Host ""
  Write-Host ("== Feed: {0}" -f $feed.Name)

  $rssXml = [xml](Invoke-HttpGet $feed.Rss).Content
  $rssItems = @($rssXml.rss.channel.item) | Select-Object -First $MaxItemsPerFeed

  foreach ($it in $rssItems) {
    $link = [string]$it.link
    if (-not $link) { continue }

    # VOA sometimes emits "audio clip" pages like /a/8008674.html that typically have audio but no article/transcript.
    if ($link -match '/a/\d+\.html(\?|$)') {
      $skipped.Add([pscustomobject]@{
        id = Get-StableIdFromUrl $link
        url = $link
        title = [string]$it.title
        reason = "audio_clip_page_likely_no_transcript"
        feed = $feed.Name
      })
      continue
    }

    $id = Get-StableIdFromUrl $link
    $itemFolder = Join-Path $itemsDir $id
    $metaPath = Join-Path $itemFolder "meta.json"
    if (Test-Path -LiteralPath $metaPath) {
      continue
    }

    Write-Host ("- Fetching {0}" -f $link)
    try {
      $resp = Invoke-HttpGet $link
      $html = [string]$resp.Content

      $agency = Has-AgencyContent $html
      if ($agency -and (-not $AllowAgencyContent)) {
        $skipped.Add([pscustomobject]@{
          id = $id
          url = $link
          title = [string]$it.title
          reason = "agency_content_detected"
          feed = $feed.Name
        })
        continue
      }

      $inner = Extract-ArticleInnerHtml $html
      $paras = @()
      if ($inner) { $paras = Extract-Paragraphs $inner }

      if ($RequireTranscript -and ($paras.Count -eq 0)) {
        $skipped.Add([pscustomobject]@{
          id = $id
          url = $link
          title = [string]$it.title
          reason = "no_transcript_found"
          feed = $feed.Name
        })
        continue
      }

      $audioUrl = Extract-AudioUrl $html
      if (-not $audioUrl) {
        $skipped.Add([pscustomobject]@{
          id = $id
          url = $link
          title = [string]$it.title
          reason = "no_audio_url_found"
          feed = $feed.Name
        })
        continue
      }

      if ($AudioSeen.ContainsKey($audioUrl)) {
        $skipped.Add([pscustomobject]@{
          id = $id
          url = $link
          title = [string]$it.title
          reason = "duplicate_audio_url"
          feed = $feed.Name
          duplicateOf = $AudioSeen[$audioUrl]
        })
        continue
      }

      Ensure-Dir $itemFolder

      # Save transcript
      $transcriptPath = Join-Path $itemFolder "transcript.txt"
      if ($paras.Count -gt 0) {
        ($paras -join "`r`n`r`n") | Set-Content -LiteralPath $transcriptPath -Encoding UTF8
      } else {
        "" | Set-Content -LiteralPath $transcriptPath -Encoding UTF8
      }

      # Download audio (if present)
      $audioPath = Join-Path $itemFolder "audio.mp3"
      Start-Sleep -Milliseconds $DelayMs
      Invoke-WebRequest -Uri $audioUrl -Headers @{ "User-Agent" = $UserAgent } -OutFile $audioPath -UseBasicParsing
      $audioLocalRel = "items/$id/audio.mp3"
      $AudioSeen[$audioUrl] = $id

      $meta = [pscustomobject]@{
        id = $id
        source = "VOA Learning English"
        feed = $feed.Name
        title = [string]$it.title
        url = $link
        publishedAt = [string]$it.pubDate
        audioUrl = $audioUrl
        audioLocalPath = $audioLocalRel
        transcriptLocalPath = "items/$id/transcript.txt"
        paragraphCount = $paras.Count
        agencyContentDetected = $agency
        attribution = "Credit: learningenglish.voanews.com (public domain Learning English content; exclude AP/Reuters/AFP materials)."
        fetchedAt = (Get-Date).ToString("o")
      }

      ($meta | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $metaPath -Encoding UTF8
      $allItems.Add($meta)
    } catch {
      $skipped.Add([pscustomobject]@{
        id = $id
        url = $link
        title = [string]$it.title
        reason = "error"
        error = ($_.Exception.Message)
        feed = $feed.Name
      })
      continue
    }
  }
}

$index = [pscustomobject]@{
  source = "VOA Learning English"
  generatedAt = (Get-Date).ToString("o")
  outDir = (Resolve-Path $OutDir).Path
  feeds = $Feeds
  items = $allItems
  skipped = $skipped
}

($index | ConvertTo-Json -Depth 10) | Set-Content -LiteralPath (Join-Path $OutDir "index.json") -Encoding UTF8
Write-Host ""
Write-Host ("Done. Items saved to: {0}" -f (Resolve-Path $OutDir).Path)

