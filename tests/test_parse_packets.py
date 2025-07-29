from datetime import timedelta

import pytest

from togrill_bluetooth.parse_packets import (
    Packet,
    PacketA0Notify,
    PacketA1Notify,
    PacketA7Write,
    PacketUnknown,
)


@pytest.mark.parametrize(
    "data,result",
    [
        (
            "a05b000800600501",
            PacketA0Notify(
                battery=91,
                version_major=0,
                version_minor=8,
                function_type=0,
                probe_number=6,
                ambient=False,
                alarm_interval=5,
                alarm_sound=True,
            ),
        ),
        (
            "a1ffffffffffffffffffffffffffff",
            PacketA1Notify(temperatures=[None, None, None, None, None, None, None]),
        ),
        (
            "a1 ffff ffff ffff ffff ffff ffff 01b5",
            PacketA1Notify(temperatures=[None, None, None, None, None, None, 43.7]),
        ),
        (
            "00ffffffffffffffffffffffffffff",
            PacketUnknown(0x00, bytes.fromhex("ffffffffffffffffffffffffffff")),
        ),
        (
            "a700010010",
            PacketA7Write(probe=0, time=timedelta(seconds=16), unknown=1),
        ),
    ],
)
def test_decode_packet(data, result: Packet):
    packet = result.decode(bytes.fromhex(data))
    assert packet == result


@pytest.mark.parametrize(
    "data,result",
    [
        (
            PacketA7Write(probe=0, time=timedelta(seconds=16), unknown=1),
            "a700010010",
        ),
        (
            PacketA7Write(probe=0, time=timedelta(seconds=256), unknown=1),
            "a700010100",
        ),
    ],
)
def test_encode_packet(data: Packet, result):
    packet = data.encode()
    assert packet == bytes.fromhex(result)
