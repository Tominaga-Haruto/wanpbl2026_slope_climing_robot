# 2026-09-19 Isaac Lab debugging #10 終了・#11への引継ぎ

## やったこと

- P2/P3の最終ログとWRS側の再生を確認した。
- WRS側でCodexが利用可能になった。既存のWRS側Codexチャットへ追記で実行・実在確認を依頼する方針に切り替えた。
- `next_chat_briefing.md`をこのノートPC側のIsaac Lab debugging #11用に書き換え、READMEの開始手順でproject_handbook必読を強調した。

## 決めたこと・分かったこと

- P2/P3はtrain行に平地用`sub_terrains`上書きが無く、terrain level 4.714 / 5.075まで上がった。平地のgain DR比較として無効であり、候補・再開元に使わない。
- WRSの既存cloneに削除・未追跡の未整理変更があることが判明した。二重clone、pull、fetch、reset、checkout、restore、stash、削除をせず、read-onlyのGit状態確認を先に行う。
- #11は平地をparamsで検証したF1（H@2999から狭いgain DR）と、T1（L_angstd_w1の旋回設定で純旋回指令比率だけ0.35）の2本を並列実行する。F1はc06、T1は連続300 iterの事前規則を満たさなければ候補にしない。
- WRS cloneの未整理状態は、WRS側Codexが追跡docsだけを安全に復元してfast-forward同期する。未追跡物は残す。学習の前には各runの平地16 env再生コマンドを提示し、iteration 30後には実測終了見込み時刻・残り時間を報告する。

## 手を動かした場所

- 更新: `README.md`、`project_handbook.md`、`next_chat_briefing.md`。
- 追加: このチャット記録。

## 積み残し・次にやること

- WRS側Codexが既存cloneのGit状態をread-onlyで報告する。ユーザーが扱いを決め、実在する平地上書きとプリロード起動方法を確認してからF1/T1の64 envテスト、本番、評価を行う。
