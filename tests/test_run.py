from vrcdj.run import ParamSender


class FakeClient:
    def __init__(self):
        self.sent = []

    def send_message(self, address, value):
        self.sent.append((address, value))


def test_sender_only_sends_changes_and_keeps_bool_type():
    client = FakeClient()
    sender = ParamSender(client, verbose=False)
    sender.send({"DJ_HandL": 1, "DJ_Active": True})
    sender.send({"DJ_HandL": 1, "DJ_Active": True})
    sender.send({"DJ_HandL": 0, "DJ_Active": False})
    assert client.sent == [
        ("/avatar/parameters/DJ_HandL", 1),
        ("/avatar/parameters/DJ_Active", True),
        ("/avatar/parameters/DJ_HandL", 0),
        ("/avatar/parameters/DJ_Active", False),
    ]
