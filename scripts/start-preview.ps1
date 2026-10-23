<#
.SYNOPSIS
  Start the ATRI engineering preview static server on 127.0.0.1:8765.

.DESCRIPTION
  The preview needs http:// because figure.js is an ES module and the browser refuses to
  fetch it over file://. python -m http.server is enough.

  Two things learned the hard way:
    * Do NOT start it with `nohup ... &` from git-bash: the process gets reaped and the port
      dies silently a few minutes later (the log just stops). Start-Process from PowerShell
      survives.
    * The server binds IPv6 `::` by default, so `Get-NetTCPConnection -LocalPort 8765`
      filtered to IPv4 shows nothing even though it is listening. Verify with
      Invoke-WebRequest instead.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\start-preview.ps1
  # then open http://127.0.0.1:8765/preview/engineering.html?pack=scratch/candidates/atri-pure-components-01
#>
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $py)) { throw "venv python not found: $py" }

# already up? then say so and leave it alone
try {
    $null = Invoke-WebRequest -Uri 'http://127.0.0.1:8765/preview/engineering.html' -UseBasicParsing -TimeoutSec 4
    Write-Output 'preview already serving on 127.0.0.1:8765'
    return
} catch {}

Start-Process -FilePath $py -ArgumentList '-m','http.server','8765','--bind','127.0.0.1' -WorkingDirectory $root -WindowStyle Hidden
Start-Sleep -Seconds 3
try {
    $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8765/preview/engineering.html' -UseBasicParsing -TimeoutSec 8
    Write-Output ("preview serving on 127.0.0.1:8765 (HTTP {0})" -f $r.StatusCode)
    Write-Output 'open: http://127.0.0.1:8765/preview/engineering.html?pack=scratch/candidates/atri-pure-components-01'
    Write-Output '坐姿核查页: http://127.0.0.1:8765/preview/seat-check.html?word=大哭'
} catch {
    Write-Output ("FAILED: " + $_.Exception.Message)
    exit 1
}
