Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Write-Step($Message) {
    Write-Host "[stop] $Message"
}

function Load-EnvFile($Path) {
    if (-not (Test-Path $Path)) {
        return
    }

    Get-Content $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or $line -notmatch "=") {
            return
        }

        $name, $value = $line -split "=", 2
        [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), "Process")
    }
}

function Stop-AppPythonProcesses {
    $processes = Get-CimInstance Win32_Process | Where-Object {
        $_.Name -like "python*" -and (
            $_.CommandLine -like "*streamlit*app/Home.py*" -or
            $_.CommandLine -like "*celery*app.jobs.celery_app*"
        )
    }

    foreach ($process in $processes) {
        Write-Step "Stopping PID $($process.ProcessId)"
        Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-NativeQuiet($Command) {
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"

    try {
        & $Command 1>$null 2>$null
        return $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
}

Write-Step "Loading .env"
Load-EnvFile (Join-Path $Root ".env")
$env:PYTHONIOENCODING = "utf-8"

Write-Step "Stopping Streamlit and Celery"
Stop-AppPythonProcesses
Start-Sleep -Seconds 1

$python = Join-Path $Root ".venv\Scripts\python.exe"
if ((Test-Path $python) -and $env:REDIS_URL) {
    Write-Step "Purging Celery queue"
    try {
        & $python -m celery -A app.jobs.celery_app purge -f *> $null
    } catch {
        Write-Step "Celery purge skipped: $($_.Exception.Message)"
    }
}

Write-Step "Stopping Docker containers"
$composeExitCode = Invoke-NativeQuiet { docker compose stop }
if ($composeExitCode -ne 0) {
    Write-Step "docker compose stop exited with code $composeExitCode"
}

docker ps --filter "name=^/testai-postgres-15432$" --format "{{.Names}}" | ForEach-Object {
    if ($_) {
        $postgresExitCode = Invoke-NativeQuiet { docker stop testai-postgres-15432 }
        if ($postgresExitCode -ne 0) {
            Write-Step "docker stop testai-postgres-15432 exited with code $postgresExitCode"
        }
    }
}

Write-Step "Removing log files"
Remove-Item (Join-Path $Root "*.log") -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "AI Subtitle Studio stopped."
Write-Host "App processes stopped, Docker project containers stopped, root *.log files removed."
