param()

if ($env:SKIP_SECRET_CHECK -eq '1') {
  Write-Host "[precommit] Secret check skipped via SKIP_SECRET_CHECK=1"
  exit 0
}

# Get staged files
$staged = git diff --cached --name-only --diff-filter=ACM
if (-not $staged) { exit 0 }

$pattern = '(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*["\']?[A-Za-z0-9_\-]{12,}'
$hasHits = $false

foreach ($f in $staged) {
  if (-not (Test-Path $f)) { continue }
  if ($f -like 'tests/*') { continue }
  if ($f -like '.git/*') { continue }
  try {
    $i = 0
    Get-Content -LiteralPath $f -Encoding UTF8 | ForEach-Object {
      $i++
      if ($_ -match $pattern) {
        Write-Host "[precommit] Potential secret in $f:$i => $_" -ForegroundColor Red
        $hasHits = $true
      }
    }
  } catch {
    # ignore unreadable files
  }
}

if ($hasHits) {
  Write-Host "[precommit] Secret scan failed. To bypass, set SKIP_SECRET_CHECK=1 for this commit." -ForegroundColor Red
  exit 1
}

Write-Host "[precommit] Secret scan passed."
exit 0 