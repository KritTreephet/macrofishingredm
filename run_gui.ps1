$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptPath = Join-Path $scriptDir "fishing_gui.py"
$requirementsPath = Join-Path $scriptDir "requirements.txt"

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

if (-not $isAdmin) {
    Write-Host "Requesting Administrator permission..."
    Start-Process powershell.exe -Verb RunAs -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", "`"$PSCommandPath`""
    )
    exit
}

$python = Get-Command python -ErrorAction SilentlyContinue
$pythonw = Get-Command pythonw -ErrorAction SilentlyContinue

if (-not $python) {
    $candidateRoots = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312",
        "$env:LOCALAPPDATA\Programs\Python\Python311",
        "$env:LOCALAPPDATA\Programs\Python\Python310"
    )

    foreach ($root in $candidateRoots) {
        $candidate = Join-Path $root "python.exe"
        if (Test-Path $candidate) {
            $python = Get-Item $candidate
            break
        }
    }
}

if (-not $pythonw) {
    $candidateRoots = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312",
        "$env:LOCALAPPDATA\Programs\Python\Python311",
        "$env:LOCALAPPDATA\Programs\Python\Python310"
    )

    foreach ($root in $candidateRoots) {
        $candidate = Join-Path $root "pythonw.exe"
        if (Test-Path $candidate) {
            $pythonw = Get-Item $candidate
            break
        }
    }
}

if (-not $python) {
    Write-Host "[ERROR] Python not found. Please install Python 3.10+ first."
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not $pythonw) {
    $pythonw = $python
}

& $python.Source -m pip install -r $requirementsPath --quiet
Start-Process -FilePath $pythonw.Source -ArgumentList "`"$scriptPath`"" -WorkingDirectory $scriptDir
