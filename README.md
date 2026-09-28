# vrc-dj-motion

DDJ-FLX4 の MIDI 入力に合わせて、VRChat アバターを OSC で「それっぽく」動かすためのプログラムです。
VRChat はデスクトップモード、DJ ソフトは rekordbox(予備に Mixxx)を想定しています。

今入っているもの:

- `vrcdj.run`: 本体。FLX4 の操作に合わせてアバターパラメーターを VRChat に送る
- `vrcdj.monitor`: FLX4 から届く MIDI を表示・記録する
- `vrcdj.osctest`: VRChat に OSC を送る、VRChat から届く OSC を表示する
- `vrcdj.flx4`: FLX4 の MIDI を「どの操作か」に変換する(一覧は [docs/flx4-controls.md](docs/flx4-controls.md))

`vrcdj.monitor` は、FLX4 の操作名も一緒に表示します。

## セットアップ(Windows 11)

1. [Python 3.12](https://www.python.org/downloads/) をインストール(「Add python.exe to PATH」にチェック)
   - MIDI ライブラリ(python-rtmidi)が Windows 向けに配布しているのは Python 3.12 までです。3.13 以降だとインストールでエラーになります。
2. このリポジトリを取得して、フォルダで PowerShell を開く
3. 必要なライブラリを入れる

```powershell
py -3.12 -m venv .venv
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

## 本体を動かす

アバター側に `docs/avatar-parameters.md` のパラメーターを用意してから使います。

```powershell
python -m vrcdj.run --verbose
```

VRChat やアバターの準備がまだでも、次の方法で動きを確認できます。

```powershell
python -m vrcdj.run --dry-run --verbose --show-controls   # 送らずに表示だけ
python -m vrcdj.run --replay logs\midi-xxxx.jsonl --dry-run --verbose   # 記録したログを再生
```

アバターに届いているかは、別の PowerShell で `python -m vrcdj.osctest listen` を動かすと、VRChat から返ってくる値で確認できます。

## テスト(開発用)

```powershell
pip install pytest
python -m pytest
```
