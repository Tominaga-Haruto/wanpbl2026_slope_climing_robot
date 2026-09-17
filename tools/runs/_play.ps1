# 学習した方策を GUI で再生する。
#
#   .\_play.ps1 -Run 2026-09-16_05-15-41_B_combined -Ckpt model_2999.pt
#   .\_play.ps1 -Run 2026-09-16_05-14-59_A_base0821 -Ckpt model_2999.pt -Terrain rough
#   .\_play.ps1 -Run 2026-09-16_05-15-41_B_combined -Ckpt model_2999.pt -Video
#
# -Terrain flat  : 全面平地（B / C_flatonly の学習条件）。既定。
# -Terrain rough : 08-21 の混合地形（A / C_noflat の学習条件）。
# -Video         : GUI を出さずに動画だけ録る（GUI が起動しない環境向け）。
param(
    [Parameter(Mandatory = $true)][string]$Run,
    [string]$Ckpt = "model_2999.pt",
    [ValidateSet("flat", "rough")][string]$Terrain = "flat",
    [int]$NumEnvs = 16,
    [switch]$Video,
    [int]$VideoLength = 400
)

$env:OMNI_KIT_ACCEPT_EULA = "YES"

# conda activation + h5py preload: see _launch.ps1 for why (2026-09-16, h5py-vs-isaacsim.sensors.rtx
# DLL race).
& "C:\Users\WRS\miniconda3\shell\condabin\conda-hook.ps1" | Out-Null
conda activate "D:\Tominaga\envs\isaac_env"

$py   = "D:\Tominaga\envs\isaac_env\python.exe"
$pre  = "D:\Tominaga\slope-climbing-robot\tools\runs\_preload_h5py_and_run.py"
$play = "D:\Tominaga\IsaacLab\scripts\reinforcement_learning\rsl_rl\play.py"
$runDir = "D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\$Run"
$ckpt = Join-Path $runDir $Ckpt

if (-not (Test-Path $ckpt)) { Write-Error "checkpoint not found: $ckpt"; exit 1 }

# noise_std_type ('log' vs 'scalar') は学習時に実際に使われた値でないとチェックポイントの
# state_dict読み込みに失敗する（distribution.log_std_param / distribution.std_param のキー不一致）。
# 起動行の手書き("log"固定)に頼らず、そのrun自身のparams\agent.yamlから読み直す
# (2026-09-17: H_gainDRの起動行にこのオーバーライドを入れ忘れ、rsl-rl既定の'scalar'のまま
# 学習してしまった事故を受けての修正)。
$noiseStdType = "log"
$agentYaml = Join-Path $runDir "params\agent.yaml"
if (Test-Path $agentYaml) {
    $yamlText = Get-Content $agentYaml -Raw
    if ($yamlText -match "std_type:\s*(\S+)") {
        $noiseStdType = $matches[1]
    } else {
        Write-Warning "std_type not found in $agentYaml -- falling back to '$noiseStdType'"
    }
} else {
    Write-Warning "$agentYaml not found -- falling back to noise_std_type='$noiseStdType'"
}
Write-Output "noise_std_type: $noiseStdType (from $agentYaml)"

# $pre で play.py をラップして h5py を Kit 起動前に先読みする。しないと
# "ImportError: DLL load failed while importing _errors" で落ちる（2026-09-16 判明、
# 特に --video で再現しやすい）。
$a = @(
    $pre,
    $play,
    "--task", "Velocity-Rough-Skyentific-Poclegs-Play-v0",
    "--num_envs", "$NumEnvs",
    "--checkpoint", $ckpt,
    "agent.policy.noise_std_type=$noiseStdType"
)

if ($Terrain -eq "flat") {
    $a += @(
        "env.scene.terrain.terrain_generator.sub_terrains.flat.proportion=1.0",
        "env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope.proportion=0.0",
        "env.scene.terrain.terrain_generator.sub_terrains.hf_pyramid_slope_inv.proportion=0.0",
        "env.scene.terrain.terrain_generator.sub_terrains.pyramid_stairs.proportion=0.0",
        "env.scene.terrain.terrain_generator.sub_terrains.pyramid_stairs_inv.proportion=0.0",
        "env.scene.terrain.terrain_generator.sub_terrains.wave_terrain.proportion=0.0",
        "env.scene.terrain.terrain_generator.sub_terrains.random_rough.proportion=0.0",
        "env.curriculum.terrain_levels=null"
    )
}

if ($Video) {
    $a += @("--video", "--video_length", "$VideoLength", "--headless")
} else {
    $a += @("--real-time")
}

Write-Output "checkpoint : $ckpt"
Write-Output "terrain    : $Terrain"
Push-Location "D:\Tominaga\IsaacLab"
try { & $py @a } finally { Pop-Location }
