$repoPath = (Resolve-Path ".").Path
$cmdPath = Join-Path $repoPath "launch.cmd"

if (-not (Test-Path $cmdPath)) {
    Write-Error "launch.cmd not found at $cmdPath"
    exit 1
}

if (-not (Test-Path $PROFILE)) {
    New-Item -ItemType File -Path $PROFILE -Force | Out-Null
}

$aliasBlock = @"
function launch {
    & "$cmdPath" @args
}
"@

$profileContent = Get-Content $PROFILE -Raw
if ($profileContent -match "function launch\s*\{") {
    Write-Host "A launch function already exists in $PROFILE"
    Write-Host "No changes made."
    exit 0
}

Add-Content -Path $PROFILE -Value "`r`n$aliasBlock`r`n"
Write-Host "Added launch function to $PROFILE"
Write-Host "Restart PowerShell, then run: launch --mode test"
