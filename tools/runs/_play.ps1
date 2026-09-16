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

$py   = "D:\Tominaga\envs\isaac_env\python.exe"
$play = "D:\Tominaga\IsaacLab\scripts\reinforcement_learning\rsl_rl\play.py"
$ckpt = Join-Path "D:\Tominaga\IsaacLab\logs\rsl_rl\skyentific_poclegs_rough\$Run" $Ckpt

if (-not (Test-Path $ckpt)) { Write-Error "checkpoint not found: $ckpt"; exit 1 }

# 学習時は agent.policy.noise_std_type=log で回したので、ここでも同じにしないと
# 分布パラメータの名前が変わってチェックポイントの読み込みに失敗する。
$a = @(
    $play,
    "--task", "Velocity-Rough-Skyentific-Poclegs-Play-v0",
    "--num_envs", "$NumEnvs",
    "--checkpoint", $ckpt,
    "agent.policy.noise_std_type=log"
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
