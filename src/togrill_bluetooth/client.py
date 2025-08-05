from __future__ import annotations

import logging
from collections.abc import Callable

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection

from .const import MainService
from .exceptions import DecodeError
from .packets import Packet, PacketNotify
from .services import NotifyCharacteristic, WriteCharacteristic

_LOGGER = logging.getLogger(__name__)


class Client:
    def __init__(self, client: BleakClient, notify_callback: Callable[[Packet], None]) -> None:
        self.bleak_client = client
        self._notify_callback = notify_callback

    @property
    def is_connected(self) -> bool:
        return self.bleak_client.is_connected

    async def _start_notify(self):
        def notify_data(char_specifier: BleakGATTCharacteristic, data: bytearray):
            try:
                packet_data = NotifyCharacteristic.decode(data)
                packet = PacketNotify.decode(packet_data)
                _LOGGER.debug("Notify: %s", packet)

                if self._notify_callback:
                    self._notify_callback(packet)
            except DecodeError as exc:
                _LOGGER.error("Failed to decode: %s with error %s", data, exc)

        await self.bleak_client.start_notify(MainService.notify.uuid, notify_data)

    @staticmethod
    async def connect(
        device: BLEDevice,
        notify_callback: Callable[[Packet], None],
        disconnected_callback: Callable[[], None] | None = None,
    ) -> Client:
        def _disconnected_callback(client: BleakClient):
            _LOGGER.info("Device disconnected %s", client.address)
            if disconnected_callback:
                disconnected_callback()

        bleak_client = await establish_connection(
            BleakClient,
            device=device,
            name="ToGrill Connection",
            disconnected_callback=_disconnected_callback,
        )
        try:
            client = Client(bleak_client, notify_callback)
            await client._start_notify()
        except Exception:
            await bleak_client.disconnect()
            pass
        return client

    async def disconnect(self) -> None:
        await self.bleak_client.disconnect()

    async def request(self, packet: type[PacketNotify]) -> None:
        await self.bleak_client.write_gatt_char(
            MainService.write.uuid, WriteCharacteristic.encode(packet.request()), False
        )
