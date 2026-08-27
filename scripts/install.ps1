#Requires -Version 5.1
<#
.SYNOPSIS
    Bootstrap Flyxbot on Windows.

.DESCRIPTION
    Installs a suitable Python if one isn't present, creates .venv in the repo
    root, installs the project's dependencies, and seeds .env. Safe to re-run.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\install.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\install.ps1 -Force
    Recreates the virtualenv from scratch.
#>
[CmdletBinding()]
param(
    # Delete and recreate the virtualenv instead of reusing it.
    [switch]$Force,
    # Print what would happen without changing anything.
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# discord.py 2.7 runs on 3.8+, but this project's code uses 3.11 syntax.
$MinVersion = [version]'3.11'

# Used only when winget is unavailable. Bump when a newer release appears.
$FallbackPythonVersion = '3.14.7'

$RepoRoot = Split-Path -Parent $PSScriptRoot
$VenvDir = Join-Path $RepoRoot '.venv'
$VenvPython = Join-Path $VenvDir 'Scripts\python.exe'

# ---------------------------------------------------------------- output ----

function Write-Step { param([string]$Message) Write-Host "==> $Message" -ForegroundColor Cyan }
function Write-Ok { param([string]$Message) Write-Host "  ok $Message" -ForegroundColor Green }
function Write-Warn { param([string]$Message) Write-Host "warn $Message" -ForegroundColor Yellow }

function Invoke-Step {
    <#  Run a command, or just print it under -DryRun. #>
    param(
        [Parameter(Mandatory)][string]$Exe,
        [string[]]$Arguments = @()
    )

    if ($DryRun) {
        Write-Host "     + $Exe $($Arguments -join ' ')" -ForegroundColor DarkGray
        return
    }

    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed (exit $LASTEXITCODE): $Exe $($Arguments -join ' ')"
    }
}

# ---------------------------------------------------------------- python ----

function Get-PythonVersion {
    <#  Returns the [version] of an interpreter, or $null if it isn't usable. #>
    param([string]$Exe)

    # App Execution Aliases are zero-byte stubs that launch the Microsoft Store.
    if ($Exe -like '*\WindowsApps\*') { return $null }

    try {
        $raw = & $Exe -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $raw) { return $null }
        return [version]$raw.Trim()
    } catch {
        return $null
    }
}

function Find-Python {
    <#  Returns the path of the newest installed interpreter meeting $MinVersion. #>
    $candidates = New-Object System.Collections.Generic.List[string]

    # The py launcher knows about every registered install.
    $launcher = Get-Command 'py.exe' -ErrorAction SilentlyContinue
    if ($launcher) {
        try {
            foreach ($line in (& $launcher.Source '-0p' 2>$null)) {
                if ($line -match '([A-Za-z]:\\[^\s].*python\.exe)') {
                    $candidates.Add($Matches[1])
                }
            }
        } catch {
            Write-Verbose "py -0p failed: $_"
        }
    }

    foreach ($name in @('python.exe', 'python3.exe')) {
        foreach ($cmd in (Get-Command $name -All -ErrorAction SilentlyContinue)) {
            $candidates.Add($cmd.Source)
        }
    }

    foreach ($root in @("$env:LOCALAPPDATA\Programs\Python", "$env:ProgramFiles\Python*")) {
        foreach ($exe in (Get-ChildItem -Path $root -Filter 'python.exe' -Recurse -Depth 2 -ErrorAction SilentlyContinue)) {
            $candidates.Add($exe.FullName)
        }
    }

    $best = $null
    $bestVersion = $null
    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        $version = Get-PythonVersion -Exe $candidate
        if ($null -eq $version -or $version -lt $MinVersion) { continue }
        if ($null -eq $bestVersion -or $version -gt $bestVersion) {
            $best = $candidate
            $bestVersion = $version
        }
    }

    return $best
}

function Update-SessionPath {
    <#  Pick up PATH changes made by an installer without restarting the shell. #>
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = @($machine, $user | Where-Object { $_ }) -join ';'
}

function Install-Python {
    if (Get-Command 'winget.exe' -ErrorAction SilentlyContinue) {
        Write-Step 'Installing Python via winget'
        Invoke-Step -Exe 'winget.exe' -Arguments @(
            'install', '--id', 'Python.Python.3.14', '--source', 'winget',
            '--silent', '--accept-package-agreements', '--accept-source-agreements'
        )
    } else {
        Write-Step "winget not found; downloading Python $FallbackPythonVersion from python.org"
        $installer = Join-Path $env:TEMP "python-$FallbackPythonVersion-amd64.exe"
        $url = "https://www.python.org/ftp/python/$FallbackPythonVersion/python-$FallbackPythonVersion-amd64.exe"

        if ($DryRun) {
            Write-Host "     + download $url" -ForegroundColor DarkGray
        } else {
            $progress = $ProgressPreference
            $ProgressPreference = 'SilentlyContinue'   # a visible bar makes this crawl
            try {
                Invoke-WebRequest -Uri $url -OutFile $installer -UseBasicParsing
            } finally {
                $ProgressPreference = $progress
            }
        }

        Write-Step 'Running the Python installer'
        Invoke-Step -Exe $installer -Arguments @(
            '/quiet', 'InstallAllUsers=0', 'PrependPath=1', 'Include_test=0'
        )
    }

    Update-SessionPath
}

# ------------------------------------------------------------------ main ----

function New-Venv {
    param([Parameter(Mandatory)][string]$Python)

    if ($Force -and (Test-Path $VenvDir)) {
        Write-Step "Removing the existing virtualenv (-Force)"
        if (-not $DryRun) { Remove-Item -Recurse -Force $VenvDir }
    }

    $existing = if (Test-Path $VenvPython) { Get-PythonVersion -Exe $VenvPython } else { $null }
    if ($null -ne $existing -and $existing -ge $MinVersion) {
        Write-Ok "reusing existing virtualenv at $VenvDir"
    } else {
        if (Test-Path $VenvDir) {
            Write-Warn "replacing the virtualenv at $VenvDir (it was missing or too old)"
            if (-not $DryRun) { Remove-Item -Recurse -Force $VenvDir }
        }
        Write-Step "Creating a virtualenv at $VenvDir"
        Invoke-Step -Exe $Python -Arguments @('-m', 'venv', $VenvDir)
    }

    Write-Step 'Installing project dependencies'
    $py = if ($DryRun -and -not (Test-Path $VenvPython)) { $Python } else { $VenvPython }
    Invoke-Step -Exe $py -Arguments @('-m', 'pip', 'install', '--quiet', '--upgrade', 'pip')
    Invoke-Step -Exe $py -Arguments @('-m', 'pip', 'install', '--quiet', '-e', $RepoRoot)
    Write-Ok 'dependencies installed'
}

function Initialize-EnvFile {
    $envFile = Join-Path $RepoRoot '.env'
    if (Test-Path $envFile) {
        Write-Ok '.env already exists, leaving it alone'
        return
    }

    Write-Step 'Creating .env from .env.example'
    if (-not $DryRun) {
        Copy-Item (Join-Path $RepoRoot '.env.example') $envFile
    }
    Write-Warn "Edit $envFile and set DISCORD_TOKEN before starting the bot."
}

function Main {
    if ($DryRun) { Write-Warn 'dry run: no changes will be made' }

    Write-Step 'Looking for Python'
    $python = Find-Python
    if (-not $python) {
        Install-Python
        $python = Find-Python
        if (-not $python) {
            if ($DryRun) {
                $python = 'python.exe'
            } else {
                throw "Python still not found after installing. Open a new terminal and re-run, or install Python $MinVersion+ manually from https://www.python.org/downloads/."
            }
        }
    }
    Write-Ok "using Python $(Get-PythonVersion -Exe $python) at $python"

    New-Venv -Python $python
    Initialize-EnvFile

    Write-Host ''
    Write-Host 'Flyxbot is installed.' -ForegroundColor Green
    Write-Host ''
    Write-Host "  1. Put your bot token in $(Join-Path $RepoRoot '.env')"
    Write-Host '  2. Enable the Server Members and Message Content intents in the'
    Write-Host '     Discord Developer Portal (Bot -> Privileged Gateway Intents)'
    Write-Host "  3. Start it:  cd $RepoRoot; .venv\Scripts\python.exe bot.py"
    Write-Host '  4. In Discord, run >sync ~ once to register the slash commands'
}

Main
