param(
    [ValidateSet("setup", "install", "migrate", "seed", "run", "test", "lint", "format", "superuser")]
    [string]$Task = "setup",
    [string]$AdminEmail = "admin@example.com",
    [string]$AdminPassword = "admin123",
    [switch]$UpdateAdminPassword,
    [switch]$ResetOperations
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

$venvPython = Join-Path $repoRoot "venv\Scripts\python.exe"

function Ensure-Venv {
    if (-not (Test-Path $venvPython)) {
        Write-Host "[setup] Creating virtual environment..."
        py -m venv venv
    }
}

function Ensure-EnvFile {
    if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
        Write-Host "[setup] Creating .env from .env.example..."
        Copy-Item ".env.example" ".env"
    }
}

function Invoke-VenvPython {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    if (-not (Test-Path $venvPython)) {
        throw "Virtual environment not found at venv\\Scripts\\python.exe. Run: .\\scripts\\dev.ps1 -Task install"
    }

    & $venvPython @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: python $($Args -join ' ')"
    }
}

function Install-Dependencies {
    Ensure-Venv
    Ensure-EnvFile
    Write-Host "[install] Upgrading pip..."
    Invoke-VenvPython -Args @("-m", "pip", "install", "--upgrade", "pip")

    Write-Host "[install] Installing requirements..."
    Invoke-VenvPython -Args @("-m", "pip", "install", "-r", "requirements.txt")
}

function Run-Migrations {
    Write-Host "[migrate] Generating migrations..."
    Invoke-VenvPython -Args @("manage.py", "makemigrations")

    Write-Host "[migrate] Applying migrations..."
    Invoke-VenvPython -Args @("manage.py", "migrate")
}

function Run-Seed {
    $seedArgs = @("manage.py", "seed_data", "--admin-email", $AdminEmail, "--admin-password", $AdminPassword)

    if ($UpdateAdminPassword) {
        $seedArgs += "--update-admin-password"
    }

    if ($ResetOperations) {
        $seedArgs += "--reset-operations"
    }

    Write-Host "[seed] Running seed_data..."
    Invoke-VenvPython -Args $seedArgs
}

switch ($Task) {
    "setup" {
        Install-Dependencies
        Run-Migrations
        Run-Seed
        Write-Host "[done] Setup complete. Start the app with: .\\scripts\\dev.ps1 -Task run"
    }
    "install" {
        Install-Dependencies
        Write-Host "[done] Install complete."
    }
    "migrate" {
        Run-Migrations
        Write-Host "[done] Migrations complete."
    }
    "seed" {
        Run-Seed
        Write-Host "[done] Seed complete."
    }
    "run" {
        Write-Host "[run] Starting development server at http://127.0.0.1:8000/"
        Invoke-VenvPython -Args @("manage.py", "runserver")
    }
    "test" {
        Write-Host "[test] Running Django tests..."
        Invoke-VenvPython -Args @("manage.py", "test")
    }
    "lint" {
        Write-Host "[lint] Running ruff check..."
        Invoke-VenvPython -Args @("-m", "ruff", "check", ".")
    }
    "format" {
        Write-Host "[format] Running ruff format..."
        Invoke-VenvPython -Args @("-m", "ruff", "format", ".")
    }
    "superuser" {
        Write-Host "[superuser] Creating Django superuser..."
        Invoke-VenvPython -Args @("manage.py", "createsuperuser")
    }
}
