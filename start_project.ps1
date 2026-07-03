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

function Stop-AppPythonProcesses {
    $processes = Get-CimInstance Win32_Process | Where-Object {
        $_.Name -like "python*" -and (
            $_.CommandLine -like "*streamlit*app/Home.py*" -or
            $_.CommandLine -like "*celery*app.jobs.celery_app*"
        )
    }

    foreach ($process in $processes) {
        Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

function Ensure-Postgres {
    $container = docker ps -a --filter "name=^/testai-postgres-15432$" --format "{{.Names}}"
    if (-not $container) {
        Write-Step "Creating Postgres on localhost:15432"
        docker run -d --name testai-postgres-15432 `
            -e POSTGRES_DB=subtitle_studio `
            -e POSTGRES_USER=subtitle_studio `
            -e POSTGRES_PASSWORD=subtitle_studio `
            -p 15432:5432 postgres:16 | Out-Null
    } else {
        Write-Step "Starting Postgres on localhost:15432"
        docker start testai-postgres-15432 | Out-Null
    }

    for ($i = 0; $i -lt 30; $i++) {
        if ((Invoke-NativeQuiet { docker exec testai-postgres-15432 pg_isready -U subtitle_studio -d subtitle_studio }) -eq 0) {
            return
        }
        Start-Sleep -Seconds 2
    }
    throw "Postgres did not become ready."
}

function Ensure-Redis {
    Write-Step "Starting Redis"
    docker compose up -d redis | Out-Null
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

$python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Missing virtualenv Python at $python. Create .venv and install requirements first."
}

Write-Step "Loading .env"
Load-EnvFile (Join-Path $Root ".env")

Write-Step "Preparing PATH"
$ffmpegBin = Find-FfmpegBin
$torchLib = Join-Path $Root ".venv\Lib\site-packages\torch\lib"
$ctranslate2Lib = Join-Path $Root ".venv\Lib\site-packages\ctranslate2"
$env:PATH = "$ffmpegBin;$torchLib;$ctranslate2Lib;$env:PATH"
$env:PYTHONIOENCODING = "utf-8"

Write-Step "Stopping stale app processes"
Stop-AppPythonProcesses
Start-Sleep -Seconds 1

Write-Step "Starting infrastructure"
Start-DockerDesktopIfNeeded
try {
    Invoke-NativeQuiet { docker compose stop postgres } | Out-Null
} catch {
    Write-Step "Compose Postgres stop skipped."
}
Ensure-Postgres
Ensure-Redis

Write-Step "Clearing old logs"
Remove-Item (Join-Path $Root "*.log") -Force -ErrorAction SilentlyContinue

$streamlitOut = Join-Path $Root "streamlit.out.log"
$streamlitErr = Join-Path $Root "streamlit.err.log"
$celeryOut = Join-Path $Root "celery.out.log"
$celeryErr = Join-Path $Root "celery.err.log"

Write-Step "Starting Streamlit"
$streamlit = Start-Process -FilePath $python `
    -ArgumentList @("-m", "streamlit", "run", "app/Home.py", "--server.port", "8501", "--server.address", "localhost") `
    -WorkingDirectory $Root `
    -RedirectStandardOutput $streamlitOut `
    -RedirectStandardError $streamlitErr `
    -WindowStyle Hidden `
    -PassThru

Write-Step "Starting Celery worker"
$celery = Start-Process -FilePath $python `
    -ArgumentList @("-m", "celery", "-A", "app.jobs.celery_app", "worker", "--loglevel=info", "--pool=solo") `
    -WorkingDirectory $Root `
    -RedirectStandardOutput $celeryOut `
    -RedirectStandardError $celeryErr `
    -WindowStyle Hidden `
    -PassThru

Write-Host ""
Write-Host "AI Subtitle Studio is starting."
Write-Host "Streamlit: http://localhost:8501"
Write-Host "Streamlit PID: $($streamlit.Id)"
Write-Host "Celery PID: $($celery.Id)"
Write-Host "Logs: streamlit.*.log, celery.*.log"
