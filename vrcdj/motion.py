"""FLX4 の操作をアバターパラメーターに変換する。

考え方:
- 左手・右手それぞれに「今やっている動作」(DJ_HandL / DJ_HandR の番号)を持つ
- ボタンは押した瞬間に動作を始め、最低 BUTTON_HOLD 秒は保つ(同期に乗る長さにするため)
- つまみ・フェーダー・ジョグは触っている間ずっとその動作で、値を DJ_ValueL / DJ_ValueR に入れる
- しばらく何も触らなければ待機(0)に戻る
- どちらの手でもよい操作(クロスフェーダーなど)は、長く空いている方の手に振る
- SAMPLER モードのパッドは表情・特殊動作(DJ_Emote)に使う

アバター側で必要なパラメーターは docs/avatar-parameters.md を参照。
"""

from __future__ import annotations

from dataclasses import dataclass

from vrcdj.flx4 import JOG, KNOB, LEFT, RIGHT, Event

# アバターパラメーター名
P_HAND = {LEFT: "DJ_HandL", RIGHT: "DJ_HandR"}
P_VALUE = {LEFT: "DJ_ValueL", RIGHT: "DJ_ValueR"}
P_XFADER = "DJ_XFader"
P_EMOTE = "DJ_Emote"
P_ACTIVE = "DJ_Active"

# 手の動作番号(DJ_HandL / DJ_HandR の値)
ACTIONS = {
    "idle": 0,
    "cue": 1,         # CUE ボタン
    "play": 2,        # PLAY/PAUSE ボタン
    "jog": 3,         # ジョグを回す(Value: 0.5=停止、0/1 に近いほど速い)
    "knob": 4,        # つまみ(TRIM・EQ・CFX・レベル類。Value=つまみの位置)
    "fader": 5,       # チャンネルフェーダー(Value=位置)
    "tempo": 6,       # テンポスライダー(Value=位置)
    "loop": 7,        # LOOP IN/OUT・RELOOP・CUE/LOOP CALL
    "sync": 8,        # BEAT SYNC
    "pad": 9,         # パッドを叩く
    "browse": 10,     # ロータリーセレクター・LOAD
    "crossfader": 11, # クロスフェーダー(Value=位置)
    "fx": 12,         # BEAT FX 周り
    "mode": 13,       # パッドモード切り替えボタン
    "button": 14,     # その他のボタン
}

BUTTON_HOLD = 0.35         # ボタン動作を最低これだけ保つ(秒)
CONTINUOUS_TIMEOUT = 0.6   # つまみ等を最後に触ってから待機に戻るまで(秒)
EMOTE_HOLD = 2.0           # パッドで出した表情を保つ(秒)
JOG_SCALE = 0.08           # ジョグの回転量 1 あたりの Value の振れ幅

_CONTINUOUS = {"jog", "knob", "fader", "tempo", "crossfader"}


def classify(event: Event) -> str | None:
    """操作を手の動作名に分類する。動かさない操作は None。"""
    control = event.control
    key = control.id.split(".")[-1]
    if key in ("shift", "fader_start"):
        return None
    if control.id.startswith("fx."):
        return "knob" if key == "level" else "fx"
    if key.startswith("pad"):
        return "pad"
    if key.startswith("mode_"):
        return "mode"
    if control.kind == JOG and key == "browse":
        return "browse"
    if control.kind == JOG or key == "jog_touch":
        return "jog"
    if control.id.startswith("deck"):
        if key == "cue":
            return "cue"
        if key == "play":
            return "play"
        if key == "tempo":
            return "tempo"
        if key in ("loop_in", "loop_out", "reloop", "call_left", "call_right"):
            return "loop"
        if key in ("sync", "sync_long"):
            return "sync"
        return "button"
    # ミキサー
    if key == "crossfader":
        return "crossfader"
    if key == "fader":
        return "fader"
    if key in ("browse_press", "load1", "load2"):
        return "browse"
    if control.kind == KNOB:
        return "knob"
    return "button"


@dataclass
class _Hand:
    action: str = "idle"
    control_id: str = ""
    value: float = 0.5
    until: float = 0.0
    last_used: float = -1.0


class MotionEngine:
    def __init__(self) -> None:
        self.hands = {LEFT: _Hand(), RIGHT: _Hand()}
        self.xfader = 0.5
        self.emote = 0
        self.emote_until = 0.0

    # --- 入力 ---

    def handle(self, event: Event, now: float) -> None:
        action = classify(event)
        if action is None:
            return

        control = event.control
        if control.id.endswith("crossfader") and control.kind != JOG:
            self.xfader = event.value

        if action == "pad" and "SAMPLER" in control.name and event.value > 0:
            deck = 1 if control.id.startswith("deck1") else 2
            index = int(control.id.split("pad")[-1])
            self.emote = index + (0 if deck == 1 else 8)
            self.emote_until = now + EMOTE_HOLD

        hand_name = self._pick_hand(control.hand, control.id, now)
        hand = self.hands[hand_name]

        if action in _CONTINUOUS:
            if action == "jog":
                if control.kind == JOG:
                    hand.value = min(1.0, max(0.0, 0.5 + event.value * JOG_SCALE))
                elif event.value == 0:  # ジョグから手を離した
                    if hand.action == "jog":
                        hand.until = min(hand.until, now + BUTTON_HOLD)
                    return
                else:  # ジョグに手を乗せた
                    hand.value = 0.5
            else:
                hand.value = event.value
            hand.action = action
            hand.control_id = control.id
            hand.until = now + CONTINUOUS_TIMEOUT
            hand.last_used = now
            return

        # ボタン類: 押したときだけ動作を始める。離したときは何もしない
        if event.value <= 0:
            return
        hand.action = action
        hand.control_id = control.id
        hand.until = now + BUTTON_HOLD
        hand.last_used = now

    def _pick_hand(self, preferred: str, control_id: str, now: float) -> str:
        if preferred in (LEFT, RIGHT):
            return preferred
        # すでにこの操作をしている手があればそのまま
        for name, hand in self.hands.items():
            if hand.control_id == control_id and hand.until > now:
                return name
        # 空いている手、両方空いていれば長く使っていない方
        left, right = self.hands[LEFT], self.hands[RIGHT]
        left_free, right_free = left.until <= now, right.until <= now
        if left_free != right_free:
            return LEFT if left_free else RIGHT
        return LEFT if left.last_used < right.last_used else RIGHT

    # --- 出力 ---

    def params(self, now: float) -> dict[str, bool | int | float]:
        """今この瞬間にアバターへ送るべき値。"""
        out: dict[str, bool | int | float] = {P_ACTIVE: True, P_XFADER: round(self.xfader, 3)}
        for name, hand in self.hands.items():
            if hand.until <= now and hand.action != "idle":
                hand.action = "idle"
                hand.control_id = ""
            out[P_HAND[name]] = ACTIONS[hand.action]
            out[P_VALUE[name]] = round(hand.value, 3) if hand.action in _CONTINUOUS else 0.5
        if self.emote and self.emote_until <= now:
            self.emote = 0
        out[P_EMOTE] = self.emote
        return out
