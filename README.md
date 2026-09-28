# vrc-dj-motion

DDJ-FLX4 の MIDI 入力に合わせて、VRChat アバターを OSC で「それっぽく」動かすためのプログラムです。
VRChat はデスクトップモード、DJ ソフトは rekordbox(予備に Mixxx)を想定しています。

今入っているのは、本体を作る前の確認用ツール 2 つです。

- `vrcdj.monitor`: FLX4 から届く MIDI を表示・記録する
- `vrcdj.osctest`: VRChat に OSC を送る、VRChat から届く OSC を表示する

## セットアップ(Windows 11)

1. [Python 3.11 以上](https://www.python.org/downloads/) をインストール(「Add python.exe to PATH」にチェック)
2. このリポジトリを取得して、フォルダで PowerShell を開く
3. 必要なライブラリを入れる

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`Activate.ps1` の実行でエラーが出たら、先に `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` を 1 回だけ実行してください。

## 確認 1: rekordbox と同時に FLX4 の MIDI を読めるか

これがこのプロジェクトで一番大事な確認です。

1. FLX4 を接続して rekordbox を起動し、普通に操作できる状態にする
2. PowerShell で次を実行する

```powershell
python -m vrcdj.monitor --list   # ポート一覧。DDJ-FLX4 が出ればOK
python -m vrcdj.monitor --log    # FLX4 を開いて表示・記録
```

3. FLX4 のボタンやフェーダーを触って、画面に行が流れること、rekordbox も普通に反応することを確認する

結果の見方:

- 両方動く → rekordbox で進められます
- 「ポートを開けませんでした」と出る → rekordbox が FLX4 を独占しています。Windows Update で「Windows MIDI Services」が入っているか確認し、ダメなら Mixxx での中継方式に切り替えます

`--log` を付けると `logs/` に記録が残ります。全部のボタン・つまみ・フェーダー・ジョグ・パッドを 1 回ずつ順番に触ったログがあると、次の段階で操作と動きの対応表を作れます。

## 確認 2: VRChat に OSC が届くか

1. VRChat を起動し、アクションメニュー → Options → OSC → Enabled をオンにする
2. 次を実行して、チャットボックスに文字が出れば OK(アバター改変は不要)

```powershell
python -m vrcdj.osctest chatbox "OSCテスト"
```

3. VRChat からの送信も見たい場合は、次を実行してから表情を変えたりする

```powershell
python -m vrcdj.osctest listen
```

アバターパラメーターを直接送ることもできます(アバター側にパラメーターを作ってから使います)。

```powershell
python -m vrcdj.osctest param DJ_HandL 1      # 整数
python -m vrcdj.osctest param DJ_XFader 0.5   # 小数
python -m vrcdj.osctest param DJ_Active true  # true / false
```

## テスト(開発用)

```powershell
pip install pytest
python -m pytest
```
