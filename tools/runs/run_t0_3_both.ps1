# Runs t0_3_s6_diag.py once per checkpoint (each its own process -> its own single
# ManagerBasedRLEnv), sequentially. See the K1 note in t0_3_s6_diag.py's docstring for why: running
# both checkpoints inside one process (the original script) hung on the second env's construction.
#
# Usage: .\run_t0_3_both.ps1 [-NumEnvs 64]
param(
    [int]$NumEnvs = 64
)

$env:OMNI_KIT_ACCEPT_EULA = "YES"
& "C:\Users\WRS\miniconda3\shell\condabin\conda-hook.ps1" | Out-Null
conda activate "D:\Tominaga\envs\isaac_env"

$runs = @(
    @{ Name = "G_real_peak"; LoadRun = "2026-09-16_17-28-46_G_real_peak"; Ckpt = "model_2999.pt" },
    @{ Name = "H_eff13p5"; LoadRun = "2026-09-17_00-08-51_H_eff13p5"; Ckpt = "model_2999.pt" }
)

foreach ($r in $runs) {
    $out = "D:\Tominaga\slope-climbing-robot\tools\logs\T0_3_s6_diag_$($r.Name).md"
    $stdout = "D:\Tominaga\slope-climbing-robot\tools\logs\t0_3_$($r.Name).txt"
    $stderr = "D:\Tominaga\slope-climbing-robot\tools\logs\t0_3_$($r.Name).err.txt"
    Write-Output "=== t0_3_s6_diag: $($r.Name) ==="
    $allArgs = @(
        "-u", "D:\Tominaga\slope-climbing-robot\tools\runs\_preload_h5py_and_run.py",
        "D:\Tominaga\slope-climbing-robot\tools\t0_3_s6_diag.py",
        "--load_run", $r.LoadRun, "--checkpoint", $r.Ckpt, "--name", $r.Name,
        "--num_envs", "$NumEnvs", "--out", $out
    )
    $p = Start-Process -FilePath "D:\Tominaga\envs\isaac_env\python.exe" -ArgumentList $allArgs `
      -WorkingDirectory "D:\Tominaga\IsaacLab" -NoNewWindow -PassThru -Wait `
      -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    Write-Output "$($r.Name) exit=$($p.ExitCode) -> $out"
}
