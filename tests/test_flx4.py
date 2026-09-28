import mido

from vrcdj.flx4 import BUTTON, FADER, JOG, KNOB, LEFT, PAD, RIGHT, FLX4Decoder, lookup


def cc(ch, control, value):
    return mido.Message("control_change", channel=ch, control=control, value=value)


def note(ch, n, velocity=127):
    return mido.Message("note_on", channel=ch, note=n, velocity=velocity)


def test_deck_buttons():
    control, _ = lookup(note(0, 11))
    assert control.id == "deck1.play" and control.kind == BUTTON and control.hand == LEFT
    control, _ = lookup(note(1, 12))
    assert control.id == "deck2.cue" and control.hand == RIGHT
    control, _ = lookup(note(1, 72))
    assert control.id == "deck2.cue" and control.shift


def test_channel_strip_is_mixer_but_keeps_its_side():
    control, part = lookup(cc(0, 7, 64))
    assert control.id == "mixer.ch1.eq_hi" and control.kind == KNOB and control.hand == LEFT
    assert part == "msb"
    control, _ = lookup(note(1, 84))
    assert control.id == "mixer.ch2.cue" and control.hand == RIGHT


def test_pads_modes_and_shift():
    control, _ = lookup(note(7, 50))
    assert control.id == "deck1.pad3" and control.kind == PAD and "SAMPLER" in control.name
    control, _ = lookup(note(10, 99))
    assert control.id == "deck2.pad4" and control.shift and "BEAT LOOP" in control.name


def test_fader_combines_14bit_value():
    decoder = FLX4Decoder()
    assert decoder.decode(cc(6, 31, 127)) is None  # MSB だけではまだ出さない
    event = decoder.decode(cc(6, 63, 127))
    assert event.control.id == "mixer.crossfader" and event.control.kind == FADER
    assert event.value == 1.0
    decoder.decode(cc(6, 31, 64))
    assert decoder.decode(cc(6, 63, 0)).value == round(64 * 128 / 16383, 4)


def test_jog_is_relative():
    decoder = FLX4Decoder()
    event = decoder.decode(cc(0, 33, 65))
    assert event.control.id == "deck1.jog_side" and event.control.kind == JOG and event.value == 1
    assert decoder.decode(cc(0, 33, 63)).value == -1
    assert decoder.decode(cc(0, 33, 64)) is None


def test_unchanged_values_are_dropped():
    decoder = FLX4Decoder()
    decoder.decode(cc(0, 4, 66))
    assert decoder.decode(cc(0, 36, 61)) is not None
    # SMART CFX を押したときのまとめ送りで同じ値がもう一度来ても無視する
    decoder.decode(cc(0, 4, 66))
    assert decoder.decode(cc(0, 36, 61)) is None


def test_button_press_and_release():
    decoder = FLX4Decoder()
    assert decoder.decode(note(0, 12)).value == 1.0
    assert decoder.decode(note(0, 12, 0)).value == 0.0


def test_unknown_messages():
    assert lookup(cc(4, 81, 21)) is None
    assert lookup(mido.Message("clock")) is None
