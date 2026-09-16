# .\_eval.ps1 -Run <run folder> -Ckpt model_1600.pt [-NumEnvs 64] [-Tag cond01] [-ExtraArgs @(...)]
# -ExtraArgs is passed straight through to measure_crab.py (e.g. --override, --actuator_scale,
# --delay_fixed, --obs_noise, --scenarios, --drop_test, --spawn_height_offset).
param(
    [Parameter(Mandatory = $true)][string]$Run,
    [Parameter(Mandatory = $true)][string]$Ckpt,
    [int]$NumEnvs = 64,
    [string]$Tag = "",
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$ExtraArgs
)

$env:OMNI_KIT_ACCEPT_EULA = "YES"
# NOTE: PowerShell variable names are case-insensitive, so this local must NOT be named $tag --
# that would silently alias and overwrite the -Tag parameter itself.
$logTag = "$Run" + "_" + ($Ckpt -replace "[^0-9]", "") + $(if ($Tag) { "_$Tag" } else { "" })
$out = "D:\Tominaga\slope-climbing-robot\tools\logs\measure_$logTag.txt"
$err = "D:\Tominaga\slope-climbing-robot\tools\logs\measure_$logTag.err.txt"

# conda activation + h5py preload: see _launch.ps1 for why (2026-09-16, h5py-vs-isaacsim.sensors.rtx
# DLL race).
& "C:\Users\WRS\miniconda3\shell\condabin\conda-hook.ps1" | Out-Null
conda activate "D:\Tominaga\envs\isaac_env"
$allArgs = @(
    "-u", "D:\Tominaga\slope-climbing-robot\tools\runs\_preload_h5py_and_run.py",
    "D:\Tominaga\slope-climbing-robot\tools\measure_crab.py",
    "--load_run", $Run, "--checkpoint", $Ckpt, "--num_envs", "$NumEnvs"
)
if ($Tag) { $allArgs += @("--tag", $Tag) }
if ($ExtraArgs) { $allArgs += $ExtraArgs }
$p = Start-Process -FilePath "D:\Tominaga\envs\isaac_env\python.exe" -ArgumentList $allArgs `
  -WorkingDirectory "D:\Tominaga\IsaacLab" -NoNewWindow -PassThru `
  -RedirectStandardOutput $out -RedirectStandardError $err

Write-Output "EVAL $Run $Ckpt $Tag PID=$($p.Id)"
$p.Id | Out-File -Encoding ascii "D:\Tominaga\slope-climbing-robot\tools\logs\pid_eval_$logTag.txt"
