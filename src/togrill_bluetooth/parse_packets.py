from dataclasses import dataclass
from datetime import timedelta
from enum import IntEnum
from typing import ClassVar, Self, cast

from .exceptions import DecodeError

_PACKET_REGISTRY: dict[int, "PacketNotify"] = {}


@dataclass
class Packet:
    type: int

    @classmethod
    def decode(cls, data: bytes) -> Self:
        raise NotImplementedError()

    def encode(self) -> bytes:
        raise NotImplementedError()


@dataclass
class PacketNotify(Packet):
    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        if type := getattr(cls, "type", None):
            _PACKET_REGISTRY[type] = cast(PacketNotify, cls)

    @classmethod
    def decode(cls, data: bytes) -> Packet:
        if len(data) < 1:
            raise DecodeError("Failed to parse packet")
        registered_cls = _PACKET_REGISTRY.get(data[0])
        if registered_cls:
            return registered_cls.decode(data)
        return PacketUnknown(data[0], data[1:])

    @classmethod
    def request(cls) -> bytes:
        raise NotImplementedError


@dataclass
class PacketA0Notify(PacketNotify):
    """Device status"""

    type: ClassVar[int] = 0xA0
    battery: int
    version_major: int
    version_minor: int
    function_type: int
    probe_count: int
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
        probe_count = (bitfield >> 4) & 0x7
        ambient = bool(bitfield >> 7)

        alarm_interval = 5
        alarm_sound = True
        if len(data) > 6:
            alarm_interval = data[6]
            alarm_sound = data[7] == 1

        return cls(
            battery=battery,
            version_major=version_major,
            version_minor=version_minor,
            function_type=function_type,
            probe_count=probe_count,
            ambient=ambient,
            alarm_interval=alarm_interval,
            alarm_sound=alarm_sound,
        )

    @classmethod
    def request(cls) -> bytes:
        return bytes(
            [
                cls.type,
                0x00,
                0x00,
            ]
        )


@dataclass
class PacketA1Notify(PacketNotify):
    """Temperature on probes"""

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

        return cls(temperatures=temperatures)

    @classmethod
    def request(cls) -> bytes:
        return bytes(
            [
                cls.type,
                0x00,
            ]
        )


@dataclass
class PacketA300Write(Packet):
    """Set min max temperature."""

    type: ClassVar[int] = 0xA3
    probe: int
    subtype: ClassVar[int] = 0x00
    minimum: float
    maximum: float

    @classmethod
    def decode(cls, data: bytes) -> Self:
        if len(data) < 7:
            raise DecodeError("Packet too short")
        if data[2] != cls.subtype:
            raise DecodeError("Invalid subtype")
        return cls(
            probe=data[1],
            minimum=int.from_bytes(data[3:5], "big") / 10,
            maximum=int.from_bytes(data[5:7], "big") / 10,
        )

    def encode(self) -> bytes:
        min_temp = round(self.minimum * 10).to_bytes(2, "big")
        max_temp = round(self.maximum * 10).to_bytes(2, "big")
        return bytes([self.type, self.probe, self.subtype, *min_temp, *max_temp])


@dataclass
class PacketA301Write(Packet):
    """Set target temperature."""

    type: ClassVar[int] = 0xA3
    probe: int
    subtype: ClassVar[int] = 0x01
    target: float

    @classmethod
    def decode(cls, data: bytes) -> Self:
        if len(data) < 7:
            raise DecodeError("Packet too short")
        if data[2] != cls.subtype:
            raise DecodeError("Invalid subtype")
        return cls(
            probe=data[1],
            target=int.from_bytes(data[3:5], "big") / 10,
        )

    def encode(self) -> bytes:
        target_temp = round(self.target * 10).to_bytes(2, "big")
        return bytes([self.type, self.probe, self.subtype, *target_temp, 0, 0])


@dataclass
class PacketA303Write(Packet):
    """Set target temperature."""

    type: ClassVar[int] = 0xA3
    probe: int
    subtype: ClassVar[int] = 0x03
    grill_type: int

    @classmethod
    def decode(cls, data: bytes) -> Self:
        if len(data) < 7:
            raise DecodeError("Packet too short")
        if data[2] != cls.subtype:
            raise DecodeError("Invalid subtype")
        return cls(
            probe=data[1],
            grill_type=data[4],
        )

    def encode(self) -> bytes:
        return bytes([self.type, self.probe, self.subtype, 0, self.grill_type, 0, 0])


@dataclass
class PacketA5Notify(PacketNotify):
    """Status from probe"""

    type: ClassVar[int] = 0xA5
    probe: int
    message: int

    class Message(IntEnum):
        PROBE_ACKNOWLEDGE = 0
        PROBE_ALARM = 5
        PROBE_DISCONNECTED = 6

    @classmethod
    def decode(cls, data: bytes) -> Self:
        if len(data) < 3:
            raise DecodeError("Packet too short")
        if data[0] != cls.type:
            raise DecodeError("Failed to parse packet")

        try:
            message = PacketA5Notify.Message(data[2])
        except ValueError:
            message = data[2]

        return cls(probe=data[1], message=message)


@dataclass
class PacketA7Notify(PacketNotify):
    """Set timer."""

    type: ClassVar[int] = 0xA7
    data: int

    @classmethod
    def decode(cls, data: bytes) -> Self:
        if len(data) < 2:
            raise DecodeError("Packet too short")
        return cls(data=data[1])


@dataclass
class PacketA7Write(Packet):
    """Set timer."""

    type: ClassVar[int] = 0xA7
    probe: int
    time: timedelta
    unknown: int = 1

    @classmethod
    def decode(cls, data: bytes) -> Self:
        if len(data) < 5:
            raise DecodeError("Packet too short")
        return cls(
            time=timedelta(seconds=int.from_bytes(data[3:5], "big")), probe=data[1], unknown=data[2]
        )

    def encode(self) -> bytes:
        seconds = round(self.time.total_seconds())
        return bytes(
            [
                self.type,
                self.probe,
                self.unknown,
                *seconds.to_bytes(2, "big"),
            ]
        )


@dataclass
class PacketUnknown(Packet):
    type: int
    data: bytes

    @classmethod
    def decode(cls, data: bytes) -> Self:
        if len(data) < 1:
            raise DecodeError("Packet too short")
        return cls(data[0], data=data[1:])
