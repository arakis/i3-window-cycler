#!/usr/bin/env python3
import asyncio
from evdev import InputDevice, ecodes, list_devices
import subprocess
import argparse
import os

async def monitor_key_events(execute_path, keycode, print_all_keys):
    print(f"Execute path: {execute_path}")
    print(f"Keycode: {keycode}")
    if print_all_keys:
        print(f"Print all keys!")

    # Find the keyboard device
    devices = [InputDevice(path) for path in list_devices()]
    keyboard_device = None

    if not devices:
        print("No Devices found. Run as root or configure privileges for evdev")
        return

    print("Found Devices:")
    for device in devices:
        print(device.name)

    for device in devices:
        if "keyboard" in device.name.lower():
            keyboard_device = device
            break

    if not keyboard_device:
        print("Keyboard device not found")
        return

    print(f"Monitoring key events on {keyboard_device.name}")

    # Monitor key events
    async def read_events(device):
        while True:
            event = await device.async_read_one()
            yield event

    async for event in read_events(keyboard_device):
        if event.type == ecodes.EV_KEY:
            if (print_all_keys or event.code == keycode) and event.value == 0:
                print(f"Key with code {event.code} released!")
            if event.code == keycode and event.value == 0:
                subprocess.run(["i3-msg", "mode", "default"])
                subprocess.run([execute_path, "--command", "finish"])

async def main():
    parser = argparse.ArgumentParser(description="Monitor key events for i3 window cycling.")
    parser.add_argument("--execute", default=os.path.join(os.path.dirname(__file__), "i3-window-cycler.py"),
                        help="Path to the i3-window-cycler.py script (default: ./i3-window-cycler.py)")
    parser.add_argument("--keycode", type=int, default=56,
                        help="Keycode to monitor, for example 56 for Left Alt Key, or 125 for Left WIN key (default: 56)")
    parser.add_argument("--print-all-keys", action="store_true",
                        help="Print all key events (default: False)")
    args = parser.parse_args()

    task = asyncio.create_task(monitor_key_events(args.execute, args.keycode, args.print_all_keys))
    await task

if __name__ == "__main__":
    asyncio.run(main())