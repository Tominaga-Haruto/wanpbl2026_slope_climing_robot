# D7 一括原点設定コマンド

## 変更

`C:\Users\harut\Connect2USB2CAN\d7_origin_console.py` に `oa` コマンドを追加した。

実行手順は `scan 3` → `oa` → `YES ALL 10`。10軸の経路確定、フィードバック新鮮性、`err=0`、サーボ形式を確認してから、全軸へ `kind=0` の原点設定を順番に送る。確認文字列が一致しない場合は送信しない。途中で状態が古くなった場合は残りを送らず停止する。

## 確認

`python -m py_compile d7_origin_console.py` を実行し、構文エラーがないことを確認した。実機では未実行。
