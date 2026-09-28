"""DDJ-FLX4 の MIDI メッセージを「どの操作か」に変換する。

対応表は、実機で全部の操作を触って記録したログ(rekordbox 起動中)と、
Mixxx 同梱の FLX4 マッピングを突き合わせて作った。
名前に「(推定)」とある操作は、ログ上の位置から推測したもの。

使い方:
    decoder = FLX4Decoder()
    event = decoder.decode(msg)   # 変化がなければ None
    if event:
        print(event.control.name, event.value)
"""

from __future__ import annotations

from dataclasses import dataclass

import mido

# 操作の種類
BUTTON = "button"    # 押す/離す。value は 1.0(押した) か 0.0(離した)
PAD = "pad"          # パッド。value はボタンと同じ
KNOB = "knob"        # つまみ。value は 0.0〜1.0
FADER = "fader"      # フェーダー。value は 0.0〜1.0
JOG = "jog"          # ジョグ・ロータリー。value は回転量(正=時計回り)

# どちらの手で触るか
LEFT = "left"
RIGHT = "right"
EITHER = "either"


@dataclass(frozen=True)
class Control:
    id: str       # 例: "deck1.play", "mixer.crossfader"
    name: str     # 画面表示用の日本語名
    kind: str
    hand: str
    shift: bool = False


@dataclass(frozen=True)
class Event:
    control: Control
    value: float


# --- デッキ(ch1=左デッキ, ch2=右デッキ)のボタン: note 番号 -> (id, 名前, shift) ---
_DECK_NOTES = {
    11: ("play", "PLAY/PAUSE", False),
    12: ("cue", "CUE", False),
    14: ("play", "PLAY/PAUSE", True),
    16: ("loop_in", "LOOP IN / 4BEAT", False),
    17: ("loop_out", "LOOP OUT", False),
    27: ("mode_hotcue", "HOT CUE モード", False),
    30: ("mode_padfx", "PAD FX モード", False),
    32: ("mode_beatjump", "BEAT JUMP モード", False),
    34: ("mode_sampler", "SAMPLER モード", False),
    54: ("jog_touch", "ジョグ上面タッチ", False),
    61: ("call_right", "CUE/LOOP CALL ▶", True),
    62: ("call_left", "CUE/LOOP CALL ◀", True),
    63: ("shift", "SHIFT", False),
    72: ("cue", "CUE", True),
    76: ("loop_in", "LOOP IN / 4BEAT", True),
    77: ("reloop", "RELOOP/EXIT", False),
    78: ("loop_out", "LOOP OUT", True),
    80: ("reloop", "RELOOP/EXIT", True),
    81: ("call_left", "CUE/LOOP CALL ◀", False),
    83: ("call_right", "CUE/LOOP CALL ▶", False),
    88: ("sync", "BEAT SYNC", False),
    92: ("sync_long", "BEAT SYNC 長押し", False),
    96: ("sync", "BEAT SYNC", True),
    103: ("jog_touch", "ジョグ上面タッチ", True),
    105: ("mode_hotcue", "HOT CUE モード", True),
    107: ("mode_padfx", "PAD FX モード", True),
    109: ("mode_beatjump", "BEAT JUMP モード", True),
    111: ("mode_sampler", "SAMPLER モード", True),
}

# デッキの ch に乗ってくるが、物理的にはミキサーのチャンネル列にある操作
_STRIP_NOTES = {
    84: ("cue", "ヘッドホン CUE", False),
    104: ("cue", "ヘッドホン CUE", True),
    82: ("fader_start", "フェーダースタート(推定)", True),
    102: ("fader_start", "フェーダースタート(推定)", True),
}

# デッキの ch の CC: MSB 番号 -> (id, 名前, 種類, エリア)。LSB は MSB+32
_DECK_14BIT = {
    0: ("tempo", "テンポスライダー", FADER, "deck"),
    4: ("trim", "TRIM", KNOB, "strip"),
    7: ("eq_hi", "EQ HI", KNOB, "strip"),
    11: ("eq_mid", "EQ MID", KNOB, "strip"),
    15: ("eq_low", "EQ LOW", KNOB, "strip"),
    19: ("fader", "チャンネルフェーダー", FADER, "strip"),
}
_DECK_JOG = {
    33: ("jog_side", "ジョグ側面", False),
    34: ("jog_top", "ジョグ上面", False),
    35: ("jog_top", "ジョグ上面", False),
    41: ("jog_top", "ジョグ上面", True),
}

# パッド: note // 16 -> モード名(+SHIFT は ch がひとつ後ろ)
_PAD_MODES = {
    0: "HOT CUE",
    1: "PAD FX",
    2: "BEAT JUMP",
    3: "SAMPLER",
    4: "KEYBOARD",
    5: "PAD FX2",
    6: "BEAT LOOP",
    7: "KEY SHIFT",
}

# ミキサー(ch7)
_MIXER_14BIT = {
    5: ("mic_level", "MIC LEVEL", KNOB, EITHER),
    8: ("master_level", "MASTER LEVEL", KNOB, EITHER),
    12: ("hp_mix", "HEADPHONES MIXING", KNOB, EITHER),
    13: ("hp_level", "HEADPHONES LEVEL", KNOB, EITHER),
    23: ("ch1.cfx", "CFX(左チャンネル)", KNOB, LEFT),
    24: ("ch2.cfx", "CFX(右チャンネル)", KNOB, RIGHT),
    31: ("crossfader", "クロスフェーダー", FADER, EITHER),
}
_MIXER_ENCODERS = {
    64: ("browse", "ロータリーセレクター", False),
    100: ("browse", "ロータリーセレクター", True),
}
_MIXER_NOTES = {
    0: ("smart_cfx", "SMART CFX", False),
    8: ("smart_cfx", "SMART CFX", True),
    1: ("smart_fader", "SMART FADER", False),
    9: ("smart_fader", "SMART FADER", True),
    65: ("browse_press", "ロータリーセレクター押し", False),
    66: ("browse_press", "ロータリーセレクター押し", True),
    70: ("load1", "LOAD(左デッキ)", False),
    104: ("load1", "LOAD(左デッキ)", True),
    71: ("load2", "LOAD(右デッキ)", False),
    122: ("load2", "LOAD(右デッキ)", True),
    99: ("master_cue", "MASTER CUE(推定)", False),
    120: ("master_cue", "MASTER CUE(推定)", True),
}

# BEAT FX(ch5 / ch6)
_FX_NOTES = {
    16: ("fx_ch", "BEAT FX CH SELECT"),
    17: ("fx_ch", "BEAT FX CH SELECT"),
    18: ("fx_ch", "BEAT FX CH SELECT"),
    19: ("fx_ch", "BEAT FX CH SELECT"),
    20: ("fx_ch", "BEAT FX CH SELECT"),
    21: ("fx_ch", "BEAT FX CH SELECT"),
    67: ("fx_on", "BEAT FX ON/OFF"),
    71: ("fx_on", "BEAT FX ON/OFF"),
    74: ("fx_left", "BEAT ◀"),
    75: ("fx_right", "BEAT ▶"),
    99: ("fx_select", "BEAT FX SELECT"),
    100: ("fx_select", "BEAT FX SELECT"),
    102: ("fx_left", "BEAT ◀"),
    107: ("fx_right", "BEAT ▶"),
}
_FX_SHIFT_NOTES = {67, 100, 102, 107}

DECK_CHANNELS = {0: 1, 1: 2}
PAD_CHANNELS = {7: (1, False), 8: (1, True), 9: (2, False), 10: (2, True)}
MIXER_CHANNEL = 6
FX_CHANNELS = {4, 5}


def _deck_hand(deck: int) -> str:
    return LEFT if deck == 1 else RIGHT


def lookup(msg: mido.Message) -> tuple[Control, str] | None:
    """メッセージの操作と、値の解釈方法を返す。未知なら None。

    解釈方法: "note"(押す/離す), "msb", "lsb"(14bit の上位/下位), "relative"(回転量)
    """
    ch = getattr(msg, "channel", None)
    is_note = msg.type in ("note_on", "note_off")
    is_cc = msg.type == "control_change"
    if not (is_note or is_cc):
        return None

    if ch in DECK_CHANNELS:
        deck = DECK_CHANNELS[ch]
        hand = _deck_hand(deck)
        if is_note:
            if msg.note in _DECK_NOTES:
                key, name, shift = _DECK_NOTES[msg.note]
                kind = BUTTON
                return Control(f"deck{deck}.{key}", f"{name}({'左' if deck == 1 else '右'}デッキ)", kind, hand, shift), "note"
            if msg.note in _STRIP_NOTES:
                key, name, shift = _STRIP_NOTES[msg.note]
                return Control(f"mixer.ch{deck}.{key}", f"{name}(ch{deck})", BUTTON, hand, shift), "note"
            return None
        number = msg.control
        if number in _DECK_JOG:
            key, name, shift = _DECK_JOG[number]
            return Control(f"deck{deck}.{key}", f"{name}({'左' if deck == 1 else '右'}デッキ)", JOG, hand, shift), "relative"
        part = "msb" if number in _DECK_14BIT else "lsb" if number - 32 in _DECK_14BIT else None
        if part is None:
            return None
        key, name, kind, area = _DECK_14BIT[number if part == "msb" else number - 32]
        if area == "deck":
            control = Control(f"deck{deck}.{key}", f"{name}({'左' if deck == 1 else '右'}デッキ)", kind, hand)
        else:
            control = Control(f"mixer.ch{deck}.{key}", f"{name}(ch{deck})", kind, hand)
        return control, part

    if ch in PAD_CHANNELS and is_note:
        deck, shift = PAD_CHANNELS[ch]
        mode = _PAD_MODES.get(msg.note // 16)
        index = msg.note % 16 + 1
        if mode is None or index > 8:
            return None
        side = "左" if deck == 1 else "右"
        return (
            Control(f"deck{deck}.pad{index}", f"パッド{index} [{mode}]({side}デッキ)", PAD, _deck_hand(deck), shift),
            "note",
        )

    if ch == MIXER_CHANNEL:
        if is_note:
            if msg.note not in _MIXER_NOTES:
                return None
            key, name, shift = _MIXER_NOTES[msg.note]
            hand = LEFT if key == "load1" else RIGHT if key == "load2" else EITHER
            return Control(f"mixer.{key}", name, BUTTON, hand, shift), "note"
        number = msg.control
        if number in _MIXER_ENCODERS:
            key, name, shift = _MIXER_ENCODERS[number]
            return Control(f"mixer.{key}", name, JOG, EITHER, shift), "relative"
        part = "msb" if number in _MIXER_14BIT else "lsb" if number - 32 in _MIXER_14BIT else None
        if part is None:
            return None
        key, name, kind, hand = _MIXER_14BIT[number if part == "msb" else number - 32]
        return Control(f"mixer.{key}", name, kind, hand), part

    if ch in FX_CHANNELS:
        if is_note and msg.note in _FX_NOTES:
            key, name = _FX_NOTES[msg.note]
            return Control(f"fx.{key}", name, BUTTON, RIGHT, msg.note in _FX_SHIFT_NOTES), "note"
        if is_cc and msg.control in (2, 34):
            part = "msb" if msg.control == 2 else "lsb"
            return Control("fx.level", "BEAT FX LEVEL/DEPTH", KNOB, RIGHT), part
        return None

    return None


class FLX4Decoder:
    """MIDI メッセージを Event に変換する。

    - 14bit の値(フェーダー・つまみ)は上位と下位を組み合わせて 0.0〜1.0 にする
    - ジョグやロータリーは 64 を止まっている状態とした回転量にする
    - 値が変わっていないメッセージは捨てる。SMART CFX などを押したときに
      FLX4 が全部のつまみの現在値をまとめて送ってくるので、それで手が動かないようにするため
    """

    def __init__(self) -> None:
        self._msb: dict[str, int] = {}
        self._last: dict[str, float] = {}

    def decode(self, msg: mido.Message) -> Event | None:
        found = lookup(msg)
        if found is None:
            return None
        control, part = found

        if part == "note":
            pressed = msg.type == "note_on" and msg.velocity > 0
            value = 1.0 if pressed else 0.0
        elif part == "relative":
            value = float(msg.value - 64)
            if value == 0:
                return None
            return Event(control, value)
        elif part == "msb":
            self._msb[control.id] = msg.value
            return None
        else:  # lsb
            msb = self._msb.get(control.id)
            if msb is None:
                return None
            value = round((msb * 128 + msg.value) / 16383, 4)

        state_key = f"{control.id}{'+shift' if control.shift else ''}"
        if self._last.get(state_key) == value:
            return None
        self._last[state_key] = value
        return Event(control, value)
