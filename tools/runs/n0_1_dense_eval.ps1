# N0-1 (exp09): dense S6/S9-only sweep over every saved checkpoint after iter 3000 for a run,
# 2 eval seeds each, 256 env, 1 process per (checkpoint, seed) -- measure_crab.py is already
# single-env-per-process safe. Runs up to $MaxConcurrent measure_crab.py processes at once
# (GPU known limit is 3 concurrent processes per wrs_new_chat_start.md).
#
# Usage: .\n0_1_dense_eval.ps1 -Run "2026-09-17_21-18-22_L_angstd_w1" -Checkpoints @(3200,3400,3600,3800,4000,4200,4400,4498) -Seeds @(1,2)
param(
    [Parameter(Mandatory = $true)][string]$Run,
    [Parameter(Mandatory = $true)][int[]]$Checkpoints,
    [int[]]$Seeds = @(1, 2),
    [int]$NumEnvs = 256,
    [string]$Scenarios = "S6,S9",
    [int]$MaxConcurrent = 3
)

$env:OMNI_KIT_ACCEPT_EULA = "YES"
& "C:\Users\WRS\miniconda3\shell\condabin\conda-hook.ps1" | Out-Null
conda activate "D:\Tominaga\envs\isaac_env"

$py = "D:\Tominaga\envs\isaac_env\python.exe"
$pre = "D:\Tominaga\slope-climbing-robot\tools\runs\_preload_h5py_and_run.py"
$mc = "D:\Tominaga\slope-climbing-robot\tools\measure_crab.py"
$wd = "D:\Tominaga\IsaacLab"

$jobs = @()
foreach ($iter in $Checkpoints) {
    $ckpt = "model_$iter.pt"
    foreach ($seed in $Seeds) {
        $tag = "n0_1_seed$seed"
        $out = "D:\Tominaga\slope-climbing-robot\tools\logs\n0_1_$($Run)_$($iter)_seed$seed.txt"
        $err = "D:\Tominaga\slope-climbing-robot\tools\logs\n0_1_$($Run)_$($iter)_seed$seed.err.txt"
        $allArgs = @(
            "-u", $pre, $mc,
            "--load_run", $Run, "--checkpoint", $ckpt, "--num_envs", "$NumEnvs",
            "--seed", "$seed", "--scenarios", $Scenarios, "--tag", $tag
        )

        while (($jobs | Where-Object { -not $_.HasExited }).Count -ge $MaxConcurrent) {
            Start-Sleep -Seconds 15
        }

        Write-Output "=== launching $Run @ $ckpt seed=$seed ==="
        $p = Start-Process -FilePath $py -ArgumentList $allArgs -WorkingDirectory $wd -NoNewWindow -PassThru `
              -RedirectStandardOutput $out -RedirectStandardError $err
        $jobs += $p
    }
}

Write-Output "all $($jobs.Count) jobs launched, waiting for completion..."
$jobs | Wait-Process
Write-Output "N0-1 dense eval done: $Run, checkpoints=$($Checkpoints -join ','), seeds=$($Seeds -join ',')"
