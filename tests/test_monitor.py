import json

import mido

from vrcdj import monitor


class FakePort:
    def __init__(self, messages):
        self.messages = messages

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __iter__(self):
        return iter(self.messages)


def test_find_port_is_case_insensitive():
    names = ["Microsoft GS Wavetable Synth", "DDJ-FLX4 0"]
    assert monitor.find_port(names, "flx4") == "DDJ-FLX4 0"
    assert monitor.find_port(names, "nothing") is None


def test_describe_formats_common_messages():
    assert "note= 11" in monitor.describe(mido.Message("note_on", channel=0, note=11, velocity=127))
    assert "cc= 31" in monitor.describe(mido.Message("control_change", channel=6, control=31, value=64))
    assert "ch 7" in monitor.describe(mido.Message("control_change", channel=6, control=31, value=64))


def test_main_prints_and_logs_messages(monkeypatch, tmp_path, capsys):
    messages = [
        mido.Message("clock"),
        mido.Message("note_on", channel=0, note=12, velocity=127),
        mido.Message("control_change", channel=6, control=31, value=10),
    ]
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(mido, "get_input_names", lambda: ["DDJ-FLX4 0"])
    monkeypatch.setattr(mido, "open_input", lambda name: FakePort(messages))

    assert monitor.main(["--log"]) == 0

    out = capsys.readouterr().out
    assert "監視中: DDJ-FLX4 0" in out
    assert "clock" not in out.split("監視中")[1]
    logs = list((tmp_path / "logs").glob("midi-*.jsonl"))
    records = [json.loads(line) for line in logs[0].read_text(encoding="utf-8").splitlines()]
    assert [r["type"] for r in records] == ["note_on", "control_change"]


def test_main_reports_busy_port(monkeypatch, capsys):
    def busy(name):
        raise OSError("device in use")

    monkeypatch.setattr(mido, "get_input_names", lambda: ["DDJ-FLX4 0"])
    monkeypatch.setattr(mido, "open_input", busy)

    assert monitor.main([]) == 1
    assert "rekordbox" in capsys.readouterr().out


def test_main_lists_ports_when_hint_missing(monkeypatch, capsys):
    monkeypatch.setattr(mido, "get_input_names", lambda: ["loopMIDI Port"])
    assert monitor.main(["--port", "FLX4"]) == 1
    assert "loopMIDI Port" in capsys.readouterr().out
