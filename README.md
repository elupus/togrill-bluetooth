# ToGrill Bluetooth Library

ToGrill is a Python library for communicating with ToGrill Bluetooth-enabled devices, such as smart grilling thermometers. It provides tools for scanning, connecting, and interacting with these devices, including reading probe temperatures, setting timers, and configuring temperature ranges.

It's main target use is for integration into Home Assistant integrations.

## Features

- Scan for ToGrill Bluetooth devices
- Connect and interact with devices using BLE
- Read probe temperatures and device status
- Set timers and temperature ranges
- Command-line interface for easy usage and scripting

## Command-Line Interface

### Commands

- scan
  Scan for nearby ToGrill Bluetooth devices and display their information.

- connect `address`
  Connect to a device by Bluetooth address. This command opens a group of subcommands:
  Commands can be chained to perform multiple actions in one connection.

  - list
    List all GATT services and characteristics, and read available data.

  - timer `probe` `seconds`
    Set a timer on the specified probe for a given number of seconds.

  - range `probe` `minimum` `maximum`
    Set a minimum and maximum temperature range for a probe.

  - target `probe` `target`
    Set a target temperature for a probe.

  - wait
    Wait indefinitely, keeping the connection open.

### Examples

- `togrill-bluetooth scan`
- `togrill-bluetooth connect AA:BB:CC:DD:EE:FF list wait`
- `togrill-bluetooth connect AA:BB:CC:DD:EE:FF timer 1 600`
- `togrill-bluetooth connect AA:BB:CC:DD:EE:FF range 1 50.0 80.0`
- `togrill-bluetooth connect AA:BB:CC:DD:EE:FF target 1 65.0`
- `togrill-bluetooth connect AA:BB:CC:DD:EE:FF wait`
