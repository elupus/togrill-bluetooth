from dataclasses import dataclass
from typing import ClassVar, Self

from .exceptions import DecodeError

_PACKET_REGISTRY: dict[int, "Packet"] = {}


@dataclass
class Packet:
    type: int

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "type"):
            _PACKET_REGISTRY[cls.type] = cls

    @classmethod
    def decode(cls, data: bytes) -> Self:
        if len(data) < 1:
            raise DecodeError("Failed to parse packet")
        cls = _PACKET_REGISTRY.get(data[0])
        if cls:
            return cls.decode(data)
        return PacketUnknown(data[0], data[1:])


@dataclass
class PacketA0(Packet):
    type: ClassVar[int] = 0xA0
    battery: int
    version_major: int
    version_minor: int
    function_type: int
    probe_number: int
    ambient: bool
    alarm_interval: int
    alarm_sound: bool

    @classmethod
    def decode(cls, data: bytes) -> Self:
        if len(data) < 6:
            raise DecodeError("Packet too short")
        if data[0] != cls.type:
            raise DecodeError("Failed to parse packet")

        battery = data[1]
        version_major = data[2]
        version_minor = data[3]
        _unknown = data[4]
        bitfield = data[5]
        function_type = bitfield & 0xF
        probe_number = (bitfield >> 4) & 0x7
        ambient = bool(bitfield >> 7)

        alarm_interval = 5
        alarm_sound = True
        if len(data) > 6:
            alarm_interval = data[6]
            alarm_sound = data[7] == 1

        return PacketA0(
            battery=battery,
            version_major=version_major,
            version_minor=version_minor,
            function_type=function_type,
            probe_number=probe_number,
            ambient=ambient,
            alarm_interval=alarm_interval,
            alarm_sound=alarm_sound,
        )

    @classmethod
    def request(cls) -> None:
        return bytes(
            [
                cls.type,
                0x00,
                0x00,
            ]
        )


@dataclass
class PacketA1(Packet):
    type: ClassVar[int] = 0xA1
    temperatures: list[float | None]

    @classmethod
    def decode(cls, data: bytes) -> Self:
        if len(data) < 1:
            raise DecodeError("Packet too short")
        if data[0] != cls.type:
            raise DecodeError("Failed to parse packet")

        temperatures = [
            int.from_bytes(data[index : index + 2], "big") for index in range(1, len(data), 2)
        ]

        def convert(value: int) -> float | None:
            if value == 65535:
                return None
            if value > 32768:
                return (value - 32768) / 10
            return value / 10

        temperatures = [convert(temperature) for temperature in temperatures]

        return PacketA1(temperatures=temperatures)

    @classmethod
    def request(cls) -> None:
        return bytes(
            [
                cls.type,
                0x00,
            ]
        )


@dataclass
class PacketUnknown(Packet):
    type: int
    data: bytes
