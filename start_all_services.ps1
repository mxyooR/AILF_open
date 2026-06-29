param(
    [string]$ProjectRoot = "",
    [string]$RedisDir = "D:/redis"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = $PSScriptRoot
}
$ProjectRoot = (Resolve-Path $ProjectRoot).Path

function Start-InNewPwsh {
    param(
        [Parameter(Mandatory = $true)][string]$Title,
        [Parameter(Mandatory = $true)][string]$Command
    )

    # Use EncodedCommand to avoid quoting issues.
    $titleEscaped = $Title -replace "'", "''"
    $wrapped = "`$Host.UI.RawUI.WindowTitle = '$titleEscaped';`n$Command"
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($wrapped))
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-EncodedCommand", $encoded
    ) | Out-Null
}

function Test-ProcessByCommandLine {
    param(
        [Parameter(Mandatory = $true)][string]$Pattern
    )
    $matched = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue `
        | Where-Object { $_.CommandLine -and $_.CommandLine -match $Pattern } `
        | Select-Object -First 1
    return ($null -ne $matched)
}

function Test-BackendRunning {
    $listener = Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue `
        | Select-Object -First 1
    return ($null -ne $listener)
}

function Test-CeleryRunning {
    return (Test-ProcessByCommandLine -Pattern "-m\s+celery\s+-A\s+celery_worker\.celery_app:celery_app\s+worker")
}

function Get-Utf8Bootstrap {
    return @"
`$utf8NoBom = New-Object System.Text.UTF8Encoding `$false
[Console]::InputEncoding = `$utf8NoBom
[Console]::OutputEncoding = `$utf8NoBom
`$OutputEncoding = `$utf8NoBom
`$env:PYTHONUTF8 = '1'
`$env:PYTHONIOENCODING = 'utf-8'
"@
}

$redisExe = Join-Path $RedisDir "redis-server.exe"
$redisConfCandidates = @(
    (Join-Path -Path $RedisDir -ChildPath "redis.windows.conf")
    (Join-Path -Path $RedisDir -ChildPath "redis.conf")
)
$redisConf = $redisConfCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
$redisConfName = if ($redisConf) { Split-Path -Leaf $redisConf } else { "" }

if (-not (Test-Path $redisExe)) {
    throw "Redis executable not found: $redisExe"
}
if (-not (Test-Path (Join-Path $ProjectRoot "backend\main.py"))) {
    throw "Backend entry not found: $(Join-Path $ProjectRoot 'backend\main.py')"
}
if (-not (Test-Path (Join-Path $ProjectRoot "frontend\package.json"))) {
    throw "Frontend project not found: $(Join-Path $ProjectRoot 'frontend\package.json')"
}
if (-not (Test-Path (Join-Path $ProjectRoot "celery_worker\start_celery_worker.ps1"))) {
    throw "Celery startup script not found: $(Join-Path $ProjectRoot 'celery_worker\start_celery_worker.ps1')"
}
if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    throw "conda command not found. Please install and initialize conda first."
}

$utf8Bootstrap = Get-Utf8Bootstrap

if ($redisConf) {
    $redisCmd = @"
Set-Location '$RedisDir'
& '.\redis-server.exe' '$redisConfName'
"@
}
else {
    $redisCmd = @"
Set-Location '$RedisDir'
& '.\redis-server.exe'
"@
}

$backendCmd = @"
$utf8Bootstrap
Set-Location "$ProjectRoot\backend"
conda run --live-stream -n ailf_env python main.py
"@

$frontendCmd = @"
Set-Location '$ProjectRoot\frontend'
pnpm dev
"@

$celeryCmd = @"
$utf8Bootstrap
Set-Location "$ProjectRoot"
conda run --live-stream -n ailf_env powershell -NoProfile -ExecutionPolicy Bypass -File "$ProjectRoot\celery_worker\start_celery_worker.ps1"
"@

$started = @()

Start-InNewPwsh -Title "AILF-Redis" -Command $redisCmd
$started += "Redis"
Start-Sleep -Seconds 1
if (Test-BackendRunning) {
    Write-Host "Skip Backend: already running."
} else {
    Start-InNewPwsh -Title "AILF-Backend" -Command $backendCmd
    $started += "Backend"
}
Start-Sleep -Seconds 1
Start-InNewPwsh -Title "AILF-Frontend" -Command $frontendCmd
$started += "Frontend"
Start-Sleep -Seconds 1
if (Test-CeleryRunning) {
    Write-Host "Skip Celery: already running."
} else {
    Start-InNewPwsh -Title "AILF-Celery" -Command $celeryCmd
    $started += "Celery"
}

Write-Host ("Started windows: " + ($started -join " / "))
Write-Host "ProjectRoot = $ProjectRoot"
Write-Host "RedisDir    = $RedisDir"
Start-Sleep -Seconds 2
Write-Host ("Backend listening on :5000 = " + (Test-BackendRunning))
Write-Host ("Celery worker process found = " + (Test-CeleryRunning))
