# i3 Window Cycler

## Features

The **i3 Window Cycler** is a tool designed for the [i3 window manager](https://i3wm.org/), providing a more intuitive way to switch between windows based on their recent usage. It maintains a Most Recently Used (MRU) list of windows and allows users to cycle through them, similar to the Alt+Tab functionality found in other desktop environments.

Key features include:

- **MRU Window Switching**: Cycle through windows based on the order of recent focus.
- **Forward and Backward Cycling**: Navigate through the window list in both directions.
- **Cycling Cancellation**: Cancel the cycling operation to return to the initially focused window.
- **Automatic List Management**: The MRU list updates automatically when windows are opened, closed, or focused.
- **Daemon Mode**: Runs as a background process to listen for cycling commands.

## Installation & Configuration

### Prerequisites

- **Python 3**: Ensure you have Python 3 installed on your system.
- **i3ipc**: Install the `i3ipc` Python library by running:
  ```
  pip install i3ipc
  ```
- **evdev**: Install the `evdev` library for keyboard event monitoring:
  ```
  pip install evdev
  ```
- **i3 Window Manager**: This tool is designed to work with the i3 window manager.

### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/i3-window-cycler.git
   ```
2. **Make Scripts Executable**:
   ```bash
   cd i3-window-cycler
   chmod +x i3-window-cycler.py
   chmod +x i3-grab-key.py
   ```

### Configuration

1. **Start the Daemon**:

   Add the following line to your i3 config file (usually located at `~/.config/i3/config`) to start the window cycler daemon when i3 starts:

   ```
   exec --no-startup-id /path/to/i3-window-cycler.py --daemon
   ```

2. **Set Up Key Monitoring**:

   The `i3-grab-key.py` script monitors key events to detect when a modifier key (like Alt) is released, allowing the cycler to finish cycling. It requires root privileges or appropriate permissions to read input devices.

   Run the script with sudo or configure udev rules to allow your user to read input devices without root.

   Add the following line to your i3 config:

   ```
   exec --no-startup-id sudo /path/to/i3-grab-key.py --keycode 56
   ```

   Replace `56` with the keycode of your modifier key if different (e.g., `56` for Left Alt, `125` for Left Super/Windows key).

3. **Keybindings for Window Cycling**:

   Add the following keybindings to your i3 config to initiate window cycling:

   First, clone the repository and set the correct permissions:
   ```bash
   cd ~/.config/i3
   git clone https://github.com/yourusername/i3-window-cycler.git
   cd i3-window-cycler
   chmod +x i3-window-cycler.py i3-grab-key.py
   ```

   Then, add the following to your i3 config:

   ```
   set $alt Mod1 # More intuitive alias for alt key

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
       # Cancel cycling with Escape, Backup when something went wrong
       bindsym Escape exec --no-startup-id ~/.config/i3/i3-window-cycler/i3-window-cycler.py --command cancel; mode "default"

       # Finish cycling when Alt is released
       # It seems this isn't currently supported by i3, that's why we're using the i3-grab-key.py script.
       #bindsym --release $alt exec --no-startup-id ~/.config/i3/i3-window-cycler/i3-window-cycler.py --command finish; mode "default"
   }
   ```

   Feel free to experiment with different keybinding setups, including advanced keyboard navigation techniques. Since the cycler picks up the latest focused window when you release the Alt key, you can tailor the keybindings to suit your workflow and preferences.

4. **Ensure Proper Permissions**:

   If you prefer not to run `i3-grab-key.py` with sudo, you can set up udev rules to grant your user access to input devices.

   Create a file at `/etc/udev/rules.d/99-input.rules` with the following content:

   ```
   KERNEL=="event*", SUBSYSTEM=="input", TAG+="uaccess", TAG+="udev-acl", OWNER="yourusername"
   ```

   Replace `yourusername` with your actual username.

   Then, reload udev rules:

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
