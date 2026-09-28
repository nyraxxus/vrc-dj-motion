"""DDJ-FLX4 などの MIDI コントローラーから届くメッセージを表示・記録する。

使い方:
    python -m vrcdj.monitor --list            # MIDI 入力ポートの一覧
    python -m vrcdj.monitor                   # 名前に "FLX4" を含むポートを開いて表示
    python -m vrcdj.monitor --port "loopMIDI" # ポート名の一部で指定
    python -m vrcdj.monitor --log             # logs/ に JSON Lines で記録もする

rekordbox を起動したままこれで表示できれば、MIDI の同時読み取りは OK。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import mido

DEFAULT_PORT_HINT = "FLX4"


def find_port(names: list[str], hint: str) -> str | None:
    hint_lower = hint.lower()
    for name in names:
        if hint_lower in name.lower():
            return name
    return None


def describe(msg: mido.Message) -> str:
    """人が読みやすい 1 行表示。"""
    ch = getattr(msg, "channel", None)
    ch_text = f"ch{ch + 1:>2}" if ch is not None else "    "
    if msg.type in ("note_on", "note_off"):
        return f"{ch_text} {msg.type:<14} note={msg.note:>3} vel={msg.velocity:>3}"
    if msg.type == "control_change":
        return f"{ch_text} {msg.type:<14} cc={msg.control:>3}   val={msg.value:>3}"
    if msg.type == "pitchwheel":
        return f"{ch_text} {msg.type:<14} pitch={msg.pitch:>6}"
    return f"{ch_text} {msg}"


def receive(port, interval: float = 0.002):
    """ポートからメッセージを取り出し続ける。

    `for msg in port` だと Windows ではメッセージ待ちの間 Ctrl+C が効かないので、
    短い間隔でポーリングして KeyboardInterrupt を受け取れるようにしている。
    """
    while True:
        yield from port.iter_pending()
        time.sleep(interval)


def to_record(msg: mido.Message, elapsed: float) -> dict:
    record = {"t": round(elapsed, 4)}
    record.update(msg.dict())
    return record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MIDI 入力を表示・記録する")
    parser.add_argument("--list", action="store_true", help="MIDI 入力ポートの一覧を表示して終了")
    parser.add_argument("--port", default=DEFAULT_PORT_HINT, help="開くポート名の一部 (既定: FLX4)")
    parser.add_argument("--log", action="store_true", help="logs/ に JSON Lines で記録する")
    parser.add_argument("--show-clock", action="store_true", help="clock / active_sensing も表示する")
    args = parser.parse_args(argv)

    names = mido.get_input_names()
    if args.list or not names:
        if not names:
            print("MIDI 入力ポートが見つかりません。コントローラーの接続とドライバを確認してください。")
        else:
            print("MIDI 入力ポート:")
            for name in names:
                print(f"  {name}")
        return 0 if names else 1

    port_name = find_port(names, args.port)
    if port_name is None:
        print(f'"{args.port}" を含む MIDI 入力ポートがありません。見つかったポート:')
        for name in names:
            print(f"  {name}")
        return 1

    log_file = None
    if args.log:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_path = log_dir / f"midi-{datetime.now():%Y%m%d-%H%M%S}.jsonl"
        log_file = log_path.open("w", encoding="utf-8")
        print(f"記録先: {log_path}")

    try:
        port = mido.open_input(port_name)
    except (OSError, IOError) as exc:
        print(f"ポート「{port_name}」を開けませんでした: {exc}")
        print("別のアプリ (rekordbox など) が独占している可能性があります。")
        return 1

    hidden = set() if args.show_clock else {"clock", "active_sensing"}
    print(f"監視中: {port_name}  (Ctrl+C で終了)")
    start = time.perf_counter()
    try:
        with port:
            for msg in receive(port):
                if msg.type in hidden:
                    continue
                elapsed = time.perf_counter() - start
                print(f"{elapsed:9.3f}s  {describe(msg)}")
                if log_file:
                    log_file.write(json.dumps(to_record(msg, elapsed)) + "\n")
                    log_file.flush()
    except KeyboardInterrupt:
        print("\n終了しました。")
    finally:
        if log_file:
            log_file.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
