Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Write-Step($Message) {
    Write-Host "[start] $Message"
}

function Load-EnvFile($Path) {
    if (-not (Test-Path $Path)) {
        throw "Missing .env file at $Path"
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

function Wait-DockerReady {
    for ($i = 0; $i -lt 40; $i++) {
        if ((Invoke-NativeQuiet { docker info }) -eq 0) {
            return
        }
        Start-Sleep -Seconds 3
    }
    throw "Docker engine is not ready."
}

function Start-DockerDesktopIfNeeded {
    if ((Invoke-NativeQuiet { docker info }) -eq 0) {
        return
    }

    $dockerDesktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerDesktop) {
        Write-Step "Starting Docker Desktop"
        Start-Process -FilePath $dockerDesktop -WindowStyle Hidden
    }

    Wait-DockerReady
}

function Stop-DevProcesses {
    $allProcesses = @(Get-CimInstance Win32_Process)
    $patterns = @(
        "celery -A app.jobs.celery_app",
        "uvicorn backend.main:app",
        "app.telegram_bot.bot",
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
        Write-Step "Stopping stale PID $processId"
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
}

function Stop-LegacyPostgresContainer {
    $legacy = docker ps --filter "name=^/testai-postgres-15432$" --format "{{.Names}}"
    if ($legacy) {
        Write-Step "Stopping legacy Postgres container testai-postgres-15432"
        Invoke-NativeQuiet { docker stop testai-postgres-15432 } | Out-Null
    }
}

function Wait-PostgresReady {
    for ($i = 0; $i -lt 40; $i++) {
        if ((Invoke-NativeQuiet { docker compose exec -T postgres pg_isready -U subtitle_studio -d subtitle_studio }) -eq 0) {
            return
        }
        Start-Sleep -Seconds 2
    }
    throw "Postgres did not become ready."
}

function Wait-RedisReady {
    for ($i = 0; $i -lt 40; $i++) {
        if ((Invoke-NativeQuiet { docker compose exec -T redis redis-cli ping }) -eq 0) {
            return
        }
        Start-Sleep -Seconds 2
    }
    throw "Redis did not become ready."
}

function Find-FfmpegBin {
    $candidates = @()
    $candidates += ($env:Path -split ";")
    $candidates += "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin"

    foreach ($path in $candidates) {
        if (-not $path) {
            continue
        }
        if (Test-Path (Join-Path $path "ffmpeg.exe")) {
            return $path
        }
    }

    throw "ffmpeg.exe was not found. Install FFmpeg or update PATH."
}

function Wait-HttpReady($Url, $Name) {
    for ($i = 0; $i -lt 40; $i++) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing $Url -TimeoutSec 3
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                return
            }
        } catch {
            Start-Sleep -Seconds 2
        }
    }
    throw "$Name did not become ready at $Url."
}

function Start-LoggedProcess($Name, $FilePath, $ArgumentList, $WorkingDirectory) {
    $stdout = Join-Path $Root "$Name.out.log"
    $stderr = Join-Path $Root "$Name.err.log"

    Write-Step "Starting $Name"
    return Start-Process -FilePath $FilePath `
        -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -WindowStyle Hidden `
        -PassThru
}

$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Missing virtualenv Python at $python. Create .venv and install requirements first."
}

$npm = (Get-Command "npm.cmd" -ErrorAction SilentlyContinue).Source
if (-not $npm) {
    throw "npm.cmd was not found. Install Node.js before starting the React frontend."
}

Write-Step "Loading .env"
Load-EnvFile (Join-Path $Root ".env")

Write-Step "Preparing PATH"
$ffmpegBin = Find-FfmpegBin
$torchLib = Join-Path $Root ".venv\Lib\site-packages\torch\lib"
$ctranslate2Lib = Join-Path $Root ".venv\Lib\site-packages\ctranslate2"
$env:PATH = "$ffmpegBin;$torchLib;$ctranslate2Lib;$env:PATH"
$env:PYTHONIOENCODING = "utf-8"

Write-Step "Stopping stale dev processes"
Stop-DevProcesses
Start-Sleep -Seconds 1

Write-Step "Starting infrastructure"
Start-DockerDesktopIfNeeded
Stop-LegacyPostgresContainer
docker compose up -d | Out-Null
Wait-PostgresReady
Wait-RedisReady

Write-Step "Preparing frontend dependencies"
$frontendDir = Join-Path $Root "frontend"
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    & $npm install --prefix $frontendDir
    if ($LASTEXITCODE -ne 0) {
        throw "npm install failed."
    }
}

Write-Step "Clearing old logs"
Remove-Item (Join-Path $Root "*.log") -Force -ErrorAction SilentlyContinue

$celery = Start-LoggedProcess `
    -Name "celery" `
    -FilePath $python `
    -ArgumentList @("-m", "celery", "-A", "app.jobs.celery_app", "worker", "--loglevel=info", "--pool=solo") `
    -WorkingDirectory $Root

$backend = Start-LoggedProcess `
    -Name "backend" `
    -FilePath $python `
    -ArgumentList @("-m", "uvicorn", "backend.main:app", "--host", "localhost", "--port", "8000", "--reload") `
    -WorkingDirectory $Root

$frontend = Start-LoggedProcess `
    -Name "frontend" `
    -FilePath $npm `
    -ArgumentList @("run", "dev", "--", "--host", "localhost", "--port", "5173") `
    -WorkingDirectory $frontendDir

$telegram = $null
if ($env:TELEGRAM_BOT_TOKEN) {
    $telegram = Start-LoggedProcess `
        -Name "telegram" `
        -FilePath $python `
        -ArgumentList @("-m", "app.telegram_bot.bot") `
        -WorkingDirectory $Root
} else {
    Write-Step "Telegram bot skipped (TELEGRAM_BOT_TOKEN is not set)"
}

Wait-HttpReady "http://localhost:8000/api/health" "FastAPI backend"
Wait-HttpReady "http://localhost:5173" "Vite frontend"

Write-Host ""
Write-Host "AI Subtitle Studio is running."
Write-Host "Frontend: http://localhost:5173"
Write-Host "Backend API: http://localhost:8000/api/health"
Write-Host "Celery PID: $($celery.Id)"
Write-Host "Backend PID: $($backend.Id)"
Write-Host "Frontend PID: $($frontend.Id)"
if ($telegram) {
    Write-Host "Telegram PID: $($telegram.Id)"
}
Write-Host "Logs: backend.*.log, celery.*.log, frontend.*.log, telegram.*.log"
