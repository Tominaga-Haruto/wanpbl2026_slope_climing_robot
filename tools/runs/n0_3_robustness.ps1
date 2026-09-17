# N0-3 (exp09): robustness sweep on a target checkpoint, same condition set/numbering as
# tools/logs/REPORT_exp04_stop4.md (1,3,4,6,7,8,9,10,16) restricted to S1,S6,S7,S8,S9, plus the
# base_lin_vel dropout timings from P6-2 (reused verbatim via tools/p6_2_basevel_dropout.py --
# durations 0.1,0.2,0.5,1.0,2.0 so the 0.2s-zero / 0.5s-hold points line up with the existing
# H_eff13p5@2999 P6-2 data already on file). Max 3 concurrent GPU processes.
#
# Usage: .\n0_3_robustness.ps1 -Run "2026-09-17_21-18-22_L_angstd_w1" -Ckpt "model_4000.pt"
param(
    [Parameter(Mandatory = $true)][string]$Run,
    [Parameter(Mandatory = $true)][string]$Ckpt,
    [int]$NumEnvs = 64,
    [int]$MaxConcurrent = 3
)

$env:OMNI_KIT_ACCEPT_EULA = "YES"
& "C:\Users\WRS\miniconda3\shell\condabin\conda-hook.ps1" | Out-Null
conda activate "D:\Tominaga\envs\isaac_env"

$py = "D:\Tominaga\envs\isaac_env\python.exe"
$pre = "D:\Tominaga\slope-climbing-robot\tools\runs\_preload_h5py_and_run.py"
$mc = "D:\Tominaga\slope-climbing-robot\tools\measure_crab.py"
$p62 = "D:\Tominaga\slope-climbing-robot\tools\p6_2_basevel_dropout.py"
$wd = "D:\Tominaga\IsaacLab"
$scenarios = "S1,S6,S7,S8,S9"

# tag -> extra measure_crab.py args (condition numbers/content match REPORT_exp04_stop4.md verbatim)
$conditions = @{
    "c01_baseline"    = @()
    "c03_ak80_12"     = @("--override", "scene.robot.actuators.hfe.effort_limit=12.0", "--override", "scene.robot.actuators.ffe.effort_limit=12.0")
    "c04_ak80_9"      = @("--override", "scene.robot.actuators.hfe.effort_limit=9.0", "--override", "scene.robot.actuators.ffe.effort_limit=9.0")
    "c06_stiff_0p7"   = @("--actuator_scale", "stiffness=0.7")
    "c07_stiff_1p3"   = @("--actuator_scale", "stiffness=1.3")
    "c08_damp_0p5"    = @("--actuator_scale", "damping=0.5")
    "c09_damp_2p0"    = @("--actuator_scale", "damping=2.0")
    "c10_delay4"      = @("--delay_fixed", "4")
}

$jobs = @()
foreach ($tag in $conditions.Keys) {
    $out = "D:\Tominaga\slope-climbing-robot\tools\logs\n0_3_$($Run)_$($tag).txt"
    $err = "D:\Tominaga\slope-climbing-robot\tools\logs\n0_3_$($Run)_$($tag).err.txt"
    $allArgs = @(
        "-u", $pre, $mc,
        "--load_run", $Run, "--checkpoint", $Ckpt, "--num_envs", "$NumEnvs",
        "--scenarios", $scenarios, "--tag", $tag
    ) + $conditions[$tag]

    while (($jobs | Where-Object { -not $_.HasExited }).Count -ge $MaxConcurrent) {
        Start-Sleep -Seconds 15
    }
    Write-Output "=== launching $tag ==="
    $p = Start-Process -FilePath $py -ArgumentList $allArgs -WorkingDirectory $wd -NoNewWindow -PassThru `
          -RedirectStandardOutput $out -RedirectStandardError $err
    $jobs += $p
}

# c16: drop test (own protocol, ignores --scenarios; spawn_height_offset matches the 0.05m used for
# the existing H_eff13p5/G_real_peak c16_droptest runs)
while (($jobs | Where-Object { -not $_.HasExited }).Count -ge $MaxConcurrent) { Start-Sleep -Seconds 15 }
Write-Output "=== launching c16_droptest ==="
$out16 = "D:\Tominaga\slope-climbing-robot\tools\logs\n0_3_$($Run)_c16_droptest.txt"
$err16 = "D:\Tominaga\slope-climbing-robot\tools\logs\n0_3_$($Run)_c16_droptest.err.txt"
$allArgs16 = @(
    "-u", $pre, $mc,
    "--load_run", $Run, "--checkpoint", $Ckpt, "--num_envs", "$NumEnvs",
    "--drop_test", "--spawn_height_offset", "0.05", "--tag", "c16_droptest"
)
$jobs += Start-Process -FilePath $py -ArgumentList $allArgs16 -WorkingDirectory $wd -NoNewWindow -PassThru `
          -RedirectStandardOutput $out16 -RedirectStandardError $err16

# P6-2 base_lin_vel dropout (own script, own protocol) -- durations match existing H_eff13p5 data
while (($jobs | Where-Object { -not $_.HasExited }).Count -ge $MaxConcurrent) { Start-Sleep -Seconds 15 }
Write-Output "=== launching P6-2 dropout ==="
$outP62 = "D:\Tominaga\slope-climbing-robot\tools\logs\n0_3_$($Run)_p6_2_dropout.txt"
$errP62 = "D:\Tominaga\slope-climbing-robot\tools\logs\n0_3_$($Run)_p6_2_dropout.err.txt"
$mdP62 = "D:\Tominaga\slope-climbing-robot\tools\logs\n0_3_$($Run)_p6_2_dropout.md"
$allArgsP62 = @(
    "-u", $pre, $p62,
    "--load_run", $Run, "--checkpoint", $Ckpt, "--num_envs", "$NumEnvs",
    "--durations", "0.1,0.2,0.5,1.0,2.0", "--out", $mdP62
)
$jobs += Start-Process -FilePath $py -ArgumentList $allArgsP62 -WorkingDirectory $wd -NoNewWindow -PassThru `
          -RedirectStandardOutput $outP62 -RedirectStandardError $errP62

Write-Output "all $($jobs.Count) jobs launched, waiting..."
$jobs | Wait-Process
Write-Output "N0-3 robustness sweep done: $Run @ $Ckpt"
