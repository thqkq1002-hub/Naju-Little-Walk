param([switch]$Apply)
$ErrorActionPreference='Stop'
$taskRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$intendedFolder=[IO.Path]::GetFullPath((Join-Path $taskRoot 'work'))
$items=Get-Content -LiteralPath (Join-Path $taskRoot 'work/cleanup-v91/archive-audit.json') -Raw -Encoding utf8 | ConvertFrom-Json
$deleted=@();$bytes=0L
foreach($item in $items){
    $target=[IO.Path]::GetFullPath((Join-Path $taskRoot $item.path))
    if([IO.Path]::GetDirectoryName($target) -ne $intendedFolder -or -not $target.EndsWith('.tar.gz')){throw "Invalid archive path: $target"}
    if(-not (Test-Path -LiteralPath $target)){continue}
    if((Get-Item -LiteralPath $target).Attributes -band [IO.FileAttributes]::ReparsePoint){throw "Linked archive refused: $target"}
    if((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256){throw "Archive changed: $target"}
    if($Apply){Remove-Item -LiteralPath $target -Force}
    $deleted+=$item;$bytes+=[long]$item.bytes
}
if($Apply){
    $recordPath=Join-Path $taskRoot 'knowledge/sources/workspace-cleanup-v91.json'
    $report=Get-Content -LiteralPath $recordPath -Raw -Encoding utf8 | ConvertFrom-Json
    $report.deleted=@($report.deleted)+$deleted;$report.bytesDeleted=[long]$report.bytesDeleted+$bytes;$report.completedAtUTC=[DateTime]::UtcNow.ToString('o')
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $recordPath -Encoding utf8
}
@{applied=[bool]$Apply;archivesDeleted=$deleted.Count;bytesDeleted=$bytes}|ConvertTo-Json
