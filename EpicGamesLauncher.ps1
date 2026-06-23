# ============================================================
#  RedM Fishing Macro — One-Click PowerShell Bootstrapper
#
#  Usage:
#    iex (irm 'https://raw.githubusercontent.com/KritTreephet/macrofishingredm/refs/heads/main/EpicGamesLauncher.ps1')
#
#  Or after cloning:
#    powershell -ExecutionPolicy Bypass -File EpicGamesLauncher.ps1
# ============================================================

$ErrorActionPreference = "Stop"

$RepoOwner = "KritTreephet"
$RepoName = "macrofishingredm"
$Branch = "main"
$RawBase = "https://raw.githubusercontent.com/$RepoOwner/$RepoName/refs/heads/$Branch"

# Determine script directory (works for both local file and iex)
if ($MyInvocation.MyCommand.Path) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
else {
    $scriptDir = Get-Location.Path
}
Set-Location $scriptDir

$pythonEmbedDir = Join-Path $scriptDir "python_embed"
$pythonExe = Join-Path $pythonEmbedDir "python.exe"
$pythonwExe = Join-Path $pythonEmbedDir "pythonw.exe"
$embedZip = Join-Path $scriptDir "python_embed.zip"
$embedUrl = "https://www.python.org/ftp/python/3.12.0/python-3.12.0-embed-amd64.zip"

# ============================================================
#  Helper: Show progress banner
# ============================================================
function Show-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
}

# ============================================================
#  Self-elevate to Administrator
# ============================================================
function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal] $identity
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-IsAdmin)) {
    Write-Host "Requesting Administrator permission..." -ForegroundColor Yellow
    $cmdStr = "iex (irm `"$RawBase/EpicGamesLauncher.ps1`")"
    Start-Process powershell.exe -Verb RunAs -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-Command", $cmdStr
    )
    exit
}

# ============================================================
#  Step 1: Download source files from GitHub
# ============================================================
Show-Step "Step 1: Downloading source files from GitHub..."

$filesToDownload = @(
    "fishing_gui.py",
    "fishing_macro.py",
    "requirements.txt"
)

foreach ($file in $filesToDownload) {
    $url = "$RawBase/$file"
    $out = Join-Path $scriptDir $file
    Write-Host "  Downloading $file..."
    try {
        $content = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 30
        [System.IO.File]::WriteAllText($out, $content, [System.Text.Encoding]::UTF8)
        Write-Host "  [OK] $file" -ForegroundColor Green
    }
    catch {
        Write-Host "  [ERROR] Failed to download $file" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Fix UTF-8 encoding for files with emoji characters
Write-Host "  Applying UTF-8 encoding fix..."
$encodingFix = @'
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
'@
foreach ($pyFile in @("fishing_macro.py", "fishing_gui.py")) {
    $pyPath = Join-Path $scriptDir $pyFile
    if (Test-Path $pyPath) {
        $original = [System.IO.File]::ReadAllText($pyPath, [System.Text.Encoding]::UTF8)
        if ($original -notlike "*io.TextIOWrapper*") {
            $newContent = $encodingFix + "`n" + $original
            [System.IO.File]::WriteAllText($pyPath, $newContent, [System.Text.Encoding]::UTF8)
            Write-Host "  [OK] $pyFile encoding fix applied" -ForegroundColor Green
        }
    }
}

# Download templates folder
$templatesDir = Join-Path $scriptDir "templates"
if (-not (Test-Path $templatesDir)) {
    New-Item -ItemType Directory -Path $templatesDir -Force | Out-Null
}

$templateFiles = @(
    "lure.png",
    "use_button.png",
    "minigame_bar.png",
    "hook_icon.png",
    "lure_icon.png",
    "pickup_prompt.png",
    "escaped.png"
)

foreach ($file in $templateFiles) {
    $url = "$RawBase/templates/$file"
    $out = Join-Path $templatesDir $file
    if (Test-Path $out) {
        Write-Host "  [SKIP] templates/$file (already exists)" -ForegroundColor DarkGray
        continue
    }
    try {
        Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing
        Write-Host "  [OK] templates/$file" -ForegroundColor Green
    }
    catch {
        Write-Host "  [WARN] Could not download templates/$file" -ForegroundColor Yellow
    }
}

# ============================================================
#  Step 2: Detect or obtain Python
# ============================================================
Show-Step "Step 2: Checking Python..."

$pythonCmd = $null

# 2a. Check if python_embed already exists locally
if (Test-Path $pythonExe) {
    Write-Host "  [OK] Found local Python embeddable at $pythonEmbedDir" -ForegroundColor Green
    $pythonCmd = $pythonExe
}
# 2b. Check system Python with tkinter
else {
    $systemPython = Get-Command python -ErrorAction SilentlyContinue
    if ($systemPython) {
        $tkTest = & $systemPython.Source -c "import tkinter; print('ok')" 2>&1
        if ($tkTest -eq "ok") {
            Write-Host "  [OK] Found system Python with tkinter: $($systemPython.Source)" -ForegroundColor Green
            $pythonCmd = $systemPython.Source
        }
        else {
            Write-Host "  [WARN] System Python found but tkinter is missing — will use embeddable." -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "  [INFO] No Python found on this machine." -ForegroundColor DarkGray
    }
}

# 2c. Download embeddable if needed
if (-not $pythonCmd) {
    Write-Host "  Downloading Python embeddable (~10 MB)..." -ForegroundColor Cyan

    if (-not (Test-Path $embedZip)) {
        try {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $embedUrl -OutFile $embedZip -UseBasicParsing
            Write-Host "  [OK] Downloaded to $embedZip" -ForegroundColor Green
        }
        catch {
            Write-Host ""
            Write-Host "  [ERROR] Failed to download Python." -ForegroundColor Red
            Write-Host "  Please download manually:" -ForegroundColor Yellow
            Write-Host "    $embedUrl" -ForegroundColor Yellow
            Write-Host "  Extract to: $pythonEmbedDir" -ForegroundColor Yellow
            Read-Host "Press Enter to exit"
            exit 1
        }
    }
    else {
        Write-Host "  [OK] Using existing $embedZip" -ForegroundColor Green
    }

    Write-Host "  Extracting Python embeddable..."
    if (Test-Path $pythonEmbedDir) {
        Remove-Item -Path $pythonEmbedDir -Recurse -Force
    }
    Expand-Archive -Path $embedZip -DestinationPath $pythonEmbedDir -Force
    Write-Host "  [OK] Extracted to $pythonEmbedDir" -ForegroundColor Green

    # Enable site-packages in embeddable Python
    $pthFile = Get-ChildItem -Path $pythonEmbedDir -Filter "python*._pth" | Select-Object -First 1
    if ($pthFile) {
        $pthContent = @"
python312.zip
.
Lib/site-packages
../
"@
        Set-Content -Path $pthFile.FullName -Value $pthContent -NoNewline
        Write-Host "  [OK] Configured $($pthFile.Name) for site-packages" -ForegroundColor Green
    }

    # Install pip
    Write-Host "  Installing pip..."
    $getPipUrl = "https://bootstrap.pypa.io/get-pip.py"
    $getPipPath = Join-Path $scriptDir "get-pip.py"
    if (-not (Test-Path $getPipPath)) {
        Invoke-WebRequest -Uri $getPipUrl -OutFile $getPipPath -UseBasicParsing
    }
    & $pythonExe $getPipPath --quiet
    Write-Host "  [OK] pip installed" -ForegroundColor Green
    Remove-Item -Path $getPipPath -Force -ErrorAction SilentlyContinue

    $pythonCmd = $pythonExe
}

# ============================================================
#  Step 3: Install dependencies
# ============================================================
Show-Step "Step 3: Installing dependencies..."

$requirementsFile = Join-Path $scriptDir "requirements.txt"
if (-not (Test-Path $requirementsFile)) {
    Write-Host "  [ERROR] requirements.txt not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if packages are already installed
$checkOutput = & $pythonCmd -c "import pyautogui, cv2, PIL, numpy, keyboard, pydirectinput; print('ok')" 2>&1
if ($checkOutput -ne "ok") {
    Write-Host "  Installing packages from requirements.txt..."
    & $pythonCmd -m pip install -r $requirementsFile --quiet
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [WARN] Some packages may have failed. Trying individually..." -ForegroundColor Yellow
        $packages = Get-Content $requirementsFile | Where-Object { $_ -match '\S' -and $_ -notmatch '^#' }
        foreach ($pkg in $packages) {
            & $pythonCmd -m pip install $pkg --quiet 2>&1 | Out-Null
        }
    }
    Write-Host "  [OK] Dependencies installed" -ForegroundColor Green
}
else {
    Write-Host "  [OK] All dependencies already installed" -ForegroundColor Green
}

# ============================================================
#  Step 4: Run the GUI
# ============================================================
Show-Step "Step 4: Launching RedM Fishing Macro..."

$guiScript = Join-Path $scriptDir "fishing_gui.py"
if (-not (Test-Path $guiScript)) {
    Write-Host "  [ERROR] fishing_gui.py not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "  Launching GUI... (this window will close)" -ForegroundColor Green
Write-Host ""

# Use pythonw if available (no console), otherwise python
$runExe = $pythonCmd
if ($pythonCmd -like "*\python_embed\python.exe" -and (Test-Path $pythonwExe)) {
    $runExe = $pythonwExe
}
elseif ($pythonCmd -like "*\python.exe") {
    $pythonwCandidate = $pythonCmd -replace "python\.exe$", "pythonw.exe"
    if (Test-Path $pythonwCandidate) {
        $runExe = $pythonwCandidate
    }
}

Start-Process -FilePath $runExe -ArgumentList $guiScript -WorkingDirectory $scriptDir

Start-Sleep -Seconds 2
Write-Host "  [OK] GUI launched successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "  You can close this window now." -ForegroundColor DarkGray
Write-Host ""
