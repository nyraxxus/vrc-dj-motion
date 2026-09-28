from vrcdj.osctest import parse_value


def test_parse_value_types():
    assert parse_value("true") is True
    assert parse_value("OFF") is False
    assert parse_value("3") == 3 and isinstance(parse_value("3"), int)
    assert parse_value("0.25") == 0.25
