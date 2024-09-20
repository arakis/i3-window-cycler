# i3 Window Cycler

A lightweight window cycling utility for the [i3 window manager](https://i3wm.org/), enabling you to switch between windows based on their recent usage without a visual popup. It mimics the Alt+Tab functionality found in other desktop environments by cycling window focus in a most-recently-used (MRU) order.

## Features

- **MRU Window Switching**: Cycle through windows based on the order of recent focus.
- **Forward and Backward Navigation**: Move through the window list in both directions.
- **Seamless Cycling**: Provides visual feedback by focusing windows as you cycle, without a popup window.
- **Cycling Cancellation**: Cancel the cycling operation to return to the initially focused window.
- **Automatic List Management**: The MRU list updates automatically when windows are opened, closed, or focused.
- **Daemon Mode**: Runs as a background process to listen for cycling commands.

## Installation & Configuration

### Prerequisites

- **Python 3**: Ensure you have Python 3 installed on your system.
- **i3ipc**: Install the `i3ipc` Python library by running:
  ```bash
  pip install i3ipc
  ```
- **evdev**: Install the `evdev` library for keyboard event monitoring:
  ```bash
  pip install evdev
  ```
### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/arakis/i3-window-cycler.git ~/.config/i3/i3-window-cycler
   ```
2. **Make Scripts Executable**:
   ```bash
   chmod +x ~/.config/i3/i3-window-cycler/i3-window-cycler.py ~/.config/i3/i3-window-cycler/i3-key-listener.py
   ```

### Configuration

1. **Start the Daemon**:

   Add the following line to your i3 configuration file (usually located at `~/.config/i3/config`) to start the window cycler daemon when i3 starts:

   ```
   exec --no-startup-id ~/.config/i3/i3-window-cycler/i3-window-cycler.py --daemon
   ```

2. **Set Up Key Monitoring**:

   The [`i3-key-listener.py`](i3-key-listener.py) script monitors key events to detect when a modifier key (like Alt) is released, allowing the cycler to finish cycling. It requires root privileges or appropriate permissions to read input devices.

   **Option 1: Run with sudo**

   Add the following line to your i3 config:

   ```
   exec --no-startup-id sudo ~/.config/i3/i3-window-cycler/i3-key-listener.py --keycode 56
   ```

   **Option 2: Configure udev Rules**

   If you prefer not to run `i3-key-listener.py` with sudo, set up udev rules to grant your user access to input devices. See the `4. Ensure Proper Permissions` section below.

   Replace `56` with the keycode of your modifier key if different (e.g., `56` for Left Alt, `125` for Left Super/Windows key).

3. **Keybindings for Window Cycling**:

   Add the following keybindings to your i3 configuration to initiate window cycling:

   ```bash
   # ~/.config/i3/config

   # More intuitive alias for Alt key
   set $alt Mod1

   # Enter window switching mode with Alt+Tab
   bindsym $alt+Tab exec --no-startup-id ~/.config/i3/i3-window-cycler/i3-window-cycler.py --command next; mode "window-cycler"
   bindsym $alt+Shift+Tab exec --no-startup-id ~/.config/i3/i3-window-cycler/i3-window-cycler.py --command prev; mode "window-cycler"

   mode "window-cycler" {
       # Cycle forward with Alt+Tab
       bindsym $alt+Tab exec --no-startup-id ~/.config/i3/i3-window-cycler/i3-window-cycler.py --command next

       # Cycle backward with Alt+Shift+Tab
       bindsym $alt+Shift+Tab exec --no-startup-id ~/.config/i3/i3-window-cycler/i3-window-cycler.py --command prev

       # Cancel cycling with Alt+Escape
       bindsym $alt+Escape exec --no-startup-id ~/.config/i3/i3-window-cycler/i3-window-cycler.py --command cancel; mode "default"
       # Backup cancel with Escape key
       bindsym Escape exec --no-startup-id ~/.config/i3/i3-window-cycler/i3-window-cycler.py --command cancel; mode "default"

       # Finish cycling when Alt is released (not supported by i3)
       # Using the i3-key-listener.py script instead
       # bindsym --release $alt exec --no-startup-id ~/.config/i3/i3-window-cycler/i3-window-cycler.py --command finish; mode "default"
   }
   ```

   Feel free to customize the keybindings to suit your workflow. Since the cycler picks up the latest focused window when you release the Alt key, you can tailor the keybindings to your preferences, for example changing focus via arrow keys. So you could combine alt-tab with classic window focus navigation.

4. **Ensure Proper Permissions**:

   To run `i3-key-listener.py` without `sudo`, you can set up udev rules to grant your user access to input devices.

   **Create udev Rule**:

   Create a file at `/etc/udev/rules.d/99-input.rules` with the following content:

   ```
   KERNEL=="event*", SUBSYSTEM=="input", TAG+="uaccess", TAG+="udev-acl", OWNER="<your-username>"
   ```

   Replace `<your-username>` with your actual username.

   Ensure the following line to your i3 config:

   ```
   exec --no-startup-id ~/.config/i3/i3-window-cycler/i3-key-listener.py --keycode 56
   ```

   **Reload udev Rules**:

   ```bash
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```

5. **Restart i3**:

   After making changes to the i3 configuration, restart i3 to apply them. You can typically do this with `$mod+Shift+r`.

## Usage

- Press `$alt+Tab` to start cycling through windows in the order of most recent focus.
- Continue pressing `Tab` while holding `$alt` to cycle forward.
- Press `Shift+Tab` while holding `$alt` to cycle backward.
- Release the `$alt` key to select the currently focused window.
- Press `Escape` to cancel cycling and return to the original window.

