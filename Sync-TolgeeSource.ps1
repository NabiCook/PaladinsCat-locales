<#
.SYNOPSIS
Synchronizes canonical English locale keys to Tolgee.

.DESCRIPTION
Use Explorer's "Run with PowerShell" action for a one-click sync, or run this
script from a terminal. When a PaladinsCat frontend checkout is supplied or
found beside this repository, it copies that catalog into this local locale
checkout before validating and pushing it to Tolgee. Without a frontend
checkout, it uses the canonical English files already in this repository. It
does not create commits or communicate with GitHub.

.EXAMPLE
.\Sync-TolgeeSource.ps1

.EXAMPLE
.\Sync-TolgeeSource.ps1 -CheckOnly

.EXAMPLE
.\Sync-TolgeeSource.ps1 -FrontendDir 'D:\work\PaladinsCat\src\frontend'
#>
[CmdletBinding()]
param(
  [switch]$CheckOnly,
  [switch]$NoPause,
  [string]$FrontendDir = $env:PALADINSCAT_FRONTEND_DIR
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSCommandPath
$siblingFrontend = Join-Path (Split-Path -Parent $repoRoot) 'PaladinsCat\src\frontend'

try {
  $npmCommand = Get-Command npm -ErrorAction Stop
  if ([string]::IsNullOrWhiteSpace($FrontendDir) -and (Test-Path -LiteralPath $siblingFrontend -PathType Container)) {
    $FrontendDir = $siblingFrontend
  }

  if (-not $CheckOnly) {
    if (-not [string]::IsNullOrWhiteSpace($FrontendDir)) {
      if (-not (Test-Path -LiteralPath $FrontendDir -PathType Container)) {
        throw "Frontend directory not found: $FrontendDir"
      }

      Push-Location -LiteralPath $FrontendDir
      try {
        Write-Host '[tolgee-sync] Copying frontend catalog into the local locales checkout...'
        & $npmCommand.Source run sync-community-locales
        if ($LASTEXITCODE -ne 0) {
          throw "Frontend locale synchronization failed with exit code $LASTEXITCODE."
        }
      } finally {
        Pop-Location
      }
    } else {
      Write-Host '[tolgee-sync] No frontend checkout configured; using this repository''s canonical English files.'
    }
  }

  Push-Location -LiteralPath $repoRoot
  try {
    $arguments = @('run', 'tolgee:sync-source', '--')
    if ($CheckOnly) {
      Write-Host '[tolgee-sync] Running read-only Tolgee parity check...'
    } else {
      Write-Host '[tolgee-sync] Synchronizing canonical English keys to Tolgee...'
      $arguments += '--apply', '--allow-local-changes'
    }
    & $npmCommand.Source @arguments
    if ($LASTEXITCODE -ne 0) {
      throw "Tolgee synchronization failed with exit code $LASTEXITCODE."
    }
  } finally {
    Pop-Location
  }
} catch {
  Write-Error $_
  exit 1
} finally {
  if (-not $NoPause) {
    Read-Host 'Press Enter to close'
  }
}
