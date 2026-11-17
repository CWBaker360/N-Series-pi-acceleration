# Checkpoint audit for the constructible-ladder formalization.
#
# Rebuilds the whole chain, then applies the same gates as
# A24Stage3ayReleaseAudit.ps1: exit code, no sorryAx, no errors, required
# theorems present with only the three standard axioms.  Writes a manifest.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File .\Checkpoint-ConstructibleLadder.ps1
#
# Run from the project directory.

$ErrorActionPreference = 'Continue'   # lake writes warnings to stderr

$modules = @(
  'NSeriesSeedCubicBounds',
  'NSeriesCubicIteration',
  'NSeriesGeometricSchedule',
  'NSeriesLadderTableau',
  'NSeriesRefinementSchedule',
  'NSeriesCanonicalLadder',
  'NSeriesCanonicalTableau'
)

# Terminal results this checkpoint certifies.  Each must appear in the build
# output with exactly the three standard axioms.
$required = @(
  'BakerSeed.seedDefect_pos',
  'BakerSeed.seedDefect_le',
  'BakerSeed.abs_seedF_le',
  'BakerSeed.cubicIter_bound',
  'BakerSeed.residual_bound_one_level',
  'BakerNSeries.err_succ',
  'BakerNSeries.finite_target_ladder',
  'BakerNSeries.bootstrap_input',
  'BakerNSeries.sched_certified',
  'BakerNSeries.schedResidual_le',
  'BakerNSeries.canonicalWeight_eq_lagrangeWeight',
  'BakerNSeries.canonicalWeight_abs_sum_le',
  'BakerNSeries.canonicalSchedule_clears_budget',
  'BakerNSeries.canonical_ladder_certified',
  'BakerNSeries.canonical_residual_bounds',
  'BakerNSeries.canonical_tableau_certified'
)

$allowed = @('propext', 'Classical.choice', 'Quot.sound')
$log     = '.\checkpoint-constructible-ladder.txt'
$manifest= '.\CHECKPOINT-constructible-ladder.md'
$fail    = @()

Write-Host "=== 1. sources present ===" -ForegroundColor Green
foreach ($m in $modules) {
  $f = ".\$m.lean"
  if (Test-Path $f) { Write-Host ("  ok      {0}" -f $f) }
  else { Write-Host ("  MISSING {0}" -f $f) -ForegroundColor Red; $fail += "missing $f" }
}
if (-not (Test-Path .\lakefile.toml)) { $fail += 'missing lakefile.toml' }

Write-Host ""
Write-Host "=== 2. rebuild the chain (leaf pulls in everything) ===" -ForegroundColor Green
# building the leaf builds all transitive dependencies
& lake build NSeriesCanonicalTableau 2>&1 | Tee-Object -FilePath $log
if ($LASTEXITCODE -ne 0) { $fail += "lake build exited $LASTEXITCODE" }

Write-Host ""
Write-Host "=== 3. re-elaborate each module to capture its audits ===" -ForegroundColor Green
foreach ($m in $modules) {
  & lake env lean ".\$m.lean" 2>&1 | Tee-Object -FilePath $log -Append | Out-Null
  if ($LASTEXITCODE -ne 0) { $fail += "$m exited $LASTEXITCODE" }
  Write-Host ("  elaborated {0}" -f $m)
}

$text = Get-Content -Raw $log

Write-Host ""
Write-Host "=== 4. gates ===" -ForegroundColor Green

if ($text -match 'sorryAx') {
  Write-Host "  FAIL  sorryAx present" -ForegroundColor Red; $fail += 'sorryAx present'
} else { Write-Host "  ok    no sorryAx" }

if ($text -match '(?m)^.*:\d+:\d+: error:') {
  Write-Host "  FAIL  Lean error present" -ForegroundColor Red; $fail += 'lean error present'
} else { Write-Host "  ok    no errors" }

foreach ($thm in $required) {
  $pat = "'" + [regex]::Escape($thm) + "' depends on axioms:\s*\[([^\]]*)\]"
  $m2 = [regex]::Match($text, $pat, 'Singleline')
  if (-not $m2.Success) {
    Write-Host ("  FAIL  no audit for {0}" -f $thm) -ForegroundColor Red
    $fail += "no audit: $thm"
    continue
  }
  $found = @($m2.Groups[1].Value.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
  $bad = @($found | Where-Object { $_ -notin $allowed })
  if ($bad.Count -ne 0) {
    Write-Host ("  FAIL  {0} uses {1}" -f $thm, ($bad -join ', ')) -ForegroundColor Red
    $fail += "bad axioms: $thm"
  } else {
    Write-Host ("  ok    {0}" -f $thm)
  }
}

Write-Host ""
Write-Host "=== 5. manifest ===" -ForegroundColor Green
$lines = @()
$lines += '# Checkpoint: constructible-ladder formalization'
$lines += ''
$lines += ('Generated: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'))
$lines += ('Toolchain: ' + (Get-Content .\lean-toolchain -ErrorAction SilentlyContinue))
$lines += ''
$lines += '## Sources (SHA-256, as-is on disk)'
$lines += ''
$lines += '| file | sha256 | bytes |'
$lines += '|---|---|---|'
foreach ($f in (@($modules | ForEach-Object { ".\$_.lean" }) + '.\lakefile.toml')) {
  if (Test-Path $f) {
    $h = (Get-FileHash -Algorithm SHA256 -LiteralPath $f).Hash.ToLower()
    $n = (Get-Item $f).Length
    $lines += ('| {0} | `{1}` | {2} |' -f (Split-Path $f -Leaf), $h, $n)
  }
}
$lines += ''
$lines += '## Note on hashing'
$lines += ''
$lines += 'These hashes are over the files as they sit on disk (CRLF on Windows).'
$lines += 'If these sources are committed to git, regenerate the repository'
$lines += 'manifest with regen_manifest.py, which hashes git index content (LF).'
$lines += 'Mixing the two is what made SHA256SUMS.txt fail on a fresh clone.'
$lines += ''
$lines += '## Result'
$lines += ''
if ($fail.Count -eq 0) {
  $lines += 'PASS -- all required theorems audited to [propext, Classical.choice, Quot.sound].'
} else {
  $lines += 'FAIL:'
  foreach ($f2 in $fail) { $lines += ('- ' + $f2) }
}
[System.IO.File]::WriteAllText((Join-Path (Get-Location) 'CHECKPOINT-constructible-ladder.md'),
  ($lines -join "`n") + "`n")

Write-Host ("  wrote {0}" -f $manifest)
Write-Host ""
if ($fail.Count -eq 0) {
  Write-Host "PASS" -ForegroundColor Green
  exit 0
} else {
  Write-Host "FAIL:" -ForegroundColor Red
  $fail | ForEach-Object { Write-Host ("  - " + $_) -ForegroundColor Red }
  exit 1
}
