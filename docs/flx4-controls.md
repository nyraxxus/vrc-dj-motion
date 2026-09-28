# DDJ-FLX4 操作一覧

`vrcdj/flx4.py` が解読する操作の一覧です。2026-09-28 に実機(rekordbox 7.2.18 起動中)で全操作を触ったログと、Mixxx の FLX4 マッピングを突き合わせて作りました。「(推定)」はログ上の位置から推測した名前です。

MIDI ch は 1 から数えた番号です(プログラム内部は 0 から)。値の種類: ボタン=押す/離す、つまみ・フェーダー=0.0〜1.0、ジョグ・ロータリー=回転量。

## デッキ(左デッキ ch1 / 右デッキ ch2)

| 操作 | note | SHIFT |
|---|---|---|
| PLAY/PAUSE | 11 |  |
| CUE | 12 |  |
| PLAY/PAUSE | 14 | ○ |
| LOOP IN / 4BEAT | 16 |  |
| LOOP OUT | 17 |  |
| HOT CUE モード | 27 |  |
| PAD FX モード | 30 |  |
| BEAT JUMP モード | 32 |  |
| SAMPLER モード | 34 |  |
| ジョグ上面タッチ | 54 |  |
| CUE/LOOP CALL ▶ | 61 | ○ |
| CUE/LOOP CALL ◀ | 62 | ○ |
| SHIFT | 63 |  |
| CUE | 72 | ○ |
| LOOP IN / 4BEAT | 76 | ○ |
| RELOOP/EXIT | 77 |  |
| LOOP OUT | 78 | ○ |
| RELOOP/EXIT | 80 | ○ |
| CUE/LOOP CALL ◀ | 81 |  |
| CUE/LOOP CALL ▶ | 83 |  |
| BEAT SYNC | 88 |  |
| BEAT SYNC 長押し | 92 |  |
| BEAT SYNC | 96 | ○ |
| ジョグ上面タッチ | 103 | ○ |
| HOT CUE モード | 105 | ○ |
| PAD FX モード | 107 | ○ |
| BEAT JUMP モード | 109 | ○ |
| SAMPLER モード | 111 | ○ |

| 操作 | CC | 種類 |
|---|---|---|
| テンポスライダー | 0 / 32 | 14bit |
| ジョグ側面 | 33 | 回転量(64=停止) |
| ジョグ上面 | 34 | 回転量(64=停止) |
| ジョグ上面 | 35 | 回転量(64=停止) |
| ジョグ上面 +SHIFT | 41 | 回転量(64=停止) |

## パッド

左デッキ ch8(SHIFT 中は ch9)、右デッキ ch10(SHIFT 中は ch11)。note = モード番号×16 + パッド番号(0〜7)。

| モード | note |
|---|---|
| HOT CUE | 0〜7 |
| PAD FX | 16〜23 |
| BEAT JUMP | 32〜39 |
| SAMPLER | 48〜55 |
| KEYBOARD | 64〜71 |
| PAD FX2 | 80〜87 |
| BEAT LOOP | 96〜103 |
| KEY SHIFT | 112〜119 |

## ミキサーのチャンネル列(ch1 列は MIDI ch1、ch2 列は MIDI ch2)

| 操作 | 番号 | 種類 |
|---|---|---|
| TRIM | CC 4 / 36 | 14bit |
| EQ HI | CC 7 / 39 | 14bit |
| EQ MID | CC 11 / 43 | 14bit |
| EQ LOW | CC 15 / 47 | 14bit |
| チャンネルフェーダー | CC 19 / 51 | 14bit |
| フェーダースタート(推定) +SHIFT | note 82 | ボタン |
| ヘッドホン CUE | note 84 | ボタン |
| フェーダースタート(推定) +SHIFT | note 102 | ボタン |
| ヘッドホン CUE +SHIFT | note 104 | ボタン |

## ミキサー(ch7)

| 操作 | 番号 | 種類 |
|---|---|---|
| MIC LEVEL | CC 5 / 37 | 14bit |
| MASTER LEVEL | CC 8 / 40 | 14bit |
| HEADPHONES MIXING | CC 12 / 44 | 14bit |
| HEADPHONES LEVEL | CC 13 / 45 | 14bit |
| CFX(左チャンネル) | CC 23 / 55 | 14bit |
| CFX(右チャンネル) | CC 24 / 56 | 14bit |
| クロスフェーダー | CC 31 / 63 | 14bit |
| ロータリーセレクター | CC 64 | 回転量 |
| ロータリーセレクター +SHIFT | CC 100 | 回転量 |
| SMART CFX | note 0 | ボタン |
| SMART FADER | note 1 | ボタン |
| SMART CFX +SHIFT | note 8 | ボタン |
| SMART FADER +SHIFT | note 9 | ボタン |
| ロータリーセレクター押し | note 65 | ボタン |
| ロータリーセレクター押し +SHIFT | note 66 | ボタン |
| LOAD(左デッキ) | note 70 | ボタン |
| LOAD(右デッキ) | note 71 | ボタン |
| MASTER CUE(推定) | note 99 | ボタン |
| LOAD(左デッキ) +SHIFT | note 104 | ボタン |
| MASTER CUE(推定) +SHIFT | note 120 | ボタン |
| LOAD(右デッキ) +SHIFT | note 122 | ボタン |

## BEAT FX(ch5 / ch6)

| 操作 | 番号 |
|---|---|
| BEAT FX CH SELECT | note 16 |
| BEAT FX CH SELECT | note 17 |
| BEAT FX CH SELECT | note 18 |
| BEAT FX CH SELECT | note 19 |
| BEAT FX CH SELECT | note 20 |
| BEAT FX CH SELECT | note 21 |
| BEAT FX ON/OFF +SHIFT | note 67 |
| BEAT FX ON/OFF | note 71 |
| BEAT ◀ | note 74 |
| BEAT ▶ | note 75 |
| BEAT FX SELECT | note 99 |
| BEAT FX SELECT +SHIFT | note 100 |
| BEAT ◀ +SHIFT | note 102 |
| BEAT ▶ +SHIFT | note 107 |
| BEAT FX LEVEL/DEPTH | CC 2 / 34 |

## 解読しないもの

SMART CFX などを押したとき、FLX4 はつまみやスイッチの現在値をまとめて送ってきます。その中の BEAT FX 内部状態(ch5/6 の CC 3・4・80〜82・100〜102 など)は操作ではないので無視します。値が変わっていないメッセージも捨てるので、まとめ送りでアバターの手が動くことはありません。
