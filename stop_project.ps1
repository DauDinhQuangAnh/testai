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

function Stop-DevProcesses {
    $allProcesses = @(Get-CimInstance Win32_Process)
    $patterns = @(
        "celery -A app.jobs.celery_app",
        "uvicorn backend.main:app",
        "streamlit run app/Home.py",
        "frontend\\node_modules",
        "frontend/node_modules",
        "frontend\\node_modules\\vite",
        "frontend/node_modules/vite",
        "npm-cli.js run dev",
        "vite --host localhost --port 5173"
    )

    $targetIds = @{}
    $targets = $allProcesses | Where-Object {
        $commandLine = $_.CommandLine
        if (-not $commandLine) {
            return $false
        }
        if ($_.Name -like "python*" -and $commandLine -like "*multiprocessing.spawn*spawn_main*") {
            return $true
        }
        if (
            $commandLine -like "*$Root*" -and
            $_.Name -in @("python.exe", "pythonw.exe", "python3.12.exe", "node.exe", "cmd.exe", "esbuild.exe")
        ) {
            return $true
        }
        foreach ($pattern in $patterns) {
            if ($commandLine -like "*$pattern*") {
                return $true
            }
        }
        return $false
    }

    foreach ($process in $targets) {
        $targetIds[$process.ProcessId] = $true
    }

    do {
        $changed = $false
        foreach ($process in $allProcesses) {
            if ($targetIds.ContainsKey($process.ParentProcessId) -and -not $targetIds.ContainsKey($process.ProcessId)) {
                $targetIds[$process.ProcessId] = $true
                $changed = $true
            }
        }
    } while ($changed)

    foreach ($processId in $targetIds.Keys) {
        Write-Step "Stopping PID $processId"
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
}

Write-Step "Loading .env"
Load-EnvFile (Join-Path $Root ".env")
$env:PYTHONIOENCODING = "utf-8"

Write-Step "Stopping app processes"
Stop-DevProcesses
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

Write-Step "Stopping Docker Compose services"
$composeExitCode = Invoke-NativeQuiet { docker compose stop }
if ($composeExitCode -ne 0) {
    Write-Step "docker compose stop exited with code $composeExitCode"
}

$legacy = docker ps --filter "name=^/testai-postgres-15432$" --format "{{.Names}}"
if ($legacy) {
    Write-Step "Stopping legacy Postgres container testai-postgres-15432"
    $legacyExitCode = Invoke-NativeQuiet { docker stop testai-postgres-15432 }
    if ($legacyExitCode -ne 0) {
        Write-Step "docker stop testai-postgres-15432 exited with code $legacyExitCode"
    }
}

Write-Step "Removing log files"
Remove-Item (Join-Path $Root "*.log") -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "AI Subtitle Studio stopped."
Write-Host "App processes stopped, Docker Compose services stopped, root *.log files removed."
