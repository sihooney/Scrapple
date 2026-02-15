"""
LeRobot integration bridge.
After a valid voice decision, the backend calls run_lerobot_commands(target).

This module handles communication with the LeRobot process running in a separate terminal.
It can:
1. Send Enter key presses to confirm actions in the LeRobot terminal
2. Execute LeRobot commands via subprocess
3. Communicate with LeRobot via a named pipe/socket for more complex interactions

The LeRobot process should be started in a separate terminal with:
    python -m lerobot.record --robot.type=so101_follower --robot.port=COM24 ...
"""

from __future__ import annotations

import os
import subprocess
import threading
import time
from typing import Optional, Callable
from config import Config

# Global state for LeRobot process management
_lerobot_process: Optional[subprocess.Popen] = None
_lerobot_lock = threading.Lock()
_lerobot_callbacks: list[Callable[[str], None]] = []


class LeRobotBridge:
    """
    Bridge for communicating with LeRobot running in a separate terminal/process.
    
    Supports multiple interaction modes:
    1. External Terminal Mode: LeRobot runs in a separate terminal, bridge sends commands via stdin
    2. Subprocess Mode: Bridge spawns and manages LeRobot process directly
    3. File-based Mode: Uses a command file for communication (fallback)
    """
    
    def __init__(self) -> None:
        self._process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._command_file = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "lerobot_command.txt"
        )
        self._last_target: Optional[str] = None
        self._callbacks: list[Callable[[str, str], None]] = []
    
    def start_recording_session(
        self,
        task_description: str = "Grab the Nut",
        episode_time_s: int = 3600,
        repo_id: str = "jakkii/eval_scrapple",
        policy_path: str = "outputs/train/scrapple_model_4",
    ) -> bool:
        """
        Start a new LeRobot recording session.
        
        This will launch the lerobot.record command with the configured parameters.
        The process runs in the background and waits for Enter key presses to
        start/stop recording episodes.
        
        Parameters
        ----------
        task_description : str
            The task description for the recording session
        episode_time_s : int
            Maximum episode time in seconds
        repo_id : str
            HuggingFace dataset repository ID
        policy_path : str
            Path to the trained policy model
            
        Returns
        -------
        bool
            True if session started successfully, False otherwise
        """
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                print("[LEROBOT] Recording session already running")
                return True
            
            cmd = self._build_command(
                task_description=task_description,
                episode_time_s=episode_time_s,
                repo_id=repo_id,
                policy_path=policy_path,
            )
            
            print(f"\n[LEROBOT] Starting recording session...")
            print(f"[LEROBOT] Command: {' '.join(cmd)}")
            
            try:
                # Start LeRobot process with stdin pipe for sending Enter keys
                self._process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,  # Line buffered
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
                )
                
                # Start a thread to read and log output
                threading.Thread(
                    target=self._read_output,
                    daemon=True,
                ).start()
                
                print(f"[LEROBOT] Session started (PID: {self._process.pid})")
                return True
                
            except Exception as e:
                print(f"[LEROBOT] Failed to start session: {e}")
                return False
    
    def _build_command(
        self,
        task_description: str,
        episode_time_s: int,
        repo_id: str,
        policy_path: str,
    ) -> list[str]:
        """Build the lerobot.record command with all parameters."""
        # Use config values
        robot_type = getattr(Config, 'LEROBOT_ROBOT_TYPE', 'so101_follower')
        robot_port = getattr(Config, 'LEROBOT_ROBOT_PORT', 'COM24')
        robot_id = getattr(Config, 'LEROBOT_ROBOT_ID', 'my_awesome_follower_arm')
        
        # Camera configuration
        cameras_config = getattr(
            Config, 
            'LEROBOT_CAMERAS_CONFIG',
            '{ handeye: {type: opencv, index_or_path: 3, width: 640, height: 480, fps: 0}, '
            'front: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}'
        )
        
        cmd = [
            "python", "-m", "lerobot.record",
            f"--robot.type={robot_type}",
            f"--robot.port={robot_port}",
            f"--robot.id={robot_id}",
            f"--robot.cameras={cameras_config}",
            "--display_data=true",
            f"--dataset.repo_id={repo_id}",
            f"--dataset.episode_time_s={episode_time_s}",
            f"--dataset.single_task={task_description}",
            f"--policy.path={policy_path}",
        ]
        
        return cmd
    
    def _read_output(self) -> None:
        """Read and log output from the LeRobot process."""
        if self._process is None or self._process.stdout is None:
            return
            
        try:
            for line in iter(self._process.stdout.readline, ''):
                if not line:
                    break
                line = line.rstrip()
                print(f"[LEROBOT OUTPUT] {line}")
                
                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        callback("output", line)
                    except Exception:
                        pass
        except Exception as e:
            print(f"[LEROBOT] Output reader error: {e}")
    
    def send_enter(self) -> bool:
        """
        Send Enter key to the LeRobot process to start/confirm an episode.
        
        This is used to:
        1. Start recording a new episode
        2. Confirm target selection
        3. Progress through prompts
        
        Returns
        -------
        bool
            True if Enter was sent successfully, False otherwise
        """
        with self._lock:
            if self._process is None or self._process.poll() is not None:
                print("[LEROBOT] No active session - Enter key not sent")
                return False
            
            try:
                if self._process.stdin:
                    self._process.stdin.write("\n")
                    self._process.stdin.flush()
                    print("[LEROBOT] Enter key sent to process")
                    return True
            except Exception as e:
                print(f"[LEROBOT] Failed to send Enter: {e}")
                return False
        
        return False
    
    def send_command(self, command: str) -> bool:
        """
        Send a text command to the LeRobot process stdin.
        
        Parameters
        ----------
        command : str
            The command/text to send (newline will be appended)
            
        Returns
        -------
        bool
            True if command was sent successfully
        """
        with self._lock:
            if self._process is None or self._process.poll() is not None:
                print(f"[LEROBOT] No active session - command not sent: {command}")
                return False
            
            try:
                if self._process.stdin:
                    self._process.stdin.write(command + "\n")
                    self._process.stdin.flush()
                    print(f"[LEROBOT] Command sent: {command}")
                    return True
            except Exception as e:
                print(f"[LEROBOT] Failed to send command: {e}")
                return False
        
        return False
    
    def set_target(self, target: str) -> None:
        """
        Set the current pick target for the robot arm.
        
        This updates the internal state and optionally writes to a command file
        that external processes can monitor.
        
        Parameters
        ----------
        target : str
            The object name to pick (e.g., "skull", "gear", "nut")
        """
        self._last_target = target
        
        # Write to command file for external monitoring
        try:
            os.makedirs(os.path.dirname(self._command_file), exist_ok=True)
            with open(self._command_file, 'w') as f:
                f.write(f"TARGET={target}\n")
                f.write(f"TIMESTAMP={time.time()}\n")
            print(f"[LEROBOT] Target set: {target}")
        except Exception as e:
            print(f"[LEROBOT] Failed to write command file: {e}")
        
        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback("target", target)
            except Exception:
                pass
    
    def get_last_target(self) -> Optional[str]:
        """Get the last set target."""
        return self._last_target
    
    def is_running(self) -> bool:
        """Check if a LeRobot session is currently running."""
        with self._lock:
            return self._process is not None and self._process.poll() is None
    
    def stop_session(self) -> bool:
        """
        Stop the current LeRobot recording session.
        
        Returns
        -------
        bool
            True if session was stopped, False if no session was running
        """
        with self._lock:
            if self._process is None:
                return False
            
            if self._process.poll() is None:
                try:
                    # Try graceful shutdown first
                    if self._process.stdin:
                        self._process.stdin.close()
                    self._process.terminate()
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                except Exception as e:
                    print(f"[LEROBOT] Error stopping session: {e}")
            
            self._process = None
            print("[LEROBOT] Session stopped")
            return True
    
    def add_callback(self, callback: Callable[[str, str], None]) -> None:
        """
        Add a callback for LeRobot events.
        
        The callback receives (event_type, data) where:
        - event_type: "target", "output", "status"
        - data: relevant string data for the event
        """
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[str, str], None]) -> None:
        """Remove a previously added callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)


# Singleton instance
lerobot_bridge = LeRobotBridge()


def run_lerobot_commands(target: str) -> None:
    """
    Execute command to drive LeRobot for the given target.
    
    This is the main entry point called by voice.py after a valid decision.
    It:
    1. Sets the target for the arm to pick
    2. Sends Enter to confirm/start the pick action if a session is running
    3. Logs the action
    
    Parameters
    ----------
    target : str
        The object name to pick (must be in visible_objects list)
    """
    if not target:
        return
    
    msg = f"LeRobot: pick target = {target!r}"
    print(f"\n[LEROBOT] {msg}")
    
    # Set the target in the bridge
    lerobot_bridge.set_target(target)
    
    # If a recording session is running, send Enter to start the episode
    if lerobot_bridge.is_running():
        print("[LEROBOT] Session active - sending Enter to start episode...")
        time.sleep(0.5)  # Brief delay to ensure target is registered
        lerobot_bridge.send_enter()
    else:
        print("[LEROBOT] No active session. Target saved for manual operation.")
        print("[LEROBOT] Start a session with: POST /api/lerobot/start")


def start_lerobot_session(
    task_description: str = "Grab the Nut",
    episode_time_s: int = 3600,
    repo_id: str = "jakkii/eval_scrapple",
    policy_path: str = "outputs/train/scrapple_model_4",
) -> bool:
    """
    Start a LeRobot recording session.
    
    Convenience function wrapping lerobot_bridge.start_recording_session().
    """
    return lerobot_bridge.start_recording_session(
        task_description=task_description,
        episode_time_s=episode_time_s,
        repo_id=repo_id,
        policy_path=policy_path,
    )


def stop_lerobot_session() -> bool:
    """Stop the current LeRobot session."""
    return lerobot_bridge.stop_session()


def send_enter_to_lerobot() -> bool:
    """Send Enter key to LeRobot process."""
    return lerobot_bridge.send_enter()


def is_lerobot_running() -> bool:
    """Check if LeRobot is running."""
    return lerobot_bridge.is_running()
