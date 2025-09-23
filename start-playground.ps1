<#
.SYNOPSIS
  AI Red Teaming Playground - Quick Start (PowerShell)

USAGE
  .\start-playground.ps1

NOTES
  - If you use PowerShell ExecutionPolicy, you may need:
      Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
  - Run from the repo root (where backend/ and frontend/ folders are).
#>

# --- Colored output helpers ---
function Write-Info  { param($m) Write-Host "[INFO]    $m" -ForegroundColor Cyan }
function Write-Success { param($m) Write-Host "[SUCCESS] $m" -ForegroundColor Green }
function Write-Warn  { param($m) Write-Host "[WARNING] $m" -ForegroundColor Yellow }
function Write-ErrorMsg { param($m) Write-Host "[ERROR]   $m" -ForegroundColor Red }

# --- Check Ollama and phi3:mini model ---
function Check-Ollama {
    Write-Info "Checking Ollama status..."
    try {
        $resp = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -ErrorAction Stop
        Write-Success "Ollama is running."
        $respText = $resp | Out-String

        if ($respText -match "phi3:mini") {
            Write-Success "phi3:mini model is available."
        } else {
            Write-Warn "phi3:mini model not found. Pulling model..."
            & ollama pull phi3:mini
            if ($LASTEXITCODE -eq 0) {
                Write-Success "phi3:mini model pulled successfully."
            } else {
                Write-ErrorMsg "Failed to pull phi3:mini model (ollama returned exit code $LASTEXITCODE)."
                throw "ollama pull failed"
            }
        }
    } catch {
        Write-ErrorMsg "Ollama is not running or unreachable. Please start Ollama first:"
        Write-Host "  ollama serve" -ForegroundColor Yellow
        throw $_
    }
}

# --- Start backend ---
function Start-Backend {
    Write-Info "Starting backend server..."
    if (-not (Test-Path -Path "backend")) {
        Write-ErrorMsg "backend directory not found. Aborting."
        throw "missing backend"
    }

    Push-Location "backend"
    try {
        if (Test-Path -Path ".\venv") {
            # Activate the virtual environment for the current session
            $activate = Join-Path -Path (Get-Item -Path ".\venv").FullName -ChildPath "Scripts\Activate.ps1"
            if (Test-Path $activate) {
                . $activate
                Write-Success "Virtual environment activated."
            } else {
                Write-Warn "Activation script not found at $activate. Proceeding without activation."
            }
        } else {
            Write-Warn "Virtual environment not found. Please set it up first."
            Write-Host "Run: python -m venv venv ; .\\venv\\Scripts\\Activate.ps1 ; pip install -r requirements.txt" -ForegroundColor Yellow
            throw "venv missing"
        }

        # Start uvicorn in background (escape quotes properly for Windows)
        $uvicornCmd = "-c", "import uvicorn; uvicorn.run(\"app:app\", host=\"0.0.0.0\", port=8000, reload=True)"
        $backendProc = Start-Process -FilePath "python" -ArgumentList $uvicornCmd -NoNewWindow -PassThru
        $backendProc.Id | Out-File -FilePath "../backend.pid" -Encoding ascii
        Write-Success "Backend server started (PID: $($backendProc.Id))"
    } finally {
        Pop-Location
    }
}

# --- Start frontend ---
function Start-Frontend {
    Write-Info "Starting frontend development server..."
    if (-not (Test-Path -Path "frontend")) {
        Write-ErrorMsg "frontend directory not found. Aborting."
        throw "missing frontend"
    }

    Push-Location "frontend"
    try {
        if (-not (Test-Path -Path "node_modules")) {
            Write-Warn "Dependencies not installed. Installing..."
            & npm.cmd install
            if ($LASTEXITCODE -ne 0) {
                Write-ErrorMsg "npm install failed (exit code $LASTEXITCODE)."
                throw "npm install failed"
            }
        }

        # Use npm.cmd explicitly on Windows
        $frontendProc = Start-Process -FilePath "npm.cmd" -ArgumentList "start" -NoNewWindow -PassThru
        $frontendProc.Id | Out-File -FilePath "../frontend.pid" -Encoding ascii
        Write-Success "Frontend server started (PID: $($frontendProc.Id))"
    } finally {
        Pop-Location
    }
}
