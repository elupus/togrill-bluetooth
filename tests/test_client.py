from unittest.mock import Mock

from bleak import BleakClient

from togrill_bluetooth.client import Client
from togrill_bluetooth.packets import PacketUnknown


def test_client_notify():
    mock_ble_client = Mock(spec_set=BleakClient)

    callback = Mock()
    packet = PacketUnknown(0, b"")

    client = Client(mock_ble_client, callback)
    client.notify_callbacks(packet)

    callback.assert_called_once_with(packet)
