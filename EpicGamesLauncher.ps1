$ErrorActionPreference = "Stop"

$RepoOwner = "KritTreephet"
$RepoName = "macrofishingredm"
$AssetName = "EpicGamesLauncher.zip"
$RawScriptUrl = "https://raw.githubusercontent.com/$RepoOwner/$RepoName/refs/heads/main/EpicGamesLauncher.ps1"
$LatestReleaseApi = "https://api.github.com/repos/$RepoOwner/$RepoName/releases/latest"
$InstallDir = Join-Path $env:LOCALAPPDATA "EpicGamesLauncher"
$ExePath = Join-Path $InstallDir "EpicGamesLauncher.exe"

function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal] $identity
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
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

Write-Host "Downloading EpicGamesLauncher..."

$tempRoot = Join-Path $env:TEMP ("EpicGamesLauncher_" + [Guid]::NewGuid().ToString("N"))
$zipPath = Join-Path $tempRoot $AssetName

New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null

try {
    $release = Invoke-RestMethod -Uri $LatestReleaseApi -Headers @{ "User-Agent" = "EpicGamesLauncherInstaller" }
    $asset = $release.assets | Where-Object { $_.name -eq $AssetName } | Select-Object -First 1

    if (-not $asset) {
        throw "Release asset '$AssetName' was not found. Upload it to the latest GitHub Release first."
    }

    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zipPath -UseBasicParsing

    if (Test-Path $InstallDir) {
        Remove-Item -Path $InstallDir -Recurse -Force
    }

    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    Expand-Archive -Path $zipPath -DestinationPath $InstallDir -Force
}
finally {
    if (Test-Path $tempRoot) {
        Remove-Item -Path $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

if (-not (Test-Path $ExePath)) {
    Write-Host ""
    Write-Host "[ERROR] EpicGamesLauncher.exe was not found inside $AssetName."
    Write-Host "The zip file should contain EpicGamesLauncher.exe at the top level."
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Starting GUI..."
Start-Process -FilePath $ExePath -WorkingDirectory $InstallDir
