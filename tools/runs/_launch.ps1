# Generic launcher: .\_launch.ps1 -RunName <name> -ExtraArgs @(...)
param(
    [Parameter(Mandatory = $true)][string]$RunName,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$ExtraArgs
)

$env:OMNI_KIT_ACCEPT_EULA = "YES"
$env:ACCEPT_EULA = "Y"

$py   = "D:\Tominaga\envs\isaac_env\python.exe"
$trn  = "D:\Tominaga\IsaacLab\scripts\reinforcement_learning\rsl_rl\train.py"
$wd   = "D:\Tominaga\IsaacLab"
$out  = "D:\Tominaga\slope-climbing-robot\tools\logs\run_$RunName.txt"
$err  = "D:\Tominaga\slope-climbing-robot\tools\logs\run_$RunName.err.txt"

$allArgs = @($trn) + $ExtraArgs
Write-Output "LAUNCH $RunName"
Write-Output ($allArgs -join " ")

$p = Start-Process -FilePath $py -ArgumentList $allArgs -WorkingDirectory $wd -NoNewWindow -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err
Write-Output "PID=$($p.Id)"
$p.Id | Out-File -Encoding ascii "D:\Tominaga\slope-climbing-robot\tools\logs\pid_$RunName.txt"
