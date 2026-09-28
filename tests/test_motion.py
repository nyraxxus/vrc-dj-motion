import mido

from vrcdj.flx4 import FLX4Decoder
from vrcdj.motion import ACTIONS, BUTTON_HOLD, CONTINUOUS_TIMEOUT, EMOTE_HOLD, MotionEngine


def cc(ch, control, value):
    return mido.Message("control_change", channel=ch, control=control, value=value)


def note(ch, n, velocity=127):
    return mido.Message("note_on", channel=ch, note=n, velocity=velocity)


class Rig:
    def __init__(self):
        self.decoder = FLX4Decoder()
        self.engine = MotionEngine()

    def feed(self, msg, now):
        event = self.decoder.decode(msg)
        if event:
            self.engine.handle(event, now)

    def params(self, now):
        return self.engine.params(now)


def test_idle_state():
    p = Rig().params(0.0)
    assert p["DJ_HandL"] == 0 and p["DJ_HandR"] == 0 and p["DJ_Emote"] == 0 and p["DJ_Active"] is True


def test_button_holds_minimum_time_then_returns_to_idle():
    rig = Rig()
    rig.feed(note(0, 12), 1.0)          # 左デッキ CUE を押す
    rig.feed(note(0, 12, 0), 1.05)      # すぐ離す
    assert rig.params(1.05)["DJ_HandL"] == ACTIONS["cue"]
    assert rig.params(1.0 + BUTTON_HOLD - 0.01)["DJ_HandL"] == ACTIONS["cue"]
    assert rig.params(1.0 + BUTTON_HOLD + 0.01)["DJ_HandL"] == 0


def test_right_deck_uses_right_hand():
    rig = Rig()
    rig.feed(note(1, 11), 1.0)
    p = rig.params(1.0)
    assert p["DJ_HandR"] == ACTIONS["play"] and p["DJ_HandL"] == 0


def test_fader_sends_position_and_times_out():
    rig = Rig()
    rig.feed(cc(1, 19, 127), 1.0)
    rig.feed(cc(1, 51, 127), 1.0)       # ch2 のチャンネルフェーダーを一番上に
    p = rig.params(1.0)
    assert p["DJ_HandR"] == ACTIONS["fader"] and p["DJ_ValueR"] == 1.0
    assert rig.params(1.0 + CONTINUOUS_TIMEOUT + 0.01)["DJ_HandR"] == 0


def test_crossfader_goes_to_free_hand_and_sets_xfader():
    rig = Rig()
    rig.feed(note(0, 11), 1.0)          # 左手は PLAY 中
    rig.feed(cc(6, 31, 0), 1.1)
    rig.feed(cc(6, 63, 0), 1.1)
    p = rig.params(1.1)
    assert p["DJ_HandR"] == ACTIONS["crossfader"] and p["DJ_XFader"] == 0.0
    assert p["DJ_HandL"] == ACTIONS["play"]


def test_same_either_control_stays_on_same_hand():
    rig = Rig()
    rig.feed(cc(6, 31, 64), 1.0)
    rig.feed(cc(6, 63, 0), 1.0)
    first = "DJ_HandL" if rig.params(1.0)["DJ_HandL"] == ACTIONS["crossfader"] else "DJ_HandR"
    rig.feed(cc(6, 31, 100), 1.2)
    rig.feed(cc(6, 63, 0), 1.2)
    p = rig.params(1.2)
    assert p[first] == ACTIONS["crossfader"]
    other = "DJ_HandR" if first == "DJ_HandL" else "DJ_HandL"
    assert p[other] == 0


def test_jog_value_reflects_direction():
    rig = Rig()
    rig.feed(cc(0, 33, 70), 1.0)        # 側面を時計回りに速く
    p = rig.params(1.0)
    assert p["DJ_HandL"] == ACTIONS["jog"] and p["DJ_ValueL"] > 0.5
    rig.feed(cc(0, 33, 60), 1.1)
    assert rig.params(1.1)["DJ_ValueL"] < 0.5


def test_sampler_pad_sets_emote():
    rig = Rig()
    rig.feed(note(9, 50), 1.0)          # 右デッキ SAMPLER パッド3
    p = rig.params(1.0)
    assert p["DJ_Emote"] == 11 and p["DJ_HandR"] == ACTIONS["pad"]
    assert rig.params(1.0 + EMOTE_HOLD + 0.01)["DJ_Emote"] == 0


def test_hot_cue_pad_does_not_set_emote():
    rig = Rig()
    rig.feed(note(7, 2), 1.0)
    p = rig.params(1.0)
    assert p["DJ_Emote"] == 0 and p["DJ_HandL"] == ACTIONS["pad"]


def test_shift_alone_does_not_move():
    rig = Rig()
    rig.feed(note(0, 63), 1.0)
    assert rig.params(1.0)["DJ_HandL"] == 0
