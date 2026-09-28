"""本体: FLX4 の操作に合わせて VRChat アバターのパラメーターを OSC で送る。

使い方:
    python -m vrcdj.run                         # FLX4 を読んで VRChat に送る
    python -m vrcdj.run --verbose               # 送った値も表示する
    python -m vrcdj.run --dry-run --verbose     # VRChat に送らず表示だけ
    python -m vrcdj.run --replay logs\\xxx.jsonl # 記録したログを再生して送る(FLX4 不要)

事前に VRChat の OSC をオンにしておくこと。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import mido
from pythonosc.udp_client import SimpleUDPClient

from vrcdj.flx4 import FLX4Decoder
from vrcdj.monitor import DEFAULT_PORT_HINT, find_port
from vrcdj.motion import P_ACTIVE, MotionEngine
from vrcdj.osctest import VRCHAT_HOST, VRCHAT_IN_PORT

TICK = 1 / 30  # パラメーターを送る間隔(秒)


class ParamSender:
    """値が変わったパラメーターだけを送る。"""

    def __init__(self, client: SimpleUDPClient | None, verbose: bool) -> None:
        self.client = client
        self.verbose = verbose
        self.sent: dict[str, bool | int | float] = {}

    def send(self, params: dict[str, bool | int | float]) -> None:
        for name, value in params.items():
            if self.sent.get(name) == value and type(self.sent.get(name)) is type(value):
                continue
            self.sent[name] = value
            if self.client:
                self.client.send_message(f"/avatar/parameters/{name}", value)
            if self.verbose:
                print(f"  {name} = {value}")


def live_messages(port) -> Iterator[mido.Message | None]:
    """FLX4 から届いたメッセージ。届いていないときは None を返して tick を回す。"""
    while True:
        got = False
        for msg in port.iter_pending():
            got = True
            yield msg
        if not got:
            yield None
            time.sleep(0.002)


def replay_messages(path: Path, speed: float) -> Iterator[mido.Message | None]:
    """記録したログを、記録したときと同じ間隔で流す。"""
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    start = time.perf_counter()
    first = records[0]["t"] if records else 0.0
    for record in records:
        due = (record.pop("t") - first) / speed
        while time.perf_counter() - start < due:
            yield None
            time.sleep(0.002)
        yield mido.Message.from_dict(record)
    # 最後の動作が待機に戻るまで少し回す
    end = time.perf_counter() + 1.5
    while time.perf_counter() < end:
        yield None
        time.sleep(0.01)


def run(messages: Iterator[mido.Message | None], sender: ParamSender, show_controls: bool) -> None:
    decoder = FLX4Decoder()
    engine = MotionEngine()
    next_tick = 0.0
    for msg in messages:
        now = time.perf_counter()
        if msg is not None:
            event = decoder.decode(msg)
            if event:
                engine.handle(event, now)
                if show_controls:
                    shift = " +SHIFT" if event.control.shift else ""
                    print(f"{event.control.name}{shift}: {event.value:g}")
        if now >= next_tick:
            sender.send(engine.params(now))
            next_tick = now + TICK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="FLX4 の操作に合わせて VRChat アバターを動かす")
    parser.add_argument("--port", default=DEFAULT_PORT_HINT, help="MIDI 入力ポート名の一部 (既定: FLX4)")
    parser.add_argument("--host", default=VRCHAT_HOST)
    parser.add_argument("--osc-port", type=int, default=VRCHAT_IN_PORT)
    parser.add_argument("--replay", type=Path, help="FLX4 の代わりに記録ログを再生する")
    parser.add_argument("--speed", type=float, default=1.0, help="ログ再生の速さ (2 なら 2 倍速)")
    parser.add_argument("--dry-run", action="store_true", help="VRChat に送らない")
    parser.add_argument("--verbose", action="store_true", help="送るパラメーターを表示する")
    parser.add_argument("--show-controls", action="store_true", help="解読した操作も表示する")
    args = parser.parse_args(argv)

    client = None if args.dry_run else SimpleUDPClient(args.host, args.osc_port)
    sender = ParamSender(client, args.verbose)

    try:
        if args.replay:
            print(f"ログ再生: {args.replay}  (Ctrl+C で終了)")
            run(replay_messages(args.replay, args.speed), sender, args.show_controls)
            print("再生が終わりました。")
            return 0

        names = mido.get_input_names()
        port_name = find_port(names, args.port)
        if port_name is None:
            print(f'"{args.port}" を含む MIDI 入力ポートがありません。見つかったポート: {names}')
            return 1
        with mido.open_input(port_name) as port:
            target = "表示のみ" if args.dry_run else f"{args.host}:{args.osc_port}"
            print(f"動作中: {port_name} → {target}  (Ctrl+C で終了)")
            run(live_messages(port), sender, args.show_controls)
    except KeyboardInterrupt:
        print("\n終了しました。")
    finally:
        sender.send({P_ACTIVE: False})
    return 0


if __name__ == "__main__":
    sys.exit(main())
