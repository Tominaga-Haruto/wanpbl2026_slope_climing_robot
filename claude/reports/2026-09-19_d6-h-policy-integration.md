# D6 H方策統合（CAN非接続部）

## 実装したもの

`C:\Users\harut\Connect2USB2CAN\policy_integration.py` を追加した。

- Hの42観測を `obs_contract.md` の順（base速度、角速度、重力投影、速度指令、H順の関節角・速度、前回action）で構成する。
- SHA256検証済みのHパッケージだけをONNX Runtimeで開き、10要素のraw actionを得る。
- `default_joint_pos + 0.5 * action_raw` をH順 `LL_HR, LR_HR, LL_HAA, LR_HAA, LL_HFE, LR_HFE, LL_KFE, LR_KFE, LL_FFE, LR_FFE` の目標角として返す。
- `test_policy_integration.py` は42要素の配置、target式、入力shape／非有限値の拒否を確認する。

CAN、T265、コントローラー、USB機器、`mit_sim`はimportも接続もしていない。

## 検証結果

成果物 `H_eff13p5_2999\H_eff13p5_2999` に対して、golden 500件を再生した。

- action 最大絶対誤差: `1.1920929e-06`（step 335）
- H順目標角 最大絶対誤差: `5.96046448e-07`（step 113）
- いずれも契約閾値 `1e-4` 以下

## 未実装にした境界

D3のロボット取付け後の `R_CB`／`R_OFFSET`、D4/M5の全10台のCAN ID・符号・原点変換表が未確定である。これらを仮定して、H順目標角をCAN順へ変換したり、`mit_sim`／実機CANにゲイン付きで送ることはしない。

よってD6の「H契約部」は完了したが、D6全体およびver9の完成条件は未達である。次はD2のver9骨組み、D3、D4/M5の確定値を接続して、`mit_sim`で10軸の順番・範囲・ゲイン適用を検証する。
