param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$auditPath = Join-Path $taskRoot 'outputs/cleanup-v81/audit.json'
$audit = Get-Content -LiteralPath $auditPath -Raw -Encoding utf8 | ConvertFrom-Json
$archiveRoot = Join-Path $taskRoot 'outputs/cleanup-v81/removed'
function CheckedPath([string]$relative) {
    $candidate = [IO.Path]::GetFullPath((Join-Path $taskRoot $relative))
    if (-not $candidate.StartsWith($taskRoot + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw "Outside workspace: $relative" }
    return $candidate
}
$moved = @(); $deleted = @(); $totalBytes = 0L
foreach ($item in $audit.unusedStarterFiles) {
    $sourcePath = CheckedPath $item.path
    $targetPath = CheckedPath ('outputs/cleanup-v81/removed/' + $item.path)
    if (Test-Path -LiteralPath $sourcePath) {
        if ($Apply) {
            if (Test-Path -LiteralPath $targetPath) { throw "Archive already exists: $targetPath" }
            New-Item -ItemType Directory -Path (Split-Path -Parent $targetPath) -Force | Out-Null
            Move-Item -LiteralPath $sourcePath -Destination $targetPath
        }
        $moved += $item.path; $totalBytes += $item.bytes
    }
}
foreach ($relative in $audit.rebuildableCaches) {
    $cachePath = CheckedPath $relative
    if (Test-Path -LiteralPath $cachePath) {
        $length = if ((Get-Item -LiteralPath $cachePath).PSIsContainer) { (Get-ChildItem -LiteralPath $cachePath -Recurse -File | Measure-Object -Property Length -Sum).Sum } else { (Get-Item -LiteralPath $cachePath).Length }
        if ($Apply) { Remove-Item -LiteralPath $cachePath -Recurse -Force }
        $deleted += $relative; $totalBytes += $length
    }
}
$recordPath = CheckedPath 'knowledge/sources/workspace-cleanup-v81.json'
if ($Apply -and (Test-Path -LiteralPath $recordPath)) {
    $previous = Get-Content -LiteralPath $recordPath -Raw -Encoding utf8 | ConvertFrom-Json
    $moved = @($previous.archivedFiles) + $moved
    $deleted = @($previous.deletedRebuildableCaches) + $deleted | Select-Object -Unique
    $totalBytes += $previous.bytesRemovedFromActiveTree
}
$result = @{ applied=[bool]$Apply; archivedFiles=$moved; deletedRebuildableCaches=$deleted; bytesRemovedFromActiveTree=$totalBytes; recovery='outputs/cleanup-v81/removed (unused code and previous media/models), plus Git history'; preserved=$audit.preserved }
if ($Apply) { $result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (CheckedPath 'knowledge/sources/workspace-cleanup-v81.json') -Encoding utf8 }
$result | ConvertTo-Json -Depth 6
