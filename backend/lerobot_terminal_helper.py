"""
LeRobot Terminal Helper
=======================
This script helps interact with a LeRobot process running in a separate terminal.

Usage:
------
1. Start LeRobot in another terminal (with lerobot venv activated):
   python -m lerobot.record --robot.type=so101_follower --robot.port=COM24 ...

2. This helper can:
   - Send Enter key to the LeRobot terminal (using pyautogui)
   - Monitor the lerobot_command.txt file for new targets
   - Automatically press Enter when a new target is set

Requirements:
- pyautogui (pip install pyautogui)
- LeRobot running in a visible terminal window

For Windows, you may need to have the LeRobot terminal window focused
when sending Enter keys.
"""

import time
import os
import sys

# Try to import pyautogui for keyboard simulation
try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False
    print("[WARN] pyautogui not installed. Install with: pip install pyautogui")
    print("[WARN] Enter key automation will not work without pyautogui.")


# Command file location (written by lerobot_bridge.py)
COMMAND_FILE = os.path.join(os.path.dirname(__file__), "lerobot_command.txt")


def send_enter_to_terminal():
    """Send Enter key to the currently focused window."""
    if not HAS_PYAUTOGUI:
        print("[ERROR] pyautogui not available. Cannot send Enter key.")
        return False
    
    try:
        pyautogui.press('enter')
        print("[OK] Enter key sent to focused window")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send Enter: {e}")
        return False


def read_command_file():
    """Read the current target from the command file."""
    if not os.path.exists(COMMAND_FILE):
        return None, None
    
    try:
        with open(COMMAND_FILE, 'r') as f:
            lines = f.readlines()
        
        target = None
        timestamp = None
        
        for line in lines:
            line = line.strip()
            if line.startswith("TARGET="):
                target = line.split("=", 1)[1]
            elif line.startswith("TIMESTAMP="):
                timestamp = float(line.split("=", 1)[1])
        
        return target, timestamp
    except Exception as e:
        print(f"[ERROR] Failed to read command file: {e}")
        return None, None


def monitor_and_send_enter(poll_interval: float = 0.5):
    """
    Monitor the command file and send Enter when a new target is detected.
    
    This is useful for automating the Enter key press when the Scrapple
    backend sets a new target after voice validation.
    
    Parameters
    ----------
    poll_interval : float
        How often to check for new targets (seconds)
    """
    print("=" * 60)
    print("  LeRobot Terminal Helper - Monitor Mode")
    print("=" * 60)
    print(f"  Monitoring: {COMMAND_FILE}")
    print(f"  Poll interval: {poll_interval}s")
    print()
    print("  IMPORTANT: Make sure the LeRobot terminal is focused")
    print("  when you want Enter to be sent!")
    print()
    print("  Press Ctrl+C to stop.")
    print("-" * 60)
    
    last_timestamp = None
    
    try:
        while True:
            target, timestamp = read_command_file()
            
            if timestamp and timestamp != last_timestamp:
                print(f"\n[NEW TARGET] {target} (timestamp: {timestamp})")
                print("[INFO] Waiting 1 second, then sending Enter...")
                print("[INFO] Focus the LeRobot terminal window NOW!")
                time.sleep(1.0)
                
                if send_enter_to_terminal():
                    print(f"[OK] Enter sent for target: {target}")
                else:
                    print(f"[FAIL] Could not send Enter for target: {target}")
                
                last_timestamp = timestamp
            
            time.sleep(poll_interval)
            
    except KeyboardInterrupt:
        print("\n[INFO] Monitor stopped by user.")


def print_lerobot_command():
    """Print the full LeRobot command for copy-paste convenience."""
    from config import Config
    
    robot_type = getattr(Config, 'LEROBOT_ROBOT_TYPE', 'so101_follower')
    robot_port = getattr(Config, 'LEROBOT_ROBOT_PORT', 'COM24')
    robot_id = getattr(Config, 'LEROBOT_ROBOT_ID', 'my_awesome_follower_arm')
    cameras_config = getattr(
        Config, 
        'LEROBOT_CAMERAS_CONFIG',
        '{ handeye: {type: opencv, index_or_path: 3, width: 640, height: 480, fps: 0}, '
        'front: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}'
    )
    repo_id = getattr(Config, 'LEROBOT_REPO_ID', 'jakkii/eval_scrapple')
    episode_time_s = getattr(Config, 'LEROBOT_EPISODE_TIME_S', 3600)
    default_task = getattr(Config, 'LEROBOT_DEFAULT_TASK', 'Grab the Nut')
    policy_path = getattr(Config, 'LEROBOT_POLICY_PATH', 'outputs/train/scrapple_model_4')
    
    cmd = (
        f'python -m lerobot.record '
        f'--robot.type={robot_type} '
        f'--robot.port={robot_port} '
        f'--robot.id={robot_id} '
        f'--robot.cameras="{cameras_config}" '
        f'--display_data=true '
        f'--dataset.repo_id={repo_id} '
        f'--dataset.episode_time_s={episode_time_s} '
        f'--dataset.single_task="{default_task}" '
        f'--policy.path={policy_path}'
    )
    
    print("=" * 60)
    print("  LeRobot Recording Command")
    print("=" * 60)
    print()
    print("Copy and paste this command into your LeRobot venv terminal:")
    print()
    print(cmd)
    print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "monitor":
            monitor_and_send_enter()
        elif sys.argv[1] == "enter":
            send_enter_to_terminal()
        elif sys.argv[1] == "command":
            print_lerobot_command()
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Usage: python lerobot_terminal_helper.py [monitor|enter|command]")
    else:
        print("LeRobot Terminal Helper")
        print("=======================")
        print()
        print("Commands:")
        print("  python lerobot_terminal_helper.py command  - Print LeRobot command to copy")
        print("  python lerobot_terminal_helper.py monitor  - Monitor for targets and send Enter")
        print("  python lerobot_terminal_helper.py enter    - Send Enter key once")
        print()
        print_lerobot_command()
