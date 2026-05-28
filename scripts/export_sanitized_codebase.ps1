param(
  [string]$OutputRoot = '',
  [string]$BundleName = '',
  [switch]$Zip
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
  $OutputRoot = Join-Path $repoRoot '_exports'
}
if ([string]::IsNullOrWhiteSpace($BundleName)) {
  $BundleName = 'crm-sanitized-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
}

$stageRoot = Join-Path $OutputRoot $BundleName
$zipPath = Join-Path $OutputRoot ($BundleName + '.zip')

$includeEntries = @(
  'backend',
  'frontend',
  'docs',
  'scripts',
  'public',
  'templates',
  'README.md',
  'SETUP_COLLEAGUE.md',
  'package.json',
  'package-lock.json',
  '.gitignore'
)

$excludedDirectoryNames = @(
  '.git',
  '.claude',
  '.venv',
  '.venvs',
  'venv',
  '.vscode',
  '__pycache__',
  'node_modules',
  'dist',
  'logs',
  'test_portal',
  'storage',
  'tmp_uploads',
  'static',
  '_extracted_preview',
  'sokolov_case_extract',
  'tmp_contract_2710',
  '__tmp_pdf_images',
  '__tmp_pdf_text'
)

$excludedFileNames = @(
  '.env',
  '.env.local',
  '.env.production',
  '.env.development',
  'export_sanitized_codebase.ps1',
  'nul',
  'con',
  'prn',
  'aux',
  'com1',
  'com2',
  'com3',
  'com4',
  'lpt1',
  'lpt2',
  'lpt3'
)

$excludedExtensions = @(
  '.db',
  '.sqlite',
  '.sqlite3',
  '.log',
  '.doc',
  '.docx',
  '.xls',
  '.xlsx',
  '.pdf',
  '.msg',
  '.eml',
  '.tgz',
  '.tar',
  '.gz',
  '.zip',
  '.pfx',
  '.pem',
  '.key',
  '.crt'
)

$excludedWildcardPatterns = @(
  '*.db',
  '*.sqlite',
  '*.sqlite3',
  '*.log',
  '*.doc',
  '*.docx',
  '*.xls',
  '*.xlsx',
  '*.pdf',
  '*.msg',
  '*.eml',
  '*.tgz',
  '*.tar',
  '*.tar.gz',
  '*.zip',
  '*.pfx',
  '*.pem',
  '*.key',
  '*.crt'
)

$textExtensions = @(
  '.py',
  '.ps1',
  '.psm1',
  '.sh',
  '.md',
  '.txt',
  '.json',
  '.js',
  '.jsx',
  '.ts',
  '.tsx',
  '.vue',
  '.css',
  '.scss',
  '.sass',
  '.html',
  '.htm',
  '.xml',
  '.yml',
  '.yaml',
  '.ini',
  '.cfg',
  '.conf',
  '.toml',
  '.sql',
  '.csv',
  '.svg'
)

$replacementRules = @(
  @{ Pattern = 'NBMD tech'; Replacement = 'Nexus' },
  @{ Pattern = 'NBMD system'; Replacement = 'Nexus' },
  @{ Pattern = 'outgoing_normbud\.docx'; Replacement = 'outgoing_nexus_beta.docx' },
  @{ Pattern = 'outgoing_bayer\.docx'; Replacement = 'outgoing_nexus_alpha.docx' },
  @{ Pattern = 'outgoing_morozov\.docx'; Replacement = 'outgoing_nexus_solo.docx' },
  @{ Pattern = 'outgoing_normbud_image'; Replacement = 'outgoing_nexus_beta_image' },
  @{ Pattern = 'outgoing_bayer_image'; Replacement = 'outgoing_nexus_alpha_image' },
  @{ Pattern = 'outgoing_morozov_image'; Replacement = 'outgoing_nexus_solo_image' },
  @{ Pattern = '\u041e\u041e\u041e\s+[\u00ab"]\u041d\u041e\u0420\u041c\u0411\u0423\u0414[\u00bb"]'; Replacement = 'OOO "Nexus Beta"' },
  @{ Pattern = '\u041e\u041e\u041e\s+[\u00ab"]\u0411\u0410\u0419\u0415\u0420[\u00bb"]'; Replacement = 'OOO "Nexus Alpha"' },
  @{ Pattern = '\u0418\u041f\s+\u041c\u043e\u0440\u043e\u0437\u043e\u0432\s+\u041e\.?\s*\u0410\.?'; Replacement = 'IP Nexus Solo' },
  @{ Pattern = '\bnormbud\b'; Replacement = 'nexus_beta' },
  @{ Pattern = '\bbayer\b'; Replacement = 'nexus_alpha' },
  @{ Pattern = '\bmorozov\b'; Replacement = 'nexus_solo' },
  @{ Pattern = '\u041d\u043e\u0440\u043c\u0431\u0443\u0434'; Replacement = 'Nexus Beta' },
  @{ Pattern = '\u041d\u041e\u0420\u041c\u0411\u0423\u0414'; Replacement = 'Nexus Beta' },
  @{ Pattern = '\u043d\u043e\u0440\u043c\u0431\u0443\u0434'; Replacement = 'nexus beta' },
  @{ Pattern = '\u0411\u0430\u0439\u0435\u0440'; Replacement = 'Nexus Alpha' },
  @{ Pattern = '\u0411\u0410\u0419\u0415\u0420'; Replacement = 'Nexus Alpha' },
  @{ Pattern = '\u0431\u0430\u0439\u0435\u0440'; Replacement = 'nexus alpha' },
  @{ Pattern = '\u041c\u043e\u0440\u043e\u0437\u043e\u0432'; Replacement = 'Nexus Solo' },
  @{ Pattern = '\u043c\u043e\u0440\u043e\u0437\u043e\u0432'; Replacement = 'nexus solo' }
)

$verificationPattern = '\u0431\u0430\u0439\u0435\u0440|\u043d\u043e\u0440\u043c\u0431\u0443\u0434|\u043c\u043e\u0440\u043e\u0437\u043e\u0432|bayer|normbud|morozov|NBMD tech|NBMD system'

function Test-ExcludedFile {
  param(
    [System.IO.FileInfo]$File
  )

  if ($excludedFileNames -contains $File.Name) {
    return $true
  }

  if ($File.Name -like '.env*') {
    return $true
  }

  if ($excludedExtensions -contains $File.Extension.ToLowerInvariant()) {
    return $true
  }

  foreach ($pattern in $excludedWildcardPatterns) {
    if ($File.Name -like $pattern) {
      return $true
    }
  }

  return $false
}

function Copy-SafeEntry {
  param(
    [string]$SourcePath,
    [string]$DestinationPath
  )

  if (Test-Path $SourcePath -PathType Container) {
    $sourceDir = Get-Item -LiteralPath $SourcePath
    if ($excludedDirectoryNames -contains $sourceDir.Name) {
      return
    }

    New-Item -ItemType Directory -Path $DestinationPath -Force | Out-Null
    Get-ChildItem -LiteralPath $SourcePath -Force | ForEach-Object {
      $childDestination = Join-Path $DestinationPath $_.Name
      if ($_.PSIsContainer) {
        if ($excludedDirectoryNames -contains $_.Name) {
          return
        }
        Copy-SafeEntry -SourcePath $_.FullName -DestinationPath $childDestination
      } else {
        if (Test-ExcludedFile -File $_) {
          return
        }
        New-Item -ItemType Directory -Path (Split-Path -Parent $childDestination) -Force | Out-Null
        Copy-Item -LiteralPath $_.FullName -Destination $childDestination -Force
      }
    }
    return
  }

  $sourceFile = Get-Item -LiteralPath $SourcePath
  if (Test-ExcludedFile -File $sourceFile) {
    return
  }
  New-Item -ItemType Directory -Path (Split-Path -Parent $DestinationPath) -Force | Out-Null
  Copy-Item -LiteralPath $SourcePath -Destination $DestinationPath -Force
}

function Sanitize-TextFiles {
  param(
    [string]$RootPath
  )

  $editedFiles = 0
  $replacementCount = 0

  Get-ChildItem -LiteralPath $RootPath -Recurse -File | Where-Object {
    $textExtensions -contains $_.Extension.ToLowerInvariant() -or $_.Name -in @('.gitignore', '.env.example')
  } | ForEach-Object {
    $path = $_.FullName
    $content = Get-Content -LiteralPath $path -Raw -Encoding UTF8
    $updated = $content
    $fileChanged = $false

    foreach ($rule in $replacementRules) {
      $regex = [regex]::new($rule.Pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
      $matches = $regex.Matches($updated)
      if ($matches.Count -gt 0) {
        $replacementCount += $matches.Count
        $updated = $regex.Replace($updated, $rule.Replacement)
        $fileChanged = $true
      }
    }

    if ($fileChanged -and $updated -ne $content) {
      Set-Content -LiteralPath $path -Value $updated -Encoding UTF8
      $editedFiles += 1
    }
  }

  return [pscustomobject]@{
    EditedFiles = $editedFiles
    Replacements = $replacementCount
  }
}

function Write-ExportReadme {
  param(
    [string]$RootPath
  )

  $content = @"
This bundle was generated by scripts/export_sanitized_codebase.ps1.

What was removed:
- local and test databases
- real environment files
- logs, node_modules, dist, virtualenvs
- local storage, uploads, test portal runtime data
- office documents, PDFs and mail exports that may contain real data or branded templates

What was sanitized:
- historical company and brand identifiers replaced with neutral aliases
- branded template and preview file references renamed to neutral aliases

Before sharing externally, do one more manual check of:
- generated binary office/PDF files, if you decide to add them separately
- ad-hoc SQL/Excel extracts outside the exported folders
"@

  Set-Content -LiteralPath (Join-Path $RootPath 'SANITIZED_EXPORT_README.txt') -Value $content -Encoding UTF8
}

if (Test-Path -LiteralPath $stageRoot) {
  Remove-Item -LiteralPath $stageRoot -Recurse -Force
}
if (Test-Path -LiteralPath $zipPath) {
  Remove-Item -LiteralPath $zipPath -Force
}

New-Item -ItemType Directory -Path $stageRoot -Force | Out-Null

foreach ($entry in $includeEntries) {
  $sourcePath = Join-Path $repoRoot $entry
  if (-not (Test-Path -LiteralPath $sourcePath)) {
    continue
  }
  $destinationPath = Join-Path $stageRoot $entry
  Copy-SafeEntry -SourcePath $sourcePath -DestinationPath $destinationPath
}

$stats = Sanitize-TextFiles -RootPath $stageRoot
Write-ExportReadme -RootPath $stageRoot

$residualMatches = Get-ChildItem -LiteralPath $stageRoot -Recurse -File | Where-Object {
  $textExtensions -contains $_.Extension.ToLowerInvariant() -or $_.Name -in @('.gitignore', '.env.example')
} | Select-String -Pattern $verificationPattern -CaseSensitive:$false

$residualNameMatches = Get-ChildItem -LiteralPath $stageRoot -Recurse -Force | Where-Object {
  $_.Name -match $verificationPattern
}

if ($Zip) {
  Compress-Archive -Path (Join-Path $stageRoot '*') -DestinationPath $zipPath -Force
}

Write-Host "Sanitized export created: $stageRoot"
if ($Zip) {
  Write-Host "Zip archive created: $zipPath"
}
Write-Host "Edited files: $($stats.EditedFiles)"
Write-Host "Total replacements: $($stats.Replacements)"
Write-Host "Residual matches in text files: $(@($residualMatches).Count)"
Write-Host "Residual matches in file or directory names: $(@($residualNameMatches).Count)"

if (@($residualMatches).Count -gt 0) {
  Write-Host "Files requiring manual review:"
  $residualMatches | Select-Object Path, LineNumber, Line | Format-Table -AutoSize
}

if (@($residualNameMatches).Count -gt 0) {
  Write-Host "Paths requiring manual review:"
  $residualNameMatches | Select-Object FullName | Format-Table -AutoSize
}
