# Generic foreground trainer.
# Usage: .\_train_foreground.ps1 -RunName <name> -ExtraArgs @(...)
#
# Unlike _launch.ps1, this script never uses Start-Process. Training output stays
# visible in this PowerShell window, and closing the window or pressing Ctrl+C
# stops the training process. Output is also copied to tools\logs for review.
param(
    [Parameter(Mandatory = $true)][string]$RunName,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$ExtraArgs
)

$env:OMNI_KIT_ACCEPT_EULA = "YES"
$env:ACCEPT_EULA = "Y"

& "C:\Users\WRS\miniconda3\shell\condabin\conda-hook.ps1" | Out-Null
conda activate "D:\Tominaga\envs\isaac_env"

$py = "D:\Tominaga\envs\isaac_env\python.exe"
$pre = "D:\Tominaga\slope-climbing-robot\tools\runs\_preload_h5py_and_run.py"
$train = "D:\Tominaga\IsaacLab\scripts\reinforcement_learning\rsl_rl\train.py"
$workDir = "D:\Tominaga\IsaacLab"
$log = "D:\Tominaga\slope-climbing-robot\tools\logs\run_$RunName.txt"

$noiseStdTypeArg = $ExtraArgs | Where-Object { $_ -match "^agent\.policy\.noise_std_type=" }
if (-not $noiseStdTypeArg) {
    Write-Error "agent.policy.noise_std_type=<log|scalar> がありません。誤設定防止のため起動しません。"
    exit 1
}

$activeTraining = Get-CimInstance Win32_Process | Where-Object {
    $_.ProcessId -ne $PID -and $_.CommandLine -match "train\.py"
}
if ($activeTraining) {
    Write-Error "別の train.py が動いています。二重起動を避けるため停止します。"
    $activeTraining | Select-Object ProcessId, CreationDate, CommandLine | Format-List
    exit 1
}

$allArgs = @($pre, $train) + $ExtraArgs
Write-Output "FOREGROUND TRAIN $RunName"
Write-Output "PowerShellを閉じないでください。停止は Ctrl+C です。"
Write-Output "Log: $log"
Write-Output ($allArgs -join " ")

Push-Location $workDir
try {
    & $py @allArgs 2>&1 | Tee-Object -FilePath $log
    $trainExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

Write-Output "Training exited with code $trainExitCode"
exit $trainExitCode
