from datetime import timedelta

import pytest

from togrill_bluetooth.packets import (
    Packet,
    PacketA0Notify,
    PacketA1Notify,
    PacketA6Write,
    PacketA7Write,
    PacketA8Notify,
    PacketA300Write,
    PacketA301Write,
    PacketA303Write,
    PacketNotify,
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
                probe_count=6,
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
            "a8 01 00 03 e8 ff ff 00 05 00 00 00 00",
            PacketA8Notify(
                probe=1, alarm_type=0, temperature_1=100, temperature_2=None, grill_type=5
            ),
        ),
        (
            "a8 02 00 03 e8 03 e9 00 05 00 00 00 00",
            PacketA8Notify(
                probe=2, alarm_type=0, temperature_1=100, temperature_2=100.1, grill_type=5
            ),
        ),
        (
            "a8 01 01 03e8 ffff 00 05 00 00 00 00",
            PacketA8Notify(probe=1, alarm_type=1, temperature_1=100, grill_type=5),
        ),
        (
            "a8 01 ff 03e8 ffff 00 05 00 00 00 00",
            PacketA8Notify(probe=1, alarm_type=None, temperature_1=100, grill_type=5),
        ),
        (
            "00ffffffffffffffffffffffffffff",
            PacketUnknown(0x00, bytes.fromhex("ffffffffffffffffffffffffffff")),
        ),
    ],
)
def test_decode_packet(data: str, result: Packet):
    packet = PacketNotify.decode(bytes.fromhex(data))
    assert packet == result


@pytest.mark.parametrize(
    "packet,raw",
    [
        (
            PacketA7Write(probe=0, time=timedelta(seconds=16), unknown=1),
            "a700010010",
        ),
        (
            PacketA6Write(temperature_unit=PacketA6Write.Unit.UNIT_CELCIUS, alarm_interval=5),
            "a60005",
        ),
        (
            PacketA6Write(temperature_unit=PacketA6Write.Unit.UNIT_FARENHEIT),
            "a601ff",
        ),
        (
            PacketA6Write(alarm_interval=15),
            "a6ff0f",
        ),
        (
            PacketA7Write(probe=0, time=timedelta(seconds=256), unknown=1),
            "a700010100",
        ),
        (
            PacketA300Write(probe=1, minimum=1.6, maximum=3.2),
            "a3 01 00 0010 0020",
        ),
        (
            PacketA301Write(probe=1, target=1.6),
            "a3 01 01 0010 0000",
        ),
        (
            PacketA303Write(probe=1, grill_type=5),
            "a3 01 03 0005 0000",
        ),
    ],
)
def test_roundtrip_packet(packet: Packet, raw: str):
    raw_bytes = bytes.fromhex(raw)
    packet_bytes = packet.encode()
    assert packet_bytes == raw_bytes
    assert packet == packet.decode(raw_bytes)
