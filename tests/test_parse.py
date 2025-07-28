import pytest

from togrill_bluetooth.parse import WriteCharacteristic
from togrill_bluetooth.parse import NotifyCharacteristic


@pytest.mark.parametrize(
    "data,result", [("A100", "55AA0002A1005C"), ("A00000", "55AA0003A000005C")]
)
def test_encode_packet(data, result):
    assert (
        WriteCharacteristic.encode(bytes.fromhex(data)).hex() == bytes(bytes.fromhex(result)).hex()
    )


@pytest.mark.parametrize(
    "data,result",
    [
        ("55aa0008a05b00080060050160", "a05b000800600501"),
        ("55aa000fa1ffffffffffffffffffffffffffff51", "a1ffffffffffffffffffffffffffff"),
    ],
)
def test_decode_packet(data, result):
    assert (
        NotifyCharacteristic.decode(bytes.fromhex(data)).hex() == bytes(bytes.fromhex(result)).hex()
    )
