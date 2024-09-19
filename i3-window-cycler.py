#!/usr/bin/env python3

# inspired by i3-cycle-focus.py

import asyncio
import os
import sys
import argparse
import logging
from i3ipc.aio import Connection

SOCKET_FILE = '/tmp/.i3-window-cycler.sock'
MAX_WIN_HISTORY = 16

# Set logging level to DEBUG for more detailed output
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

class FocusCycler:
    def __init__(self):
        self.i3 = None
        self.window_list = []  # Store dicts with 'id' and 'title'
        self.current_focused_window = None  # New attribute to store the focused window
        self.initial_window = None
        self.current_index = -1
        self.is_cycling = False
        self.ignore_focus_events = False

    async def connect(self):
        self.i3 = await Connection(auto_reconnect=True).connect()
        self.i3.on('window::focus', self.on_window_focus)
        self.i3.on('window::close', self.on_window_close)
        self.i3.on('window::new', self.on_window_new)
        self.i3.on('shutdown', self.on_shutdown)
        await self.initialize_window_list()

    async def initialize_window_list(self):
        # Initialize window list with only the currently focused window
        tree = await self.i3.get_tree()
        focused = tree.find_focused()
        if focused and focused.type == 'con':
            self.current_focused_window = {'id': focused.id, 'title': focused.name or 'No Title'}
            self.window_list = [self.current_focused_window]
        else:
            self.current_focused_window = None
            self.window_list = []
        logging.debug('Initialized window_list:\n' + await self.get_window_list_info())

    async def on_window_focus(self, i3conn, event):
        window_id = event.container.id
        window_title = event.container.name or 'No Title'
        floating = event.container.floating
        window_marks = event.container.marks  # List of window marks/tags
        logging.debug(f'Window focused: {window_id}')

        # Always update the current focused window with additional properties
        self.current_focused_window = {
            'id': window_id,
            'title': window_title,
            'floating': floating,
            'marks': window_marks,
        }

        if self.ignore_focus_events:
            logging.debug('Ignoring focus event for window list update')
            return

        # Remove window from list if it exists
        self.window_list = [w for w in self.window_list if w['id'] != window_id]
        # Insert at the front
        self.window_list.insert(0, self.current_focused_window)
        if len(self.window_list) > MAX_WIN_HISTORY:
            self.window_list = self.window_list[:MAX_WIN_HISTORY]
        logging.debug('Updated window_list:\n' + await self.get_window_list_info())

    async def on_window_close(self, i3conn, event):
        window_id = event.container.id
        logging.debug(f'Window closed: {window_id}')
        # Remove window from list
        self.window_list = [w for w in self.window_list if w['id'] != window_id]
        logging.debug('Updated window_list:\n' + await self.get_window_list_info())

    async def on_window_new(self, i3conn, event):
        window_id = event.container.id
        window_title = event.container.name or 'No Title'
        floating = event.container.floating
        window_marks = event.container.marks
        logging.debug(f'New window opened: {window_id}')
        # Insert new window at the front
        new_window = {
            'id': window_id,
            'title': window_title,
            'floating': floating,
            'marks': window_marks,
        }
        self.window_list.insert(0, new_window)
        if len(self.window_list) > MAX_WIN_HISTORY:
            self.window_list = self.window_list[:MAX_WIN_HISTORY]
        logging.debug('Updated window_list:\n' + await self.get_window_list_info())

    def on_shutdown(self, i3conn, event):
        logging.debug('Shutting down')
        if os.path.exists(SOCKET_FILE):
            os.unlink(SOCKET_FILE)
        os._exit(0)

    async def start_cycling(self):
        if self.is_cycling:
            logging.debug('Already cycling')
            return
        focused_window = self.window_list[0] if self.window_list else None
        if focused_window:
            self.initial_window = focused_window['id']
        self.current_index = 0  # Start from the current window
        self.is_cycling = True
        self.ignore_focus_events = True
        logging.debug('Cycling started')
        logging.debug(f'Initial window: {self.initial_window}')
        logging.debug('Window list at start:\n' + await self.get_window_list_info())

    # Add a new method to check and handle the current window
    async def check_and_handle_current_window(self):
        window = self.current_focused_window
        if window:
            is_floating = window.get('floating') in ('user_on', 'on', 'auto_on')
            has_scratchpad_mark = 'scratchpad' in window.get('marks', [])
            if is_floating and has_scratchpad_mark:
                window_id = window['id']
                # Send the window to scratchpad
                await self.i3.command(f'[con_id={window_id}] move to scratchpad')
                logging.debug(f'Window {window_id} sent to scratchpad')

    async def cycle_next(self):
        if not self.is_cycling:
            logging.debug('Cycling not started, starting now')
            await self.start_cycling()

        # Before moving to the next window, check and handle the current window
        await self.check_and_handle_current_window()

        self.current_index += 1
        if self.current_index >= len(self.window_list):
            logging.debug('Reached end of window_list, wrapping around')
            self.current_index = 0  # Wrap around to the first window

        window = self.window_list[self.current_index]
        window_id = window['id']
        await self.i3.command(f'[con_id={window_id}] focus')
        logging.debug(f'Focused window {window_id}, current_index is now {self.current_index}')

    async def cycle_prev(self):
        if not self.is_cycling:
            logging.debug('Cycling not started, starting now')
            await self.start_cycling()

        # Before moving to the previous window, check and handle the current window
        await self.check_and_handle_current_window()

        self.current_index -= 1
        if self.current_index < 0:
            logging.debug('Reached beginning of window_list, wrapping around')
            self.current_index = len(self.window_list) - 1  # Wrap around to the last window

        window = self.window_list[self.current_index]
        window_id = window['id']
        await self.i3.command(f'[con_id={window_id}] focus')
        logging.debug(f'Focused window {window_id}, current_index is now {self.current_index}')

    async def cancel_cycling(self):
        if self.is_cycling:
            logging.debug('Cycling canceled')
            await self.i3.command(f'[con_id={self.initial_window}] focus')
            self.is_cycling = False
            self.ignore_focus_events = False
            logging.debug('Window list after cancel:\n' + await self.get_window_list_info())

    async def finish_cycling(self):
        if self.is_cycling:
            logging.debug('Cycling finished')
            self.is_cycling = False
            self.ignore_focus_events = False
            # Update MRU list now that cycling is finished
            focused = self.current_focused_window
            if focused:
                window_id = focused['id']
                # Move the focused window to the front
                self.window_list = [w for w in self.window_list if w['id'] != window_id]
                self.window_list.insert(0, focused)
                if len(self.window_list) > MAX_WIN_HISTORY:
                    self.window_list = self.window_list[:MAX_WIN_HISTORY]
            logging.debug('Window list at finish:\n' + await self.get_window_list_info())

    async def get_window_list_info(self):
        """Helper method to get window id and title for window_list."""
        info_list = [f'[{w["id"]}] "{w["title"]}"' for w in self.window_list]
        return '\n'.join(info_list)

    async def handle_command(self, command):
        logging.debug(f'Handling command: {command}')
        if command == 'next':
            await self.cycle_next()
        elif command == 'prev':
            await self.cycle_prev()
        elif command == 'cancel':
            await self.cancel_cycling()
        elif command == 'finish':
            await self.finish_cycling()
        else:
            logging.error(f'Unknown command: {command}')

    async def run_server(self):
        # Remove existing socket file if it exists
        if os.path.exists(SOCKET_FILE):
            os.unlink(SOCKET_FILE)
        server = await asyncio.start_unix_server(self.handle_client, path=SOCKET_FILE)
        logging.info(f'Server started on {SOCKET_FILE}')
        async with server:
            await server.serve_forever()

    async def handle_client(self, reader, writer):
        data = await reader.read(100)
        message = data.decode()
        await self.handle_command(message.strip())
        writer.close()
        await writer.wait_closed()

    async def run(self):
        await self.connect()
        await self.run_server()

async def send_command(command):
    try:
        reader, writer = await asyncio.open_unix_connection(SOCKET_FILE)
        writer.write(command.encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()
    except Exception as e:
        print(f'Failed to send command: {e}')
        if not os.path.exists(SOCKET_FILE):
            print(f"Socket file not found at {SOCKET_FILE}. Is the i3-window-cycler daemon running? Start with i3-window-cycler.py --daemon")
            return
        elif isinstance(e, ConnectionRefusedError):
            print(f"Is the i3-window-cycler daemon running? Start with i3-window-cycler.py --daemon")
            return


async def main():
    parser = argparse.ArgumentParser(description='i3-cycle-focus without saving state to disk.')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--command', help='Send command to daemon: next, prev, cancel, finish')
    args = parser.parse_args()

    if args.daemon:
        focus_cycler = FocusCycler()
        await focus_cycler.run()
    elif args.command:
        await send_command(args.command)
    else:
        print_documentation()

def print_documentation():
    doc = """
i3-window-cycler: A window focus cycling tool for i3 window manager

Usage:
  python3 i3-window-cycler.py [--daemon | --command <command>]

Options:
  --daemon    Run the script as a daemon process
  --command   Send a command to the running daemon

Commands:
  next        Focus the next window in the cycle
  prev        Focus the previous window in the cycle
  cancel      Cancel cycling and return to the initial window
  finish      Finish cycling and update the Most Recently Used (MRU) list

Description:
  This script provides a window cycling functionality for the i3 window manager.
  It maintains a list of recently focused windows and allows cycling through them
  without saving state to disk.

  The script should be run in two modes:
  1. Daemon mode: Starts the background process that listens for commands
  2. Command mode: Sends commands to the running daemon

How to use:
  1. Start the daemon:
     python3 i3-window-cycler.py --daemon

  2. Bind keys in your i3 config to send commands:
     bindsym $mod+Tab exec python3 /path/to/i3-window-cycler.py --command next
     bindsym $mod+Shift+Tab exec python3 /path/to/i3-window-cycler.py --command prev
     bindsym $mod+Escape exec python3 /path/to/i3-window-cycler.py --command cancel
     bindsym $mod+Return exec python3 /path/to/i3-window-cycler.py --command finish

Features:
  - Maintains a Most Recently Used (MRU) list of windows
  - Cycles through windows based on focus history
  - Supports forward and backward cycling
  - Allows canceling the cycle to return to the initial window
  - Updates the MRU list when finishing a cycle
  - Handles new windows, closed windows, and i3 shutdown events

Note:
  This script requires the i3ipc Python library. Install it using:
  pip install i3ipc

For more information, visit: https://github.com/arakis/i3-window-cycler
    """
    print(doc)

if __name__ == '__main__':
    asyncio.run(main())