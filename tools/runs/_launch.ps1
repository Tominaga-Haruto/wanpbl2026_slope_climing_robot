# Generic launcher: .\_launch.ps1 -RunName <name> -ExtraArgs @(...)
param(
    [Parameter(Mandatory = $true)][string]$RunName,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$ExtraArgs
)

$env:OMNI_KIT_ACCEPT_EULA = "YES"
$env:ACCEPT_EULA = "Y"

# conda activation (adds isaac_env's own Library\bin/Scripts/bin to PATH) measurably avoids the
# h5py-vs-isaacsim.sensors.rtx DLL race below -- confirmed 2026-09-16 by running the same 64-env/
# 20-iter smoke test with and without activation. Do this before Start-Process so the child
# inherits the augmented PATH.
& "C:\Users\WRS\miniconda3\shell\condabin\conda-hook.ps1" | Out-Null
conda activate "D:\Tominaga\envs\isaac_env"

$py   = "D:\Tominaga\envs\isaac_env\python.exe"
$pre  = "D:\Tominaga\slope-climbing-robot\tools\runs\_preload_h5py_and_run.py"
$trn  = "D:\Tominaga\IsaacLab\scripts\reinforcement_learning\rsl_rl\train.py"
$wd   = "D:\Tominaga\IsaacLab"
$out  = "D:\Tominaga\slope-climbing-robot\tools\logs\run_$RunName.txt"
$err  = "D:\Tominaga\slope-climbing-robot\tools\logs\run_$RunName.err.txt"

# 2026-09-17: H_gainDRの起動でagent.policy.noise_std_type=logのオーバーライドを入れ忘れ、
# rsl-rl既定の'scalar'のまま学習してしまう事故があった。以後、起動行にこのオーバーライドが
# 全く含まれていない場合は警告して起動を止める(既定の挙動=このプロジェクトの全runがlogで
# 揃っている、を変えない)。明示的に...noise_std_type=scalarと指定した場合はそのまま通す。
$noiseStdTypeArg = $ExtraArgs | Where-Object { $_ -match "^agent\.policy\.noise_std_type=" }
if (-not $noiseStdTypeArg) {
    Write-Error "agent.policy.noise_std_type=<log|scalar> がExtraArgsに見つかりません。このプロジェクトの" `
        "他の全runはnoise_std_type=logで学習されています。意図してscalar(rsl-rl既定)を使う場合も" `
        "明示的に 'agent.policy.noise_std_type=scalar' を渡してください。起動を中止します。"
    exit 1
}
Write-Output "noise_std_type override confirmed: $noiseStdTypeArg"

# $pre wraps $trn to preload h5py before Kit starts (see _preload_h5py_and_run.py). Belt-and-
# suspenders alongside the conda activation above: train.py crashes with "ImportError: DLL load
# failed while importing _errors" when isaacsim.sensors.rtx's own bundled hdf5.dll (under
# isaacsim\kit\dev\libs\sensors\generic_model_output\bin\) wins the same-name DLL race against
# h5py's bundled one. Found + root-caused 2026-09-16.
$allArgs = @($pre, $trn) + $ExtraArgs
Write-Output "LAUNCH $RunName"
Write-Output ($allArgs -join " ")

$p = Start-Process -FilePath $py -ArgumentList $allArgs -WorkingDirectory $wd -NoNewWindow -PassThru `
        -RedirectStandardOutput $out -RedirectStandardError $err
Write-Output "PID=$($p.Id)"
$p.Id | Out-File -Encoding ascii "D:\Tominaga\slope-climbing-robot\tools\logs\pid_$RunName.txt"
