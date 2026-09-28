"""VRChat との OSC 疎通テスト。

事前に VRChat のアクションメニュー → Options → OSC → Enabled をオンにしておく。

使い方:
    python -m vrcdj.osctest chatbox "テスト"          # チャットボックスに表示 (アバター改変不要)
    python -m vrcdj.osctest param DJ_HandL 1          # アバターパラメーターを送る (int)
    python -m vrcdj.osctest param DJ_XFader 0.5       # 小数なら float
    python -m vrcdj.osctest param DJ_Active true      # true/false なら bool
    python -m vrcdj.osctest listen                    # VRChat から届く OSC を表示 (port 9001)
"""

from __future__ import annotations

import argparse
import sys

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

VRCHAT_HOST = "127.0.0.1"
VRCHAT_IN_PORT = 9000   # VRChat が受け取るポート
VRCHAT_OUT_PORT = 9001  # VRChat が送ってくるポート


def parse_value(text: str) -> bool | int | float:
    lowered = text.lower()
    if lowered in ("true", "on"):
        return True
    if lowered in ("false", "off"):
        return False
    try:
        return int(text)
    except ValueError:
        return float(text)


def cmd_chatbox(client: SimpleUDPClient, args: argparse.Namespace) -> None:
    # /chatbox/input: (テキスト, 即時送信, 通知音)
    client.send_message("/chatbox/input", [args.text, True, False])
    print(f"チャットボックスに送信: {args.text}")


def cmd_param(client: SimpleUDPClient, args: argparse.Namespace) -> None:
    value = parse_value(args.value)
    address = f"/avatar/parameters/{args.name}"
    client.send_message(address, value)
    print(f"送信: {address} = {value!r} ({type(value).__name__})")


def cmd_listen(args: argparse.Namespace) -> None:
    dispatcher = Dispatcher()
    dispatcher.set_default_handler(lambda address, *values: print(address, *values))
    server = BlockingOSCUDPServer((args.host, args.port), dispatcher)
    print(f"{args.host}:{args.port} で待ち受け中 (Ctrl+C で終了)")
    print("VRChat でアバターを動かしたり表情を変えたりすると、パラメーターが表示されます。")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n終了しました。")
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="VRChat との OSC 疎通テスト")
    parser.add_argument("--host", default=VRCHAT_HOST)
    sub = parser.add_subparsers(dest="command", required=True)

    p_chat = sub.add_parser("chatbox", help="チャットボックスに文字を出す")
    p_chat.add_argument("text")
    p_chat.add_argument("--port", type=int, default=VRCHAT_IN_PORT)

    p_param = sub.add_parser("param", help="アバターパラメーターを送る")
    p_param.add_argument("name")
    p_param.add_argument("value", help="true/false、整数、小数のいずれか")
    p_param.add_argument("--port", type=int, default=VRCHAT_IN_PORT)

    p_listen = sub.add_parser("listen", help="VRChat から届く OSC を表示する")
    p_listen.add_argument("--port", type=int, default=VRCHAT_OUT_PORT)

    args = parser.parse_args(argv)

    if args.command == "listen":
        cmd_listen(args)
        return 0

    client = SimpleUDPClient(args.host, args.port)
    if args.command == "chatbox":
        cmd_chatbox(client, args)
    else:
        cmd_param(client, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
