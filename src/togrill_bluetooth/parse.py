from dataclasses import dataclass
from functools import reduce
from itertools import chain, tee
from operator import xor
from typing import ClassVar, Generic, TypeVar, cast

from .exceptions import DecodeError

CharacteristicType = TypeVar("CharacteristicType")

_PAYLOAD_PREFIX = [0x55, 0xAA]


def pretty_name(name: str):
    data = name.split("_")
    return " ".join(f"{part[0].upper()}{part[1:]}" for part in data)


def wrap_payload(data: bytes) -> bytes:
    """Wraps the payload with the prefix and checksum."""
    payload = chain(_PAYLOAD_PREFIX, len(data).to_bytes(2, "big"), data)
    payload, payload_copy = tee(payload, 2)
    checksum = reduce(xor, payload_copy)
    return bytes(chain(payload, [checksum]))


def unwrap_payload(data: bytes) -> bytes:
    """Unwraps the payload, removing the prefix and checksum."""
    if len(data) < 5 or data[0:2] != bytes(_PAYLOAD_PREFIX):
        raise DecodeError("Invalid payload format")

    payload_len = int.from_bytes(data[2:4], "big")
    if len(data) - 5 != payload_len:
        raise DecodeError("Payload size mismatch")

    payload = data[4 : 4 + payload_len]
    checksum = data[4 + payload_len]
    checksum_expected = reduce(xor, data[:-1])

    if checksum_expected != checksum:
        raise DecodeError(f"Expected checksum {checksum_expected:x} found {checksum:x}")

    return payload


@dataclass
class Characteristic(Generic[CharacteristicType]):
    uuid: str
    name: str = ""
    registry: ClassVar[dict[str, "Characteristic"]] = {}

    def __set_name__(self, _, name: str):
        self.name = pretty_name(name)

    def __post_init__(self):
        self.registry[self.uuid] = self

    @classmethod
    def decode(cls, data: bytes) -> CharacteristicType:
        raise NotImplementedError(f"Decoding of {type(cls)} is not implemented")

    @classmethod
    def encode(cls, data: CharacteristicType) -> bytes:
        raise NotImplementedError(f"Encoding of {type(cls)} is not implemented")


class Service:
    uuid: ClassVar[str]
    registry: ClassVar[dict[str, "Service"]] = {}

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.registry[cls.uuid] = cast(Service, cls)

    @classmethod
    def characteristics(cls):
        for value in vars(cls).values():
            if isinstance(value, Characteristic):
                yield value


@dataclass
class NotifyCharacteristic(Characteristic[bytes]):
    uuid: ClassVar[str] = "0000cee2-0000-1000-8000-00805f9b34fb"

    @staticmethod
    def decode(data: bytes) -> bytes:
        return unwrap_payload(data)

    @staticmethod
    def encode(data: bytes) -> bytes:
        return wrap_payload(data)


@dataclass
class WriteCharacteristic(Characteristic[bytes]):
    uuid: ClassVar[str] = "0000cee1-0000-1000-8000-00805f9b34fb"

    @staticmethod
    def decode(data: bytes) -> bytes:
        return unwrap_payload(data)

    @staticmethod
    def encode(data: bytes) -> bytes:
        return wrap_payload(data)
