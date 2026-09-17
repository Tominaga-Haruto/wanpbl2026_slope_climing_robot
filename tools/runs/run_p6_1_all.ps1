# Runs p6_1_footpitch.py's Part1, then Part2 (x2 run_names), then Part3, each in its OWN process
# (its own single ManagerBasedRLEnv). See the K1 note in p6_1_footpitch.py's docstring: running
# all 4 envs (Part1 + Part2 x2 + Part3) inside one process (the original script) hung on the
# second env's construction. Part2/Part3 read the FFE calibration Part1 writes to --calib_json.
#
# Usage: .\run_p6_1_all.ps1 [-LoadRun 2026-09-16_17-28-46_G_real_peak] [-Checkpoint model_2999.pt]
param(
    [string]$LoadRun = "2026-09-16_17-28-46_G_real_peak",
    [string]$Checkpoint = "model_2999.pt"
)

$env:OMNI_KIT_ACCEPT_EULA = "YES"
& "C:\Users\WRS\miniconda3\shell\condabin\conda-hook.ps1" | Out-Null
conda activate "D:\Tominaga\envs\isaac_env"

$calibJson = "D:\Tominaga\slope-climbing-robot\tools\logs\P6_1_calib.json"

function Run-Part($PartArgs, $Tag, $Out) {
    # NOTE: Write-Host (not Write-Output) for progress lines -- Write-Output inside a function
    # joins the pipeline output, so an earlier bug here made $ec1 an array of [progress-strings,
    # exit-code] instead of just the exit code, and `-ne 0` against that array was always true
    # (element-wise), aborting after Part1 even though it had exited 0.
    $stdout = "D:\Tominaga\slope-climbing-robot\tools\logs\p6_1_$Tag.txt"
    $stderr = "D:\Tominaga\slope-climbing-robot\tools\logs\p6_1_$Tag.err.txt"
    Write-Host "=== p6_1_footpitch: $Tag ==="
    $allArgs = @(
        "-u", "D:\Tominaga\slope-climbing-robot\tools\runs\_preload_h5py_and_run.py",
        "D:\Tominaga\slope-climbing-robot\tools\p6_1_footpitch.py"
    ) + $PartArgs + @("--calib_json", $calibJson, "--load_run", $LoadRun, "--checkpoint", $Checkpoint, "--out", $Out)
    $p = Start-Process -FilePath "D:\Tominaga\envs\isaac_env\python.exe" -ArgumentList $allArgs `
      -WorkingDirectory "D:\Tominaga\IsaacLab" -NoNewWindow -PassThru -Wait `
      -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    Write-Host "$Tag exit=$($p.ExitCode) -> $Out"
    return $p.ExitCode
}

$ec1 = Run-Part @("--part", "1") "part1" "D:\Tominaga\slope-climbing-robot\tools\logs\P6_1_footpitch_part1.md"
if ($ec1 -ne 0) { Write-Output "Part1 failed (exit=$ec1) -- stopping, Part2/3 need its calib_json"; exit $ec1 }

$ec2a = Run-Part @("--part", "2", "--run_name", "G_real_peak") "part2_G" "D:\Tominaga\slope-climbing-robot\tools\logs\P6_1_footpitch_part2_G.md"
$ec2b = Run-Part @("--part", "2", "--run_name", "H_eff13p5") "part2_H" "D:\Tominaga\slope-climbing-robot\tools\logs\P6_1_footpitch_part2_H.md"
$ec3 = Run-Part @("--part", "3") "part3" "D:\Tominaga\slope-climbing-robot\tools\logs\P6_1_footpitch_part3.md"

Write-Output "done: part1=$ec1 part2_G=$ec2a part2_H=$ec2b part3=$ec3"
