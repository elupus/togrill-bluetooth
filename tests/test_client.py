from unittest.mock import Mock

from bleak import BleakClient

from togrill_bluetooth.client import Client
from togrill_bluetooth.packets import Packet


def test_client_notify():
    mock_ble_client = Mock(spec_set=BleakClient)

    callback = Mock()
    packet = Packet(0)

    client = Client(mock_ble_client, callback)
    client.notify_callbacks(packet)

    callback.assert_called_once_with(packet)
