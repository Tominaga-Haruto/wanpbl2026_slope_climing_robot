# .\_eval.ps1 -Run <run folder> -Ckpt model_1600.pt [-NumEnvs 64]
param(
    [Parameter(Mandatory = $true)][string]$Run,
    [Parameter(Mandatory = $true)][string]$Ckpt,
    [int]$NumEnvs = 64
)

$env:OMNI_KIT_ACCEPT_EULA = "YES"
$tag = "$Run" + "_" + ($Ckpt -replace "[^0-9]", "")
$out = "D:\Tominaga\slope-climbing-robot\tools\logs\measure_$tag.txt"
$err = "D:\Tominaga\slope-climbing-robot\tools\logs\measure_$tag.err.txt"

$p = Start-Process -FilePath "D:\Tominaga\envs\isaac_env\python.exe" -ArgumentList @(
    "-u", "D:\Tominaga\slope-climbing-robot\tools\measure_crab.py",
    "--load_run", $Run, "--checkpoint", $Ckpt, "--num_envs", "$NumEnvs"
) -WorkingDirectory "D:\Tominaga\IsaacLab" -NoNewWindow -PassThru `
  -RedirectStandardOutput $out -RedirectStandardError $err

Write-Output "EVAL $Run $Ckpt PID=$($p.Id)"
$p.Id | Out-File -Encoding ascii "D:\Tominaga\slope-climbing-robot\tools\logs\pid_eval_$tag.txt"
