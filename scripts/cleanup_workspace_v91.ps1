param([switch]$Apply)
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$audit = Get-Content -LiteralPath (Join-Path $taskRoot 'work/cleanup-v91/audit.json') -Raw -Encoding utf8 | ConvertFrom-Json
function CheckedPath([string]$relative) {
    $target = [IO.Path]::GetFullPath((Join-Path $taskRoot $relative))
    if (-not $target.StartsWith($taskRoot + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw "Outside workspace: $relative" }
    if (Test-Path -LiteralPath $target) {
        $item = Get-Item -LiteralPath $target -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Linked path refused: $relative" }
        if ($item.PSIsContainer -and (Get-ChildItem -LiteralPath $target -Force -Recurse | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })) { throw "Linked descendant refused: $relative" }
    }
    return $target
}
$deleted = @(); $bytes = 0L
foreach ($copy in $audit.duplicateStagedModels) {
    $target = CheckedPath $copy.path; $retained = CheckedPath $copy.retained
    if (-not (Test-Path -LiteralPath $target)) { continue }
    if (-not (Test-Path -LiteralPath $retained)) { throw "Missing retained original: $retained" }
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $copy.sha256 -or (Get-FileHash -LiteralPath $retained -Algorithm SHA256).Hash.ToLowerInvariant() -ne $copy.sha256) { throw "Changed model copy: $target" }
    if ($Apply) { Remove-Item -LiteralPath $target -Force }
    $deleted += $copy; $bytes += [long]$copy.bytes
}
foreach ($cache in $audit.rebuildableCaches) {
    $target = CheckedPath $cache.path
    if (-not (Test-Path -LiteralPath $target)) { continue }
    if ($Apply) { Remove-Item -LiteralPath $target -Recurse -Force }
    $deleted += $cache; $bytes += [long]$cache.bytes
}
$report = @{ revision='workspace-cleanup-v91'; applied=[bool]$Apply; completedAtUTC=[DateTime]::UtcNow.ToString('o'); deleted=$deleted; bytesDeleted=$bytes; preserved=$audit.preserved; unusedRuntimeCode=$audit.unusedRuntimeCode }
if ($Apply) {
    $recordPath = CheckedPath 'knowledge/sources/workspace-cleanup-v91.json'
    if (Test-Path -LiteralPath $recordPath) {
        $previous = Get-Content -LiteralPath $recordPath -Raw -Encoding utf8 | ConvertFrom-Json
        $report.deleted = @($previous.deleted) + $deleted
        $report.bytesDeleted = [long]$previous.bytesDeleted + $bytes
    }
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $recordPath -Encoding utf8
}
@{ applied=[bool]$Apply; removedGroups=$deleted.Count; bytesDeleted=$bytes } | ConvertTo-Json
