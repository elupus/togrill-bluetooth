import anyio
import asyncclick as click
from bleak import (
    AdvertisementData,
    BleakClient,
    BleakGATTCharacteristic,
    BleakScanner,
    BLEDevice,
)
from bleak.uuids import uuidstr_to_str

from .const import MainService, ManufacturerData
from .exceptions import DecodeError
from .parse import Characteristic, NotifyCharacteristic, WriteCharacteristic
from .parse_packets import Packet, PacketA0, PacketA1


@click.group()
async def cli():
    pass


@cli.command()
async def scan():
    click.echo("Scanning for devices")

    devices = set()

    def detected(device: BLEDevice, advertisement: AdvertisementData):
        if device not in devices:
            if MainService.uuid not in advertisement.service_uuids:
                return
            devices.add(device)

        click.echo(f"Device: {device}")
        for service in advertisement.service_uuids:
            click.echo(f" - Service: {service} {uuidstr_to_str(service)}")
        click.echo(f" - Data: {advertisement.service_data}")
        click.echo(f" - Manu: {advertisement.manufacturer_data}")

        if data := advertisement.manufacturer_data.get(ManufacturerData.company):
            decoded = ManufacturerData.decode(data)
            click.echo(f" -     : {decoded}")

        click.echo(f" - RSSI: {advertisement.rssi}")
        click.echo()

    async with BleakScanner(detected, service_uuids=[MainService.uuid]):
        await anyio.sleep_forever()


@cli.command()
@click.argument("address")
@click.option("--code", default="")
async def connect(address: str, code: str):
    click.echo(f"Connecting to: {address}")
    async with BleakClient(address, timeout=20) as client:
        for service in client.services:
            click.echo(f"Service: {service}")

            async def read_print(char: BleakGATTCharacteristic):
                parser = Characteristic.registry.get(char.uuid)
                if "read" in char.properties:
                    data = await client.read_gatt_char(char.uuid)
                else:
                    data = None
                click.echo(f" -  {char}")
                click.echo(f" -  {char.properties}")
                if data is not None and parser:
                    click.echo(f" -  Data: {parser.decode(data)}")

            async with anyio.create_task_group() as tg:
                for char in service.characteristics:
                    tg.start_soon(read_print, char)

        def notify_data(char_specifier: BleakGATTCharacteristic, data: bytearray):
            try:
                packet_data = NotifyCharacteristic.decode(data)
                packet = Packet.decode(packet_data)
                click.echo(f"Notify: {packet}")
            except DecodeError as exc:
                click.echo(f"Failed to decode: {data.hex()} with error {exc}")

        await client.start_notify(MainService.notify.uuid, notify_data)

        await client.write_gatt_char(
            MainService.write.uuid, WriteCharacteristic.encode(PacketA0.request()), False
        )

        # Could be needed on WP-01 devices
        await client.write_gatt_char(
            MainService.write.uuid, WriteCharacteristic.encode(PacketA1.request()), False
        )

        await anyio.sleep_forever()

        # client.write_gatt_char(MainService.auth.uuid, )


def main():
    try:
        cli()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
