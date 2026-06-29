param(
    [string]$Queue = "",
    [string]$LogLevel = "",
    [string]$Pool = "",
    [string]$Hostname = "",
    [int]$Concurrency = 0,
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

if ([string]::IsNullOrWhiteSpace($PythonExe)) {
    if ($env:CONDA_DEFAULT_ENV -eq "ailf_env" -and $env:CONDA_PREFIX -and (Test-Path (Join-Path $env:CONDA_PREFIX "python.exe"))) {
        $PythonExe = Join-Path $env:CONDA_PREFIX "python.exe"
    }
    elseif (Test-Path "$env:USERPROFILE\.conda\envs\ailf_env\python.exe") {
        $PythonExe = "$env:USERPROFILE\.conda\envs\ailf_env\python.exe"
    }
    elseif ($env:CONDA_PREFIX -and (Test-Path (Join-Path $env:CONDA_PREFIX "python.exe"))) {
        $PythonExe = Join-Path $env:CONDA_PREFIX "python.exe"
    }
    else {
        $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
        if ($pythonCmd) {
            $PythonExe = $pythonCmd.Source
        }
    }
}

if ([string]::IsNullOrWhiteSpace($PythonExe) -or -not (Test-Path $PythonExe)) {
    Write-Error "Unable to find a valid python executable. Activate ailf_env or use -PythonExe."
}

if (-not $env:CONDA_DEFAULT_ENV) {
    Write-Warning "No active conda env detected. The script will continue with selected Python executable."
}

if ([string]::IsNullOrWhiteSpace($Queue)) {
    $Queue = if ($env:CELERY_AI_QUEUE) { $env:CELERY_AI_QUEUE } else { "ai_inference" }
}
if ([string]::IsNullOrWhiteSpace($LogLevel)) {
    $LogLevel = if ($env:CELERY_WORKER_LOGLEVEL) { $env:CELERY_WORKER_LOGLEVEL } else { "info" }
}
if ([string]::IsNullOrWhiteSpace($Pool)) {
    $Pool = if ($env:CELERY_WORKER_POOL) { $env:CELERY_WORKER_POOL } else { "solo" }
}
if ($Concurrency -le 0) {
    if ($env:CELERY_WORKER_CONCURRENCY) {
        $Concurrency = [int]$env:CELERY_WORKER_CONCURRENCY
    }
    else {
        $Concurrency = 1
    }
}
if ([string]::IsNullOrWhiteSpace($Hostname)) {
    $Hostname = "inference@$env:COMPUTERNAME"
}

$env:PYTHONIOENCODING = "utf-8"
$pythonPathItems = @($projectRoot, $env:PYTHONPATH) `
    | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } `
    | ForEach-Object { $_.Trim(';') } `
    | Where-Object { $_ -ne "" } `
    | Select-Object -Unique
$env:PYTHONPATH = $pythonPathItems -join ";"

Write-Host "Starting Celery worker..."
Write-Host "Queue=$Queue Pool=$Pool Concurrency=$Concurrency Hostname=$Hostname LogLevel=$LogLevel"
Write-Host "PythonExe=$PythonExe"
Write-Host "PYTHONPATH=$env:PYTHONPATH"

& $PythonExe -m celery -A celery_worker.celery_app:celery_app worker `
    -Q $Queue `
    -n $Hostname `
    -P $Pool `
    --concurrency $Concurrency `
    -l $LogLevel
