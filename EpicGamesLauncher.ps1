$ErrorActionPreference = "Stop"

$RepoOwner = "KritTreephet"
$RepoName = "macrofishingredm"
$Branch = "main"
$RawScriptUrl = "https://raw.githubusercontent.com/$RepoOwner/$RepoName/refs/heads/$Branch/EpicGamesLauncher.ps1"
$ZipUrl = "https://codeload.github.com/$RepoOwner/$RepoName/zip/refs/heads/$Branch"
$InstallDir = Join-Path $env:LOCALAPPDATA "EpicGamesLauncher"

function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal] $identity
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Find-PythonCommand {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return $python.Source
    }

    $candidateRoots = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312",
        "$env:LOCALAPPDATA\Programs\Python\Python311",
        "$env:LOCALAPPDATA\Programs\Python\Python310"
    )

    foreach ($root in $candidateRoots) {
        $candidate = Join-Path $root "python.exe"
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

function Find-PythonwCommand {
    $pythonw = Get-Command pythonw -ErrorAction SilentlyContinue
    if ($pythonw) {
        return $pythonw.Source
    }

    $candidateRoots = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312",
        "$env:LOCALAPPDATA\Programs\Python\Python311",
        "$env:LOCALAPPDATA\Programs\Python\Python310"
    )

    foreach ($root in $candidateRoots) {
        $candidate = Join-Path $root "pythonw.exe"
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

if (-not (Test-IsAdmin)) {
    Write-Host "Requesting Administrator permission..."
    Start-Process powershell.exe -Verb RunAs -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-Command", "iex (irm '$RawScriptUrl')"
    )
    exit
}

Write-Host "Installing EpicGamesLauncher from GitHub..."

$tempRoot = Join-Path $env:TEMP ("EpicGamesLauncher_" + [Guid]::NewGuid().ToString("N"))
$zipPath = Join-Path $tempRoot "source.zip"
$extractDir = Join-Path $tempRoot "source"

New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null

try {
    Invoke-WebRequest -Uri $ZipUrl -OutFile $zipPath -UseBasicParsing
    Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

    $sourceDir = Get-ChildItem -Path $extractDir -Directory | Select-Object -First 1
    if (-not $sourceDir) {
        throw "Downloaded project folder was not found."
    }

    if (Test-Path $InstallDir) {
        Remove-Item -Path $InstallDir -Recurse -Force
    }

    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    Copy-Item -Path (Join-Path $sourceDir.FullName "*") -Destination $InstallDir -Recurse -Force
}
finally {
    if (Test-Path $tempRoot) {
        Remove-Item -Path $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

$python = Find-PythonCommand
if (-not $python) {
    Write-Host ""
    Write-Host "[ERROR] Python 3.10+ was not found."
    Write-Host "Please install Python and tick 'Add python.exe to PATH':"
    Write-Host "https://www.python.org/downloads/"
    Read-Host "Press Enter to exit"
    exit 1
}

$pythonw = Find-PythonwCommand
if (-not $pythonw) {
    $pythonw = $python
}

$requirementsPath = Join-Path $InstallDir "requirements.txt"
$guiPath = Join-Path $InstallDir "fishing_gui.py"

Write-Host "Installing Python packages..."
& $python -m pip install -r $requirementsPath --quiet

Write-Host "Starting GUI..."
Start-Process -FilePath $pythonw -ArgumentList "`"$guiPath`"" -WorkingDirectory $InstallDir
