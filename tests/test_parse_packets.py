import pytest

from togrill_bluetooth.parse_packets import Packet, PacketA0, PacketA1, PacketUnknown


@pytest.mark.parametrize(
    "data,result",
    [
        (
            "a05b000800600501",
            PacketA0(
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
            PacketA1(temperatures=[None, None, None, None, None, None, None]),
        ),
        (
            "a1 ffff ffff ffff ffff ffff ffff 01b5",
            PacketA1(temperatures=[None, None, None, None, None, None, 43.7]),
        ),
        (
            "00ffffffffffffffffffffffffffff",
            PacketUnknown(0x00, bytes.fromhex("ffffffffffffffffffffffffffff")),
        ),
    ],
)
def test_decode_packet(data, result):
    packet = Packet.decode(bytes.fromhex(data))
    assert packet == result
