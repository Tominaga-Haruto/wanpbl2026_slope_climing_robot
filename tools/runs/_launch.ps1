# Generic launcher: .\_launch.ps1 -RunName <name> -ExtraArgs @(...)
param(
    [Parameter(Mandatory = $true)][string]$RunName,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$ExtraArgs
)

$env:OMNI_KIT_ACCEPT_EULA = "YES"
$env:ACCEPT_EULA = "Y"

$py   = "D:\Tominaga\envs\isaac_env\python.exe"
$pre  = "D:\Tominaga\slope-climbing-robot\tools\runs\_preload_h5py_and_run.py"
$trn  = "D:\Tominaga\IsaacLab\scripts\reinforcement_learning\rsl_rl\train.py"
$wd   = "D:\Tominaga\IsaacLab"
$out  = "D:\Tominaga\slope-climbing-robot\tools\logs\run_$RunName.txt"
$err  = "D:\Tominaga\slope-climbing-robot\tools\logs\run_$RunName.err.txt"

# $pre wraps $trn to preload h5py before Kit starts (see _preload_h5py_and_run.py), otherwise
# train.py crashes with "ImportError: DLL load failed while importing _errors" (h5py vs a
# same-named DLL that Isaac Sim/Kit's own native plugins load first). Found 2026-09-16.
$allArgs = @($pre, $trn) + $ExtraArgs
Write-Output "LAUNCH $RunName"
Write-Output ($allArgs -join " ")

$p = Start-Process -FilePath $py -ArgumentList $allArgs -WorkingDirectory $wd -NoNewWindow -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err
Write-Output "PID=$($p.Id)"
$p.Id | Out-File -Encoding ascii "D:\Tominaga\slope-climbing-robot\tools\logs\pid_$RunName.txt"
