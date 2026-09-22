# 2026-09-18 コントローラーとGPUの今日の指示書

> 今日やることは、実機モーターを動かさずに「操縦入力」と「方策パッケージ」をデプロイ可能な形へ近づけること。モーター実験は、Kt用の重り・アーム・固定治具がそろうまで保留する。
>
> コントローラーの詳しい設計は `archive/controller_prep_briefing.md`、GPU側の判断規則は `archive/next_chat_briefing.md` を正本とする。この文書は今日の実行順だけを持つ。

## 完了条件

1. Switch 2 Pro がJetsonで認識され、モーターなしで軸・ボタンの生値を記録できる（完了）。
2. GPU側で今日の仮デプロイ候補を、事前規則どおり決める。
3. 候補ごとに ONNX、golden npz、観測契約、アクチュエータ表、SHA256 がそろっていることを確認する。
4. Jetsonへ運ぶファイルと、実機側へ渡す数値が明確になっている。

## A. Jetson: Switch 2 Pro の乾式準備

### A1. 認識確認（完了、コード・モーターなし）

1. Switch 2 Pro を USB-C 有線でJetsonへつなぐ。Bluetooth は使わない。
2. `evtest` で `Microsoft X-Box 360 pad`（`event2`）を確認した。
3. 左スティック、A / Y、十字キー、ZL / ZR、L / R、HOMEの番号を記録した。

実装で使う入力は、現時点では左スティック（`ABS_X` / `ABS_Y`）だけである。直進仮デプロイに旋回は混ぜない。詳細は `archive/controller_prep_briefing.md` と `archive/controller_next_chat_briefing.md` を正本とする。

### A2. 読み取り実装を始める条件

A1 の結果（表示名とボタン番号）をこのチャットに渡してから `C:\Users\harut\Connect2USB2CAN\controller\pad_probe.py` を実装する。パッケージの導入が必要なら、先にどのPython環境を使うか決める。

初期の操作仕様は、実測で番号を確定するまで固定しない。候補だけは以下。

| 状態 | 指令 |
|---|---|
| ZRを押していない | `(0, 0, 0)` |
| ZR + 左スティック | `(vx, vy, 0)` |
| ZL + 右スティック左右 | `(0, 0, wz)` |
| ZR + ZL | `(vx, vy, wz)` |
| 非常停止 | 専用ボタンでラッチし、再起動まで解除しない |

この段階では画面とログへ値を出すだけ。CAN・モーターへは絶対に送らない。

## B. WRS GPU: 方策パッケージを判定・検品する

### B1. 最新の夜間結果を読む

WRS機 PowerShell で実行:

```powershell
Get-Content D:\Tominaga\slope-climbing-robot\tools\logs\MORNING_0945.md
```

ファイルがなければ:

```powershell
Get-Content D:\Tominaga\slope-climbing-robot\tools\logs\REPORT_night_20260918.md
```

このチャットへ貼るのは、冒頭3行と全ランの判定表だけでよい。

### B2. 今日の候補を決める規則

- 既定の第一候補は `H_eff13p5@2999`。
- `P_gainDR_narrow@4498` が、既存基準に合格し、stiffness ×0.7 の転倒が5%以下で、H_eff13p5に無い不合格を出さず、パッケージ一式もある場合だけ、第一候補に替える。
- `G_real_peak@2999` は予備。
- その場旋回の方策は、今日の実機では吊り試験用。安定した直進候補の代わりにはしない。

### B3. 配布物を検品する

WRS機 PowerShell:

```powershell
Get-ChildItem -Recurse D:\Tominaga\deploy_pkg\20260918 | Select-Object FullName,Length
Get-Content D:\Tominaga\deploy_pkg\20260918\DEPLOY_README.md
Get-FileHash D:\Tominaga\deploy_pkg\20260918\deploy_pkg_20260918.zip -Algorithm SHA256
```

確認対象:

- ONNX
- golden npz
- `obs_contract.md` または同等の観測契約
- 関節順、42次元観測、10次元行動、50 Hz、action scale 0.5
- 関節グループ別 stiffness / damping / effort
- SHA256

ONNX・npz・zipは Git に入れない。Jetsonへは USB または安全な共有手段でコピーする。

### B4. GPUで確認すること

- 通常表示用と動画用の再生コマンドを、WRSの `MORNING_0945.md` にある実名のまま一度ずつ起動する。
- GPU温度、VRAM、学習・評価プロセスを確認する。新規学習は、夜間の報告と `archive/next_chat_briefing.md` の規則を確認するまで始めない。
- GitHubへpushするのはコード・文書・報告書だけ。`.onnx`、`.npz`、`.pt`、動画、ログ、USD、鍵は含めない。

## C. 実機側への受け渡し

GPU側の検品が終わったら、Jetson上の方策配置先を確認してから候補パッケージを置く。実機制御ループの実装開始には、候補名と次の5点が必要。

1. ONNX
2. golden npz
3. 観測契約
4. アクチュエータ表
5. SHA256

これがそろうまで CAN と方策を接続しない。

## 今日やらないこと

- モーターを方策で動かすこと
- Ktを脚付き全身で測ること
- Bluetoothのドライバー調査
- 判定規則外のGPU学習を始めること
- モデル・重み・生ログをGitへ追加すること
