# Проброс порта Windows -> WSL для доступа к сайту из домашней сети.
# Запуск из WSL: make lan
# Скрипт сам запросит права администратора (UAC).

param(
    [int]$ListenPort = 8080,
    [int]$TargetPort = 3000
)

$ErrorActionPreference = "Stop"

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    $arguments = @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", "`"$PSCommandPath`"",
        "-ListenPort", $ListenPort,
        "-TargetPort", $TargetPort
    )
    $process = Start-Process -FilePath "powershell.exe" -ArgumentList $arguments -Verb RunAs -Wait -PassThru
    exit $process.ExitCode
}

$logPath = Join-Path $env:TEMP "piano-school-lan.log"
Start-Transcript -Path $logPath -Force | Out-Null

try {
    $wslIp = ((wsl.exe -e hostname -I) -split "\s+")[0]
    if (-not $wslIp) {
        throw "Не удалось определить IP WSL. Убедитесь, что WSL запущен."
    }

    netsh interface portproxy delete v4tov4 listenport=$ListenPort listenaddress=0.0.0.0 2>$null | Out-Null
    netsh interface portproxy add v4tov4 listenport=$ListenPort listenaddress=0.0.0.0 connectport=$TargetPort connectaddress=$wslIp

    $ruleName = "Piano School LAN $ListenPort"
    Remove-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    New-NetFirewallRule -DisplayName $ruleName `
        -Direction Inbound `
        -Action Allow `
        -Protocol TCP `
        -LocalPort $ListenPort `
        -Profile Any | Out-Null

    $lanIp = Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.IPAddress -like "192.168.*" } |
        Select-Object -First 1 -ExpandProperty IPAddress

    Write-Host "OK: Windows port $ListenPort -> ${wslIp}:$TargetPort"
    if ($lanIp) {
        Write-Host "LAN URL: http://${lanIp}:$ListenPort"
    }
    netsh interface portproxy show v4tov4
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)"
    throw
}
finally {
    Stop-Transcript | Out-Null
}
