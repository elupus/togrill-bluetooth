from datetime import timedelta

import anyio
import asyncclick as click
from bleak import (
    BleakClient,
    BleakScanner,
)
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.uuids import uuidstr_to_str

from .const import MainService, ManufacturerData
from .exceptions import DecodeError
from .parse import Characteristic, NotifyCharacteristic, WriteCharacteristic
from .parse_packets import (
    PacketA0Notify,
    PacketA1Notify,
    PacketA7Write,
    PacketA300Write,
    PacketA301Write,
    PacketNotify,
)


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


@cli.group(chain=True)
@click.argument("address")
@click.option("--code", default="")
@click.pass_context
async def connect(ctx: click.Context, address: str, code: str):
    click.echo(f"Connecting to: {address} ...", nl=False)
    client = await ctx.with_async_resource(BleakClient(address, timeout=20))
    ctx.obj = client
    click.echo(" Done")

    def notify_data(char_specifier: BleakGATTCharacteristic, data: bytearray):
        try:
            packet_data = NotifyCharacteristic.decode(data)
            packet = PacketNotify.decode(packet_data)
            click.echo(f"Notify: {packet}")
        except DecodeError as exc:
            click.echo(f"Failed to decode: {data.hex()} with error {exc}")

    await client.start_notify(MainService.notify.uuid, notify_data)

    await client.write_gatt_char(
        MainService.write.uuid, WriteCharacteristic.encode(PacketA0Notify.request()), False
    )
    await client.write_gatt_char(
        MainService.write.uuid, WriteCharacteristic.encode(PacketA1Notify.request()), False
    )


@connect.command()
@click.pass_obj
async def list(client: BleakClient):
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


@connect.command()
@click.argument("probe", type=int)
@click.argument("seconds", type=int)
@click.pass_obj
async def timer(client: BleakClient, probe: int, seconds: int):
    click.echo(f"Setting timer on {probe} for delay {seconds} ...", nl=False)
    await client.write_gatt_char(
        MainService.write.uuid,
        WriteCharacteristic.encode(
            PacketA7Write(probe=probe, time=timedelta(seconds=seconds)).encode()
        ),
        False,
    )
    click.echo(" Done")


@connect.command()
@click.argument("probe", type=int)
@click.argument("minimum", type=float)
@click.argument("maximum", type=float)
@click.pass_obj
async def range(client: BleakClient, probe: int, minimum: float, maximum: float):
    click.echo(f"Setting range cook on {probe} min: {minimum} max: {maximum} ...", nl=False)
    await client.write_gatt_char(
        MainService.write.uuid,
        WriteCharacteristic.encode(
            PacketA300Write(probe=probe, minimum=minimum, maximum=maximum).encode()
        ),
        False,
    )
    click.echo(" Done")


@connect.command()
@click.argument("probe", type=int)
@click.argument("target", type=float)
@click.pass_obj
async def target(client: BleakClient, probe: int, target: float):
    click.echo(f"Setting range cook on {probe} target: {target} ...", nl=False)
    await client.write_gatt_char(
        MainService.write.uuid,
        WriteCharacteristic.encode(PacketA301Write(probe=probe, target=target).encode()),
        False,
    )
    click.echo(" Done")


@connect.command()
async def wait():
    click.echo("Waiting")
    await anyio.sleep_forever()


def main():
    try:
        cli()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
