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

Assets を右クリック → Create → Avatar Mask で 3 つ作ります。

- `DJ_LeftArm`: Humanoid の図で**左腕と左手(IK は不要)だけ**を緑にして、ほかは全部赤。肩から肘・手首までの「腕」の部分と、その先の「手」の部分は別々にクリックするので、両方とも緑になっているか確認します
- `DJ_RightArm`: 右腕と右手だけを緑
- `DJ_None`: 全部赤(IK の丸も赤)。何も動かさない身代わりのレイヤー用です

## 5. Animator Controller を作る

DJ の動きは、VRChat のエモートと同じ **Action レイヤー**に入れます。Action は使っていないときに重みを 0 にでき、そのときは元の歩き・待機の動きに完全に戻ります。Gesture レイヤーに腕を入れると、DJ オフのときに腕が固まるので使いません。

Assets を右クリック → Create → Animator Controller で `DJ_Gesture` を作ります(名前は Gesture ですが、組み込み先は Action です)。

**パラメーター**(Animator ウィンドウの Parameters タブで追加。名前と型を正確に):

| 名前 | 型 | 初期値 |
|---|---|---|
| DJ_Active | Bool | false |
| DJ_HandL | Int | 0 |
| DJ_HandR | Int | 0 |
| DJ_ValueL | Float | 0.5 |
| DJ_ValueR | Float | 0.5 |
| DJ_XFader | Float | 0.5 |

**レイヤーは上から次の順に並べます。** Layer Control で指定する番号は、上から 0, 1, 2… です。

| 番号 | レイヤー | Weight | Mask | 中身 |
|---|---|---|---|---|
| 0 | DJ None | 1(変えられない) | `DJ_None` | ステートなし |
| 1 | DJ Body | 0 | なし | `Stand` ステート 1 つ |
| 2 | DJ Left | 0 | `DJ_LeftArm` | 下の 4 ステート |
| 3 | DJ Right | 0 | `DJ_RightArm` | DJ Left の右手版 |

一番上のレイヤーは Weight を変えられないので、何も動かさない「DJ None」を身代わりに置きます。

**レイヤー「DJ Body」**(DJ 中の体の土台)

- ステート `Stand` を 1 つ作り、Motion に `proxy_stand_still` を入れる。Project の検索欄で検索範囲を **All**(または In Packages)にすると、VRChat SDK の中に見つかります。VRChat の標準の立ち姿(軽く呼吸する)に置き換わります。自作の立ちポーズだと、記録が足りないと手足を少し曲げた不自然な姿勢になります

**レイヤー「DJ Left」**

1. ステートを 4 つ作る
   - `Off`(Motion: `L_Idle`。空にすると SDK が警告を出すのと、DJ オフにしたとき手がなめらかに戻るため)
   - `Idle`(Motion: `L_Idle`)
   - `Cue`(Motion: `L_Cue`)
   - `XFader`(Motion: ブレンドツリー。右クリック → Create State → From New Blend Tree。中を 1D にして Parameter を `DJ_ValueL`、Motion に `L_XFader_Left`(Threshold 0)と `L_XFader_Right`(Threshold 1)を入れる)
2. `Off` をデフォルトステート(オレンジ)にする
3. 遷移を Any State から作る。すべて Has Exit Time のチェックを外し、Transition Duration を 0.1、**Can Transition To Self のチェックを外す**
   - Any State → `Off`: 条件 `DJ_Active` false
   - Any State → `Idle`: 条件 `DJ_Active` true、`DJ_HandL` Equals 0
   - Any State → `Cue`: 条件 `DJ_Active` true、`DJ_HandL` Equals 1
   - Any State → `XFader`: 条件 `DJ_Active` true、`DJ_HandL` Equals 11
4. ステートに Behaviour を付ける(Inspector の Add Behaviour から)
   - **`Off`**
     - VRC Animator Tracking Control: **全部 Tracking**
     - VRC Playable Layer Control: Layer **Action**、Goal Weight **0**、Blend Duration **0.2**
     - VRC Animator Layer Control: Playable **Action**、Layer **1**、Goal Weight **0**(DJ Right を作ったら Layer **3** の分も追加)
     - VRC Animator Layer Control: Playable **Action**、Layer **2**、Goal Weight **0**
   - **`Off` 以外(`Idle`・`Cue`・`XFader`)**
     - VRC Animator Tracking Control: **Hip・Left Foot・Right Foot・Left Hand・Right Hand・Left Fingers・Right Fingers** を **Animation**(Head・Eyes・Mouth は Tracking のまま)
     - 上の 3 つ(DJ Right があれば 4 つ)の Layer Control を同じように付け、Goal Weight を **1**、Blend Duration を **0.1** にする

**レイヤー「DJ Right」**: 同じものを右手用に作ります(Mask は `DJ_RightArm`、パラメーターは `DJ_HandR` / `DJ_ValueR`、クリップは `R_`)。Behaviour は DJ Left と同じ内容にします。どちらの手のステートからでも、DJ のオン・オフで全レイヤーがそろって切り替わるようにするためです。

DJ 中は体全体を Action が受け持つので、歩いても足は動きません(卓の前に立っている前提です)。

## 6. Modular Avatar でアバターに組み込む

VRC Avatar Descriptor の Playable Layers(Base・Gesture など)は、アバター付属のままにしておきます。DJ 用に書き換える必要はありません。

「DJ Motion」GameObject に次の 2 つのコンポーネントを追加します。

- **MA Merge Animator**
  - Animator to merge: `DJ_Gesture`
  - Layer Type: **Action**
  - Path Mode: Absolute
  - Match Avatar Write Defaults: オフ
- **MA Parameters**: 上の 6 つのパラメーターを追加し、すべて **Synced にして、Saved のチェックは外す**。初期値は表のとおり(`DJ_Active` はオフ)。Saved がオンだと、前回 DJ オンのままアバターを着替えたとき、次に着た直後から DJ オンになってしまいます。

これでアップロード時に、アバターの Action レイヤーと Expression Parameters に自動で追加されます。

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

- **指だけ動いて腕が動かない**: アバターマスクで腕の部分が赤のままになっているか、ステートに VRC Animator Tracking Control(Left Hand を Animation)が付いていません。手順「4」と「5」を確認してください。
- **DJ オフのときに腕が固まる・歩いても腕が振れない**: MA Merge Animator の Layer Type が Gesture のままになっていないか確認してください。Gesture に入れると、オフのときに腕を元の動きへ戻せません。Action にします。
- **DJ オフにしても DJ の立ち姿のまま**: `Off` ステートに VRC Playable Layer Control(Action、Goal Weight 0)が付いているか確認してください。
- **アバターを着た直後から DJ オンになっている**: MA Parameters で DJ のパラメーターの Saved がオンになっています。外して発行し直してください。すぐ直したいときは、本体を起動して Ctrl+C で止めると `DJ_Active` がオフで送られます。
- **DJ 中に左手以外が手足を少し曲げた姿勢になる**: `Stand` の Motion が自作の立ちポーズになっています。`proxy_stand_still` に替えてください。
- **アップロード画面に「Write Defaults disabled ... missing or empty」の警告が出る**: 発行は止まらない注意書きです。DJ のレイヤーなら、`Off` ステートに `L_Idle` を入れると消えます。アバター付属のレイヤーが原因のこともあり、その場合は放っておいて大丈夫です。**Auto Fix は押さないでください**。設定を勝手に書き換え、かえって動かなくなることがあります。
- **VRChat でパラメーターが届かない**: OSC の設定ファイルが古いアバターのままのことがあります。OSC の Reset Config をしてから、アバターを着直してください。
