# Unity でアバターに DJ の動きを仕込む手順

`python -m vrcdj.run` が送るパラメーター(`docs/avatar-parameters.md`)に合わせて、アバターの腕と手が動くようにします。
VRChat はデスクトップモード前提です。

いきなり全部作らず、**まず最小構成(待機・CUE・クロスフェーダーの 3 つ)を左右で作って、VRChat で動くところまで通す**のがおすすめです。仕組みが通ってから動作を増やす方が、つまずいたときに原因を探しやすくなります。

## 0. 準備するもの

- VRChat Creator Companion(VCC)で作ったアバターのプロジェクト(Unity 2022.3、VRChat SDK - Avatars 入り)
- **Modular Avatar**: 元のアバターを壊さずにレイヤーとパラメーターを追加するためのツール。VCC に Modular Avatar のリポジトリを追加してから、プロジェクトに入れます。
- **Gesture Manager**: Unity の Play モードでパラメーターを手で動かしてテストするためのツール。VCC からプロジェクトに入れます。
- ポーズを作るツール(次の「2」を参照)

作業前に、プロジェクトのフォルダをまるごとコピーしてバックアップしておいてください。

## 1. 卓の位置を決める

アバターの前に、FLX4 の代わりになる板を置きます。

1. Hierarchy でアバターの中に空の GameObject「DJ Motion」を作る
2. その中に Cube を作り、名前を「DJ Desk」にする
3. Scale を X 0.48 / Y 0.06 / Z 0.27 にする(FLX4 の幅・高さ・奥行きがおよそ 48cm × 6cm × 27cm)
4. アバターの腰の少し上、手を自然に前へ出した位置に置く

この板は、ポーズを作るときの目印です。アップロード時には Cube を非表示(または削除)にします。3D モデルとして卓を見せたい場合は、あとで本物に近いモデルに差し替えます。

## 2. ポーズを作る

VRChat のアバターは Humanoid なので、腕や指を動かすアニメーションは「マッスル」のカーブで作る必要があります。Unity の Animation ウィンドウで骨を直接回して録画しても、Humanoid の腕には効きません。

ポーズの作り方はどれか 1 つを選んでください。

- **Unity 用のポーズ編集アセットを使う**: VRChat 界隈では有料アセットの「Very Animation」がよく使われています。Unity 内で骨を回すだけでマッスルのカーブに変換してくれるので、一番手軽です。
- **Blender で作る**: アバターの FBX を Blender に読み込んでポーズを付け、FBX で書き出して Unity で Humanoid のアニメーションとして取り込みます。無料ですが手順は多めです。
- **Web カメラでモーションキャプチャする**: 待機のノリなど長めの動きに向いています。ボタンを押すような短い動きは手で作る方が早いです。

最小構成で作るポーズ(左手・右手それぞれ):

| ポーズ | 内容 |
|---|---|
| 待機 | デッキの上に軽く手をかざす |
| CUE を押す | 人差し指で CUE ボタン(デッキ左下)を押し込んだ瞬間 |
| クロスフェーダー左 | クロスフェーダーのつまみを左端でつまんでいる |
| クロスフェーダー右 | 同じく右端 |

左手はデッキ 1(左)、右手はデッキ 2(右)の位置で作ります。クロスフェーダーはどちらの手でも来るので、左右両方の手で作ります。

## 3. アニメーションクリップを作る

プロジェクトの Assets に「DJMotion」フォルダを作り、その中にクリップを作ります。

- **待機・フェーダーなどの止まったポーズ**: 1 フレームだけのクリップ(例: `L_Idle`, `L_XFader_Left`, `L_XFader_Right`)
- **ボタンを押す動き**: 「待機 → 押す → 待機」を 0.3 秒ほどでループさせるクリップ(例: `L_Cue`)。Loop Time にチェックを入れます。同じボタンを連打しても番号が変わらないため、ループにしておくと自然に見えます。

右手用も同じ名前の `R_` 版を作ります。

## 4. アバターマスクを作る

Assets を右クリック → Create → Avatar Mask で 2 つ作ります。

- `DJ_LeftArm`: Humanoid の図で**左腕と左手(IK は不要)だけ**を緑にして、ほかは全部赤
- `DJ_RightArm`: 右腕と右手だけを緑

これで、左手のレイヤーが右手や体を動かさなくなります。

## 5. Animator Controller を作る

Assets を右クリック → Create → Animator Controller で `DJ_Gesture` を作ります。

**パラメーター**(Animator ウィンドウの Parameters タブで追加。名前と型を正確に):

| 名前 | 型 | 初期値 |
|---|---|---|
| DJ_Active | Bool | false |
| DJ_HandL | Int | 0 |
| DJ_HandR | Int | 0 |
| DJ_ValueL | Float | 0.5 |
| DJ_ValueR | Float | 0.5 |
| DJ_XFader | Float | 0.5 |

**レイヤー「DJ Left」**(最初からある Base Layer を名前変更して使って大丈夫です)

1. レイヤーの歯車から Weight を 1、Mask を `DJ_LeftArm` にする
2. ステートを 4 つ作る
   - `Off`(Motion なし)
   - `Idle`(Motion: `L_Idle`)
   - `Cue`(Motion: `L_Cue`)
   - `XFader`(Motion: ブレンドツリー。右クリック → Create State → From New Blend Tree。中を 1D にして Parameter を `DJ_ValueL`、Motion に `L_XFader_Left`(Threshold 0)と `L_XFader_Right`(Threshold 1)を入れる)
3. `Off` をデフォルトステート(オレンジ)にする
4. 遷移を Any State から作る。すべて Has Exit Time のチェックを外し、Transition Duration を 0.1、**Can Transition To Self のチェックを外す**
   - Any State → `Off`: 条件 `DJ_Active` false
   - Any State → `Idle`: 条件 `DJ_Active` true、`DJ_HandL` Equals 0
   - Any State → `Cue`: 条件 `DJ_Active` true、`DJ_HandL` Equals 1
   - Any State → `XFader`: 条件 `DJ_Active` true、`DJ_HandL` Equals 11

**レイヤー「DJ Right」**: 同じものを右手用に作ります(Mask は `DJ_RightArm`、パラメーターは `DJ_HandR` / `DJ_ValueR`、クリップは `R_`)。

**Write Defaults について**: アバターの既存の Animator が Write Defaults をオンにしているかオフにしているかに合わせてください。Modular Avatar の設定で合わせることもできます(次の手順)。

## 6. Modular Avatar でアバターに組み込む

「DJ Motion」GameObject に次の 2 つのコンポーネントを追加します。

- **MA Merge Animator**
  - Animator: `DJ_Gesture`
  - Layer Type: **Gesture**
  - Path Mode: Absolute
  - Match Avatar Write Defaults: オン
- **MA Parameters**: 上の 6 つのパラメーターを追加し、すべて同期(Synced)にする。初期値は表のとおり。

これでアップロード時に、アバターの Gesture レイヤーと Expression Parameters に自動で追加されます。

## 7. Unity の中でテストする

1. Hierarchy に Gesture Manager を置いて Play を押す
2. Gesture Manager のパラメーター欄で `DJ_Active` をオン、`DJ_HandL` を 0 → 1 → 11 と変える
3. 11 のまま `DJ_ValueL` を 0〜1 に動かして、手が左右に動くか見る

ここで手が卓の上の正しい位置に来ていなければ、ポーズを直します。

## 8. VRChat で通しテスト

1. アバターをアップロードして、デスクトップモードで着る
2. VRChat の OSC がオンになっているか確認する(アバターを変えたあとは、Options → OSC → Reset Config をすると新しいパラメーターが認識されます)
3. PowerShell で本体を起動する

```powershell
.venv\Scripts\Activate.ps1
python -m vrcdj.run --verbose
```

4. FLX4 で CUE を押したり、クロスフェーダーを動かしたりして、鏡でアバターを確認する

## 9. 動作を増やす

最小構成で動いたら、`docs/avatar-parameters.md` の動作番号表を見ながら、PLAY(2)、ジョグ(3)、つまみ(4)、チャンネルフェーダー(5)… と 1 つずつステートを足していきます。Value を使う動作(3・4・5・6・11)はブレンドツリー、それ以外はループするクリップです。

表情(`DJ_Emote`)は、FX レイヤー用に別の Animator Controller を作り、もう 1 つの MA Merge Animator(Layer Type: FX)で組み込みます。`DJ_Emote` の番号ごとに表情のブレンドシェイプを付けたステートを作ります。

うまく動かないときは、Gesture Manager の画面か、PowerShell の `--verbose` の表示をスレッドに貼ってください。

## よくあるつまずき

- **DJ_Active をオフにしても腕が固まったまま**: Write Defaults がオフのアバターでは、空の `Off` ステートに入っても直前のポーズが残ります。`Off` ステートに VRC Animator Layer Control を付けて、このレイヤーの Weight を 0 にしてください(`Idle` などには Weight 1 に戻す Layer Control を付けます)。
- **VRChat でパラメーターが届かない**: OSC の設定ファイルが古いアバターのままのことがあります。OSC の Reset Config をしてから、アバターを着直してください。
